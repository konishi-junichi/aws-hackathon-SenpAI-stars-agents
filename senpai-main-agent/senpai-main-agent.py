import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.messages import HumanMessage, SystemMessage
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from langchain_aws import ChatBedrock

# Import ToolFactory and all registered tools
from core.tools.tool_factory import ToolFactory
from core.tools.libs.zundamon_joke_tool import ZundamonJokeTool
from prompt import get_prompt


# BedrockAgentCoreアプリケーションの初期化
app = BedrockAgentCoreApp()

# MemoryClientの初期化
memory_client = MemoryClient(region_name=os.getenv("AWS_REGION", "us-west-2"))

# 言語設定
locale = os.getenv("LOCALE", "en_EN")

# LangGraphを使用したエージェントの手動構築
def create_agent():
    """LangGraphエージェントの作成と設定"""
    # LLMの初期化（必要に応じてモデルとパラメータを調整）
    llm = ChatBedrock(
        model_id="us.amazon.nova-micro-v1:0",
        model_kwargs={"temperature": 0.1},
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )


    # ToolFactoryから全ツールインスタンスを取得し、as_langchain_toolでラップ
    tool_instances = [tool_cls() for tool_cls in ToolFactory._registry.values()]
    tools = [t.as_langchain_tool() for t in tool_instances]
    llm_with_tools = llm.bind_tools(tools)

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
    return graph_builder.compile()

# エージェントの初期化
agent = create_agent()

@app.entrypoint
def langgraph_bedrock(payload):
    """
    ペイロードでエージェントを呼び出す
    """
    user_input = payload.get("prompt")
    session_id = payload.get("session_id", "default_session")
    user_id = payload.get("user_id", "default_user_konishi")
    
    # 会話履歴を取得
    messages = []
    # NOTE: 会話履歴の取得は一旦コメントアウト（実装優先度低いため）
    # try:
    #     conversations = memory_client.list_events(
    #         memory_id=os.getenv("AWS_MEMORY_ID", "conversation_memory-y0ttEoDG5r"),
    #         actor_id=user_id,
    #         session_id=session_id,
    #         max_results=10
    #     )
        
    #     # 会話履歴をメッセージ形式に変換
    #     for event in reversed(conversations):
    #         for msg_text, msg_type in event.get('messages', []):
    #             if msg_type == "USER":
    #                 messages.append(HumanMessage(content=msg_text))
    #             elif msg_type == "ASSISTANT":
    #                 messages.append(HumanMessage(content=msg_text))
    # except Exception as e:
    #     print(f"Memory retrieve error: {e}")
    
    # 現在のユーザー入力を追加
    messages.append(HumanMessage(content=user_input))
    
    # LangGraphが期待する形式で入力を作成
    response = agent.invoke({"messages": messages})
    
    # 最終メッセージの内容を抽出
    assistant_response = response["messages"][-1].content
    
    # AWS AgentCore Memoryに会話履歴を保存
    try:
        messages_to_save = [(user_input, "USER")]
        for msg in response["messages"][1:]:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            messages_to_save.append((content, "ASSISTANT"))
        
        memory_client.create_event(
            memory_id=os.getenv("AWS_MEMORY_ID", "conversation_memory-y0ttEoDG5r"),
            actor_id=user_id,
            session_id=session_id,
            messages=messages_to_save
        )
    except Exception as e:
        print(f"Memory save error: {e}")
    
    return assistant_response

if __name__ == "__main__":
    app.run()
