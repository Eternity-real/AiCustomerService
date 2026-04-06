import os
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from langchain_community.document_loaders import TextLoader
from app.core.config import settings


def init_chroma_vectorstore() -> Chroma:
    source_path = settings.RAG_SOURCE_TXT
    persist_dir = settings.RAG_VECTORSTORE_DIR

    if not os.path.exists(source_path):
        raise FileNotFoundError(f"RAG_SOURCE_TXT 不存在：{source_path}")

    loader = TextLoader(source_path, encoding="utf-8")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(settings.RAG_CHUNK_SIZE),
        chunk_overlap=int(settings.RAG_CHUNK_OVERLAP),
    )
    splits = loader.load_and_split(splitter)

    embeddings = DashScopeEmbeddings(
        model=settings.RAG_EMBEDDING_MODEL,
        dashscope_api_key=settings.QIANWEN_APIKEY,
    )

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=persist_dir,
    )
    return vectorstore


def load_existing_vectorstore() -> Chroma:
    persist_dir = settings.RAG_VECTORSTORE_DIR
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(f"向量库目录不存在：{persist_dir}，请先初始化。")

    embeddings = DashScopeEmbeddings(
        model=settings.RAG_EMBEDDING_MODEL,
        dashscope_api_key=settings.QIANWEN_APIKEY,
    )
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
    )


if __name__ == "__main__":
    init_chroma_vectorstore()
    print(f"向量库已初始化：{settings.RAG_VECTORSTORE_DIR}")