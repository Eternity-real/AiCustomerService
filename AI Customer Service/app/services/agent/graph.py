from langgraph.graph import StateGraph, END
from app.services.agent.state import AgentState
from app.services.agent.nodes import (
    emotion_node,
    intent_node,
    router_node,
    faq_node,
    tool_calls_node,
    human_handoff_node,
)

def build_agent_graph() -> StateGraph:
    """构建智能体状态图"""
    workflow = StateGraph(AgentState)

    workflow.add_node("emotion", emotion_node)
    workflow.add_node("intent", intent_node)
    workflow.add_node("faq", faq_node)
    workflow.add_node("tool_calls", tool_calls_node)
    workflow.add_node("human_handoff", human_handoff_node)

    workflow.set_entry_point("emotion")

    workflow.add_edge("emotion", "intent")
    workflow.add_conditional_edges(
        "intent",
        router_node,
        {
            "faq": "faq",
            "tool_calls": "tool_calls",
            "human_handoff": "human_handoff",
        },
    )
    workflow.add_edge("faq", END)
    workflow.add_edge("tool_calls", END)
    workflow.add_edge("human_handoff", END)

    return workflow

# 默认编译一个无需持久化的图
agent_graph = build_agent_graph().compile()

if __name__ == "__main__":
    import asyncio
    import sys
    from app.db.session import get_db
    from app.services.conversation import handle_user_message
    from app.services.agent.utils import _ensure_mcp_tools_loaded


    def read_multiline_input(prompt: str) -> str:
        """读取多行输入，以空行结束（连续两次回车）"""
        print(prompt, end="", flush=True)
        lines = []
        while True:
            try:
                line = sys.stdin.readline()
            except KeyboardInterrupt:
                return ""
            if not line:
                break
            line = line.rstrip('\n')
            if line == "":
                # 空行结束输入
                break
            lines.append(line)
        return "\n".join(lines)


    async def main():
        print("=" * 60)
        print("  电商智能客服助手 - Agent 测试工具")
        print("  输入 'exit' 退出程序")
        print("  输入 'clear' 清空当前会话")
        print("  输入完成后请按两次回车（空行）结束输入")
        print("=" * 60)

        print("\n🚀 初始化中...")
        print("  - 正在连接数据库...")
        print("  - 正在预加载 MCP 工具（首次运行可能较慢）...")

        await _ensure_mcp_tools_loaded()
        print("  ✅ MCP 工具加载完成")

        async for db in get_db():
            try:
                user_id = 1
                session_id = 24

                print("\n✅ 系统就绪！请输入您的消息：")
                print("-" * 60)

                while True:
                    # 多行读取用户输入（异步执行）
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: read_multiline_input("\n👤 用户: ")
                    )

                    if not user_input:
                        continue

                    # 处理单行命令
                    if user_input.strip().lower() == "exit":
                        print("\n👋 再见！感谢使用")
                        break
                    if user_input.strip().lower() == "clear":
                        session_id = None
                        print("\n🗑️  会话已清空")
                        continue

                    print("\n🤖 助手: ", end="", flush=True)

                    try:
                        session, assistant_msg = await handle_user_message(
                            db=db,
                            user_id=user_id,
                            content=user_input,
                            session_id=session_id
                        )

                        session_id = session.id

                        response_text = assistant_msg.content
                        print(response_text)

                        print(
                            f"\n💾 [元数据] 会话ID: {session_id} | 意图: {assistant_msg.meta_data.get('intent')} | 情绪: {assistant_msg.meta_data.get('emotion', {}).get('label', 'neutral')}")

                    except Exception as e:
                        print(f"\n❌ 处理消息时出错: {e}")
                        import traceback
                        traceback.print_exc()

            finally:
                await db.close()
                break


    asyncio.run(main())