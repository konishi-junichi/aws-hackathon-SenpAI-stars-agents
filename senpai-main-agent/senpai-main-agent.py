import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.messages import HumanMessage, SystemMessage
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from langchain_aws import ChatBedrock

# Import logger
from core.logger import setup_logger, get_contextual_logger

# Import ToolFactory and all registered tools
from core.tools.tool_factory import ToolFactory
from core.tools.libs.zundamon_joke_tool import ZundamonJokeTool
from core.tools.libs.chat_history_summarize_tool import Chat_history_summarize_tool
from core.tools.tool_interface import Tool
from prompt import get_prompt


# Initialize logger
logger = setup_logger(
    name="senpai.main_agent",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format_type=os.getenv("LOG_FORMAT", "console"),
    log_file=os.getenv("LOG_FILE")
)

logger.info("Starting SenpAI Main Agent application")

# BedrockAgentCoreアプリケーションの初期化
app = BedrockAgentCoreApp()

# MemoryClientの初期化
memory_client = MemoryClient(region_name=os.getenv("AWS_REGION", "us-west-2"))
logger.info("MemoryClient initialized", extra={"region": os.getenv("AWS_REGION", "us-west-2")})

# 言語設定
locale = os.getenv("LOCALE", "en_EN")

# LangGraphを使用したエージェントの手動構築
def create_agent():
    """LangGraphエージェントの作成と設定"""
    logger.info("Creating LangGraph agent")
    
    # LLMの初期化（必要に応じてモデルとパラメータを調整）
    llm = ChatBedrock(
        model_id="us.amazon.nova-micro-v1:0",
        model_kwargs={"temperature": 0.1},
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )
    logger.info("LLM initialized", extra={"model_id": "us.amazon.nova-micro-v1:0"})

    # ToolFactoryから全ツールインスタンスを取得し、as_langchain_toolでラップ
    tool_instances = [tool_cls() for tool_cls in ToolFactory._registry.values()]
    
    # Store tool instances globally for context setting
    global global_tool_instances
    global_tool_instances = tool_instances
    
    tools = [t.as_langchain_tool() for t in tool_instances]
    llm_with_tools = llm.bind_tools(tools)
    
    logger.info("Tools loaded", extra={"tool_count": len(tools), "tools": [t.name for t in tool_instances]})

    # システムメッセージ
    system_message = get_prompt(locale=locale)

    # チャットボットノードの定義
    def chatbot(state: MessagesState):
        # システムメッセージがまだ存在しない場合は追加
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_message)] + messages

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # グラフの作成
    graph_builder = StateGraph(MessagesState)

    # ノードの追加
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(tools))

    # エッジの追加
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    graph_builder.add_edge("tools", "chatbot")

    # エントリーポイントの設定
    graph_builder.set_entry_point("chatbot")

    # グラフのコンパイル
    compiled_graph = graph_builder.compile()
    logger.info("LangGraph agent compiled successfully")
    return compiled_graph

# エージェントの初期化
agent = create_agent()
logger.info("Agent created and ready for use")

# Global variable to store tool instances for context setting
global_tool_instances = []

def set_tool_context(user_id: str, session_id: str):
    """Set context for all tool instances."""
    context = {
        "memory_id": os.getenv("AWS_MEMORY_ID", "conversation_memory-y0ttEoDG5r"),
        "actor_id": user_id,
        "user_id": user_id,
        # to-do: use memory or other better way to implement
        "session_id": "session_id_" + user_id
    }

    Tool.set_context(context)  # Update class-level context for any static access

    logger.info("Tool context set", extra=context)

@app.entrypoint
def langgraph_bedrock(payload):
    """
    ペイロードでエージェントを呼び出す
    """
    user_input = payload.get("prompt")
    session_id = payload.get("session_id", "default_session")
    user_id = payload.get("user_id", "default_user_konishi")
    
    # Create contextual logger for this request
    request_logger = get_contextual_logger(
        "senpai.request",
        user_id=user_id,
        session_id=session_id
    )
    
    request_logger.info("Processing user request", extra={
        "prompt_length": len(user_input) if user_input else 0,
    })
    
    # Set context for all tools
    set_tool_context(user_id, session_id)
    
    # 会話履歴を取得
    messages = []

    # 現在のユーザー入力を追加
    messages.append(HumanMessage(content=user_input))
    
    try:
        # LangGraphが期待する形式で入力を作成
        request_logger.info("Invoking LangGraph agent")
        response = agent.invoke({"messages": messages})
        
        # 最終メッセージの内容を抽出
        assistant_response = response["messages"][-1].content
        
        request_logger.info("Agent response generated", extra={
            "response_length": len(assistant_response),
            "total_messages": len(response["messages"])
        })
        
    except Exception as e:
        request_logger.error("Agent invocation failed", extra={"error": str(e)}, exc_info=True)
        return "申し訳ないのだ！ちょっと調子が悪いみたいなのだ...💧 もう一度試してみてほしいのだ！"
    
    # AWS AgentCore Memoryに会話履歴を保存
    try:
        messages_to_save = [(user_input, "USER")]
        for msg in response["messages"][1:]:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            messages_to_save.append((content, "ASSISTANT"))
        
        memory_client.create_event(
            memory_id=os.getenv("AWS_MEMORY_ID", "conversation_memory-y0ttEoDG5r"),
            actor_id=user_id,
            # to-do: use memory or other better way to implement
            session_id="session_id_" + user_id,
            messages=messages_to_save,
        )
        
        request_logger.info("Conversation saved to memory", extra={
            "saved_messages": len(messages_to_save)
        })
        
    except Exception as e:
        request_logger.error("Memory save error", extra={"error": str(e)}, exc_info=True)
    
    request_logger.info("Request completed successfully")
    return assistant_response

if __name__ == "__main__":
    logger.info("Starting SenpAI Main Agent server")
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Server error", extra={"error": str(e)}, exc_info=True)
        raise
