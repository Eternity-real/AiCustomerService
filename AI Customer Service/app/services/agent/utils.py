from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings
import logging
import asyncio
import json
from typing import Optional, Dict, Any
from pathlib import Path
from app.schemas.order import  OrderCreate, OrderInfoExtract
from datetime import datetime
import random
from app.services.agent.prompts import ORDER_STRUCTURED_EXTRACTION_PROMPT,ORDER_UPDATE_PROMPT
import re

logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# ==================== LLM 客户端配置 ====================
_llm = ChatOpenAI(
    model=settings.MODEL_NAME,
    base_url=settings.BASE_URL,
    api_key=settings.QIANWEN_APIKEY,
    streaming=True,
    timeout=300,
    max_retries=3,
    temperature=0.1,
)


def get_structured_llm(output_schema: type) -> Any:
    """获取结构化输出的 LLM 实例（每次创建新实例，避免 schema 冲突）"""
    structured_llm = ChatOpenAI(
        model=settings.MODEL_NAME,
        base_url=settings.BASE_URL,
        api_key=settings.QIANWEN_APIKEY,
        streaming=False,
        timeout=30,
        max_retries=2,
        temperature=0.0,
    )
    return structured_llm.with_structured_output(output_schema)

# 预编译 Chain 模板
_ChatPromptTemplate = ChatPromptTemplate.from_messages([("user", "{prompt}")])
_chat_chain = _ChatPromptTemplate | _llm | StrOutputParser()

async def call_llm(prompt: str) -> str:
    """调用 LLM，添加异常处理和日志"""
    try:
        # 直接使用预编译的 chain
        return await _chat_chain.ainvoke({"prompt": prompt})
    except Exception as e:
        logger.error(f"LLM 调用失败：{e}", exc_info=True)
        raise

# ==================== RAG 检索 ====================
_rag = None
_rag_lock = asyncio.Lock()


async def retrieve_knowledge(query: str) -> str:
    """检索知识库，添加并发锁保护"""
    global _rag
    async with _rag_lock:
        if _rag is None:
            from app.services.rag.agentic_rag import AgenticRAG
            _rag = AgenticRAG()
    try:
        result = await _rag.arun(query)
        return result.get("final_context", "") or ""
    except Exception as e:
        logger.error(f"RAG 检索失败：{e}", exc_info=True)
        return ""


# ==================== MCP 客户端管理 ====================
async def create_mcp_client(name: str, params: dict):
    """创建 MCP 客户端，添加超时和异常处理"""
    config = {name: {"transport": "stdio", **params}}
    logger.debug(f"创建 MCP 客户端：{name}")
    try:
        client = MultiServerMCPClient(config)
        tools = await client.get_tools()
        return client, tools
    except Exception as e:
        logger.error(f"创建 MCP 客户端 {name} 失败：{e}", exc_info=True)
        raise


_mcp_clients = {}
_mcp_tools_map: Dict[str, Any] = {}
_mcp_initialized = False
_mcp_lock = asyncio.Lock()


async def _ensure_mcp_tools_loaded():
    """MCP 工具懒加载，线程安全"""
    global _mcp_clients, _mcp_tools_map, _mcp_initialized

    if _mcp_initialized:
        return

    async with _mcp_lock:
        if _mcp_initialized:
            return

        logger.info("正在加载 MCP 工具...")
        try:
            order_client, order_tools = await create_mcp_client(
                "order",
                {
                    "command": "python",
                    "args": ["-m", "app.services.mcp.mcp_order_services"],
                    "cwd": str(PROJECT_ROOT),
                },
            )

            ticket_client, ticket_tools = await create_mcp_client(
                "ticket",
                {
                    "command": "python",
                    "args": ["-m", "app.services.mcp.mcp_ticket_services"],
                    "cwd": str(PROJECT_ROOT),
                },
            )

            _mcp_clients["order"] = order_client
            _mcp_clients["ticket"] = ticket_client

            for t in (order_tools + ticket_tools):
                _mcp_tools_map[t.name] = t

            _mcp_initialized = True
            logger.info(f"MCP 工具加载完成，共加载 {len(_mcp_tools_map)} 个工具")
        except Exception as e:
            logger.error(f"加载 MCP 工具失败：{e}", exc_info=True)
            raise


async def _call_mcp_tool(tool_name: str, args: dict) -> dict:
    """调用 MCP 工具，添加超时和异常处理"""
    try:
        await _ensure_mcp_tools_loaded()
    except Exception as e:
        return {"ok": False, "error": f"MCP 工具加载失败：{str(e)}"}

    tool = _mcp_tools_map.get(tool_name)
    if not tool:
        logger.warning(f"未找到 MCP tool: {tool_name}")
        return {"ok": False, "error": f"未找到 MCP tool：{tool_name}"}

    try:
        return await asyncio.wait_for(tool.ainvoke(args), timeout=30)
    except asyncio.TimeoutError:
        logger.error(f"调用 MCP 工具 {tool_name} 超时")
        return {"ok": False, "error": "工具调用超时，请稍后重试"}
    except Exception as e:
        logger.error(f"调用 MCP 工具 {tool_name} 失败：{e}", exc_info=True)
        return {"ok": False, "error": str(e)}


def _extract_order_no(text: str) -> Optional[str]:
    """从文本中提取订单号（支持多种格式）"""
    # 匹配模式：
    # 1. 包含连字符的订单号（如 AUTO-20260324-7353）
    # 2. 字母 + 数字（如 ORD20240101）
    # 3. 纯数字（如 20260324）
    # 使用更灵活的模式：字母、数字、连字符的组合
    m = re.search(r"[A-Za-z]+[-]?\d+[-]?\d*|[A-Za-z]*\d+[A-Za-z]*", text or "")
    return m.group() if m else None


# ==================== 工具处理类 ====================
class OrderToolHandler:
    """订单工具处理类"""

    async def handle_query_order(self, user_id: int, message: str, session_id: Optional[int] = None) -> str:
        order_no = _extract_order_no(message)
        if order_no is None:
            return "请提供订单号"
        result = await _call_mcp_tool("order_get", {"user_id": user_id, "order_no": order_no})
        return json.dumps(result, ensure_ascii=False)

    async def handle_modify_order(self, user_id: int, message: str, session_id: Optional[int] = None) -> str:
        """处理更新订单请求"""
        # 提取订单号
        order_no = _extract_order_no(message)
        if order_no is None:
            return "请提供要修改的订单号。"

        # 使用 LLM 解析要更新的字段
        update_fields = await self._parse_update_fields_by_llm(user_id, message, order_no)

        if not update_fields:
            return "抱歉，我没有理解您要修改什么信息。请明确说明要修改的内容，例如：'备注改为尽快发货' 或 '收件人改成张三'。"

        # 验证至少有一个字段
        if len(update_fields) == 0:
            return "请说明要修改什么信息（如：备注、收货地址、订单状态等）。"

        # 调用 MCP 工具
        result = await _call_mcp_tool(
            "order_update",
            {
                "user_id": user_id,
                "order_no": order_no,
                **update_fields,
            },
        )
        return json.dumps(result, ensure_ascii=False)

    async def handle_create_order(self, user_id: int, message: str, session_id: Optional[int] = None) -> str:
        """
        使用结构化输出创建订单。
        """
        try:
            # 1. 使用提示词引导模型返回正确的扁平 JSON 结构
            prompt = ChatPromptTemplate.from_messages([
                ("system", ORDER_STRUCTURED_EXTRACTION_PROMPT),
                ("user", "{user_message}")
            ])

            structured_llm = get_structured_llm(OrderInfoExtract)

            chain = prompt | structured_llm
            extract = await chain.ainvoke({"user_message": message})

            # 2. 检查必填字段
            if not extract.items:
                return "请提供商品信息（名称、数量、单价）。"

            missing_fields = []
            if not extract.receiver_name:
                missing_fields.append("收货人姓名")
            if not extract.receiver_phone:
                missing_fields.append("收货人电话")
            if not extract.shipping_address:
                missing_fields.append("收货地址")

            if missing_fields:
                return f"订单信息不完整，请补充以下信息：{', '.join(missing_fields)}。"

            # 3. 自动生成订单号
            date_str = datetime.now().strftime('%Y%m%d')
            random_str = f"{random.randint(1000, 9999)}"
            order_no = f"AUTO-{date_str}-{random_str}"

            # 4. 计算总金额
            total_amount = sum(item.quantity * float(item.price) for item in extract.items)
            total_amount = round(total_amount, 2)

            # 5. 状态映射
            status_map = {
                "待付款": "pending", "已付款": "paid", "已发货": "shipped",
                "已完成": "completed", "已取消": "cancelled", "pending": "pending",
                "paid": "paid", "shipped": "shipped", "completed": "completed", "cancelled": "cancelled"
            }
            status = status_map.get(extract.status, "pending")

            # 6. 构造订单创建数据
            order_create_data = OrderCreate(
                order_no=order_no,
                user_id=user_id,
                items=extract.items,
                total_amount=total_amount,
                status=status,
                receiver_name=extract.receiver_name,
                receiver_phone=extract.receiver_phone,
                shipping_address=extract.shipping_address,
                remark=extract.remark or "",
            )

            # 7. 调用 MCP 工具
            result = await _call_mcp_tool(
                "order_create",
                order_create_data.model_dump(mode="json")
            )

            if isinstance(result, dict):
                logger.info(f"订单创建结果：{result}")
                return json.dumps(result, ensure_ascii=False)
            elif isinstance(result, list) and len(result) > 0:
                # 从列表中提取第一个元素的 text 字段
                first_item = result[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    # text 字段是 JSON 字符串，需要再次解析
                    try:
                        nested_result = json.loads(first_item["text"])
                        logger.info(f"订单创建结果：{nested_result}")
                        return json.dumps(nested_result, ensure_ascii=False)
                    except json.JSONDecodeError:
                        # 如果不是 JSON，直接返回文本
                        return first_item["text"]
                else:
                    # 如果列表中的元素不是字典或没有 text 字段，直接返回结果
                    logger.info(f"订单创建结果：{result}")
                    return json.dumps(result, ensure_ascii=False)
            else:
                # 如果结果不是字典或列表，直接返回结果
                logger.info(f"订单创建结果：{result}")
                return str(result)

        except Exception as e:
            logger.error(f"创建订单失败：{e}", exc_info=True)
            return f"解析订单信息失败，请重新描述您的订单需求（错误：{str(e)[:50]}）"

    async def handle_delete_order(self, user_id: int, message: str, session_id: Optional[int] = None) -> str:
        order_no = _extract_order_no(message)
        if order_no is None:
            return "请提供要删除的订单号（如：AUTO-20260324-7353 或 20260324）。"
        result = await _call_mcp_tool(
            "order_delete",
            {"user_id": user_id, "order_no": order_no},  # ← 改为 order_no
        )
        return json.dumps(result, ensure_ascii=False)

    async def _parse_update_fields_by_llm(self, user_id: int, message: str, order_no: str) -> Optional[Dict[str, Any]]:
        """使用 LLM 从用户消息中解析要更新的订单字段"""

        prompt = ORDER_UPDATE_PROMPT.format(message=message,order_no=order_no,user_id=user_id)

        try:
            response = await call_llm(prompt)
            # 清理响应，确保是有效的 JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            update_fields = json.loads(response)
            print("啊啊啊啊啊啊啊啊啊")
            print(update_fields)

            # 验证返回的是字典
            if not isinstance(update_fields, dict):
                return None

            return update_fields
        except Exception as e:
            logger.error(f"LLM 解析更新字段失败：{e}")
            return None


class TicketToolHandler:
    """工单工具处理类"""

    async def handle_create_return(self, user_id: int, message: str, session_id: Optional[int] = None) -> str:
        order_no = _extract_order_no(message)
        if order_no is None:
            return "请提供要退货的订单号。"
        result = await _call_mcp_tool(
            "ticket_create",
            {
                "user_id": user_id,
                "ticket_no": f"AUTO-return-{user_id}-{order_no}",
                "type": "return",
                "description": message,
                "order_no": order_no,  # ← 传递订单号
                "session_id": session_id,
                "title": "用户退货申请",
            },
        )
        return json.dumps(result, ensure_ascii=False)

    async def handle_create_complaint(self, user_id: int, message: str, session_id: Optional[int] = None) -> str:
        order_no = _extract_order_no(message)
        if order_no is None:
            return "请提供要投诉关联的订单号。"
        result = await _call_mcp_tool(
            "ticket_create",
            {
                "user_id": user_id,
                "ticket_no": f"AUTO-complaint-{user_id}-{order_no}",
                "type": "complaint",
                "description": message,
                "order_no": order_no,  # ← 传递订单号
                "session_id": session_id,
                "title": "用户投诉",
            },
        )
        return json.dumps(result, ensure_ascii=False)


class ToolExecutor:
    """工具执行器 - 使用策略模式分发请求"""

    def __init__(self):
        self._order_handler = OrderToolHandler()
        self._ticket_handler = TicketToolHandler()

        self._handlers: Dict[str, Any] = {
            "query_order": self._order_handler.handle_query_order,
            "modify_order": self._order_handler.handle_modify_order,
            "create_order": self._order_handler.handle_create_order,
            "delete_order": self._order_handler.handle_delete_order,
            "create_return": self._ticket_handler.handle_create_return,
            "create_complaint": self._ticket_handler.handle_create_complaint,
        }

    async def execute(self, intent: str, user_id: int, message: str, session_id: Optional[int] = None) -> str:
        """执行对应意图的工具"""
        handler = self._handlers.get(intent)
        if not handler:
            logger.warning(f"未找到意图 {intent} 的处理程序")
            return "无法处理该请求。"

        try:
            return await handler(user_id, message, session_id)
        except Exception as e:
            logger.error(f"执行工具 {intent} 时出错：{e}", exc_info=True)
            return f"处理请求时发生错误：{str(e)}"


# 全局工具执行器单例
_tool_executor: Optional[ToolExecutor] = None


async def execute_tool(intent: str, user_id: int, last_user_message: str,
                       session_id: Optional[int] = None) -> str:
    """
    供 tool_calls_node 调用的业务工具入口
    """
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()

    return await _tool_executor.execute(intent, user_id, last_user_message, session_id)


# ==================== MCP 优雅关闭 ====================
async def cleanup_mcp_clients():
    """优雅关闭 MCP 客户端连接"""
    global _mcp_clients, _mcp_tools_map, _mcp_initialized
    logger.info("正在关闭 MCP 客户端连接...")

    for name, client in _mcp_clients.items():
        try:
            if hasattr(client, 'aclose'):
                await client.aclose()
            elif hasattr(client, 'close'):
                client.close()
            logger.info(f"已关闭 {name} MCP 客户端")
        except Exception as e:
            logger.warning(f"关闭 {name} MCP 客户端失败：{e}")

    _mcp_clients.clear()
    _mcp_tools_map.clear()
    _mcp_initialized = False

if __name__ == '__main__':
    message="""
    帮我删除订单ID为5的订单
    """
    result=asyncio.run(execute_tool(
        intent="delete_order",
        user_id=1,
        last_user_message=message,
    )
    )
    print(result)