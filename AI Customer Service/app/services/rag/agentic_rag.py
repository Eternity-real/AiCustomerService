import os
from typing import Annotated, TypedDict, List, Optional, Dict, Any, Literal
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.errors import GraphRecursionError
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from langchain_community.utilities import SerpAPIWrapper
from app.core.config import settings


class AgenticRAG:
    def __init__(self):
        self.enable_search_tool = settings.RAG_ENABLE_SEARCH_TOOL
        self.max_recursion_limit = settings.RAG_MAX_RECURSION_LIMIT
        self.llm = self._init_llm()
        self.embeddings = self._init_embeddings()
        self.vectorstore = self._init_vectorstore()
        self.search_tool = self._init_search_tool()

        self.graph = self._build_workflow()

    def _init_llm(self) -> ChatOpenAI:
        model_name = settings.RAG_LLM_MODEL_NAME or settings.MODEL_NAME
        return ChatOpenAI(
            model=model_name,
            base_url=settings.BASE_URL,
            api_key=settings.QIANWEN_APIKEY,
            streaming=False,
        )

    def _init_embeddings(self) -> DashScopeEmbeddings:
        return DashScopeEmbeddings(
            model=settings.RAG_EMBEDDING_MODEL,
            dashscope_api_key=settings.QIANWEN_APIKEY,
        )

    def _init_vectorstore(self) -> Chroma:
        persist_dir = settings.RAG_VECTORSTORE_DIR
        if not os.path.exists(persist_dir):
            raise FileNotFoundError(
                f"向量库目录不存在：{persist_dir}。请先运行 init_vectorstore.py 初始化。"
            )
        return Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings,
        )

    def _init_search_tool(self) -> Optional[SerpAPIWrapper]:
        if not self.enable_search_tool:
            return None
        api_key = settings.SERPAPI_API_KEY
        if not api_key:
            return None
        os.environ["SERPAPI_API_KEY"] = api_key
        return SerpAPIWrapper()

    # ---------------------- 状态定义 ----------------------
    class State(TypedDict):
        question: str
        messages: Annotated[list, add_messages]
        retrieved_docs: List[Document]
        retrieval_scores: List[float]
        final_context: str
        query_variants: List[str]
        retrieval_attempts: int
        search_attempts: int
        need_rag: Optional[bool]
        is_sufficient: Optional[bool]
        answer: Optional[str]
        reflection_score: Optional[float]
        reflection_passed: Optional[bool]

    # ---------------------- 节点函数 ----------------------
    async def _understand_node(self, state: "AgenticRAG.State") -> dict:
        question = state["question"]
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "你是一个智能客服问答助手。请判断用户问题是否需要外部知识检索（RAG）。"
             "如果问题涉及事实性知识、专业说明、规则条款、产品/售后政策等，通常需要检索。"
             "仅输出 '需要' 或 '不需要'。"),
            ("user", question),
        ])
        chain = prompt | self.llm | StrOutputParser()
        decision = (await chain.ainvoke({})).strip()
        need_rag = (decision == "需要")
        return {
            "need_rag": need_rag,
            "query_variants": [question],
            "messages": [{"role": "user", "content": question}],
        }

    async def _direct_answer_node(self, state: "AgenticRAG.State") -> dict:
        question = state["question"]
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个有用的电商客服助手。"),
            ("user", question),
        ])
        chain = prompt | self.llm | StrOutputParser()
        answer = await chain.ainvoke({})
        return {
            "answer": answer,
            "messages": [{"role": "assistant", "content": answer}],
        }

    async def _generate_query_node(self, state: "AgenticRAG.State") -> dict:
        question = state["question"]
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是检索专家。请将用户问题改写成1-3个不同角度/表述的检索查询，每行一个，不要序号。"),
            ("user", question),
        ])
        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({})
        queries = [q.strip() for q in result.split("\n") if q.strip()]
        if not queries:
            queries = [question]
        return {"query_variants": queries}

    def _retrieve_node(self, state: "AgenticRAG.State") -> dict:
        queries = state.get("query_variants", [state["question"]])
        k = int(getattr(settings, "RAG_TOP_K", 5))

        all_docs_scores = []
        for q in queries:
            docs_scores = self.vectorstore.similarity_search_with_relevance_scores(q, k=k)
            all_docs_scores.extend(docs_scores)

        all_docs_scores.sort(key=lambda x: x[1], reverse=True)

        seen = set()
        unique_docs = []
        scores = []
        for doc, score in all_docs_scores:
            if not doc or not doc.page_content:
                continue
            if doc.page_content in seen:
                continue
            seen.add(doc.page_content)
            unique_docs.append(doc)
            scores.append(float(score))

        return {
            "retrieved_docs": unique_docs,
            "retrieval_scores": scores,
            "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
        }

    def _rerank_filter_node(self, state: "AgenticRAG.State") -> dict:
        docs = state.get("retrieved_docs", [])
        if not docs:
            return {"retrieved_docs": [], "final_context": ""}
        top_n = int(getattr(settings, "RAG_RERANK_TOP_N", 3))
        top_docs = docs[:top_n]
        context = "\n".join([doc.page_content for doc in top_docs])
        return {"retrieved_docs": top_docs, "final_context": context}

    def _check_sufficiency_node(self, state: "AgenticRAG.State") -> dict:
        scores = state.get("retrieval_scores", [])
        if not scores:
            return {"is_sufficient": False}
        threshold = float(getattr(settings, "RAG_SIMILARITY_THRESHOLD", 0.2))
        return {"is_sufficient": (max(scores) > threshold)}

    def _search_tool_node(self, state: "AgenticRAG.State") -> dict:
        if not self.enable_search_tool or not self.search_tool:
            return {}
        question = state["question"]
        try:
            search_results = self.search_tool.run(question)
            doc = Document(page_content=search_results, metadata={"source": "serpapi"})
            existing = state.get("retrieved_docs", [])
            all_docs = existing + [doc]
            # 去重
            unique = {d.page_content: d for d in all_docs if d and d.page_content}.values()
            context = "\n".join([d.page_content for d in unique])
            return {
                "retrieved_docs": list(unique),
                "final_context": context,
                "search_attempts": state.get("search_attempts", 0) + 1,
            }
        except Exception:
            return {}

    async def _generate_answer_node(self, state: "AgenticRAG.State") -> dict:
        context = state.get("final_context", "")
        question = state["question"]
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "你是专业的电商客服问答助手。请严格基于上下文回答，不要编造。"
             "如果上下文没有答案，请明确说明并给出建议的下一步。\n上下文：{context}"),
            ("user", "{question}"),
        ])
        chain = prompt | self.llm | StrOutputParser()
        answer = await chain.ainvoke({"context": context, "question": question})
        return {"answer": answer}

    def _reflection_node(self, state: "AgenticRAG.State") -> dict:
        # 这里沿用你原来的简化反思：有 answer 且 context 非空就通过
        answer = state.get("answer", "")
        context = state.get("final_context", "")
        passed = bool(answer) and bool(context.strip())
        return {"reflection_score": 1.0 if passed else 0.0, "reflection_passed": passed}

    def _retry_or_fallback_node(self, state: "AgenticRAG.State") -> dict:
        return {}

    def _output_node(self, state: "AgenticRAG.State") -> dict:
        return {"messages": [{"role": "assistant", "content": state.get("answer", "")}]}

    # ---------------------- 路由函数 ----------------------
    def _route_after_understand(self, state: "AgenticRAG.State") -> Literal["direct_answer", "generate_query"]:
        return "generate_query" if state.get("need_rag", False) else "direct_answer"

    def _route_after_retrieve(self, state: "AgenticRAG.State") -> Literal["rerank", "search"]:
        return "search" if not state.get("retrieved_docs") else "rerank"

    def _route_after_check(self, state: "AgenticRAG.State") -> Literal["generate_answer", "retry_retrieve", "search"]:
        if state.get("is_sufficient", False):
            return "generate_answer"
        if state.get("retrieval_attempts", 0) >= 2 and state.get("search_attempts", 0) == 0:
            return "search"
        return "retry_retrieve"

    def _route_after_reflection(self, state: "AgenticRAG.State") -> Literal["output", "retry_retrieve", "search"]:
        if state.get("reflection_passed", False):
            return "output"
        return "search" if state.get("search_attempts", 0) == 0 else "retry_retrieve"

    # ---------------------- 构建工作流 ----------------------
    def _build_workflow(self):
        workflow = StateGraph(self.State)

        workflow.add_node("understand", self._understand_node)
        workflow.add_node("direct_answer", self._direct_answer_node)
        workflow.add_node("generate_query", self._generate_query_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("search", self._search_tool_node)
        workflow.add_node("rerank", self._rerank_filter_node)
        workflow.add_node("check_sufficiency", self._check_sufficiency_node)
        workflow.add_node("generate_answer", self._generate_answer_node)
        workflow.add_node("reflection", self._reflection_node)
        workflow.add_node("retry_retrieve", self._retry_or_fallback_node)
        workflow.add_node("output", self._output_node)

        workflow.set_entry_point("understand")

        workflow.add_conditional_edges(
            "understand",
            self._route_after_understand,
            {"direct_answer": "direct_answer", "generate_query": "generate_query"},
        )
        workflow.add_edge("direct_answer", END)
        workflow.add_edge("generate_query", "retrieve")

        workflow.add_conditional_edges(
            "retrieve",
            self._route_after_retrieve,
            {"rerank": "rerank", "search": "search"},
        )
        workflow.add_edge("search", "rerank")
        workflow.add_edge("rerank", "check_sufficiency")

        workflow.add_conditional_edges(
            "check_sufficiency",
            self._route_after_check,
            {"generate_answer": "generate_answer", "retry_retrieve": "retry_retrieve", "search": "search"},
        )
        workflow.add_edge("retry_retrieve", "generate_query")
        workflow.add_edge("generate_answer", "reflection")

        workflow.add_conditional_edges(
            "reflection",
            self._route_after_reflection,
            {"output": "output", "retry_retrieve": "retry_retrieve", "search": "search"},
        )
        workflow.add_edge("output", END)

        return workflow.compile()

    async def arun(self, question: str) -> Dict[str, Any]:
        initial_state: AgenticRAG.State = {
            "question": question,
            "messages": [],
            "retrieved_docs": [],
            "retrieval_scores": [],
            "final_context": "",
            "query_variants": [],
            "retrieval_attempts": 0,
            "search_attempts": 0,
            "need_rag": None,
            "is_sufficient": None,
            "answer": None,
            "reflection_score": None,
            "reflection_passed": None,
        }
        try:
            return await self.graph.ainvoke(
                initial_state,
                config={"recursion_limit": self.max_recursion_limit},
            )
        except Exception as e:
            if isinstance(e, GraphRecursionError) or "GraphRecursionError" in str(e):
                return {
                    "question": question,
                    "answer": "没有检索到答案",
                    "messages": [{"role": "assistant", "content": "没有检索到答案"}],
                }
            raise