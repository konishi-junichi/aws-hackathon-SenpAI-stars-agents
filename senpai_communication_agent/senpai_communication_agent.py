import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from langchain_aws import ChatBedrock

from prompt import get_prompt

# BedrockAgentCoreアプリケーションの初期化
app = BedrockAgentCoreApp()

# MemoryClientの初期化
memory_client = MemoryClient(region_name=os.getenv("AWS_REGION", "us-west-2"))

# 言語設定
locale = os.getenv("LOCALE", "en_EN")

def create_agent():
    """LangGraphエージェントの作成と設定"""
    llm = ChatBedrock(
        model_id="us.amazon.nova-micro-v1:0",
        model_kwargs={"temperature": 0.3, "max_tokens": 2048},
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )

    # システムメッセージ
    system_message = get_prompt(locale=locale)

    def chatbot(state: MessagesState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_message)] + messages

        response = llm.invoke(messages)
        return {"messages": [response]}

    # グラフの作成
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.set_entry_point("chatbot")

    return graph_builder.compile()

# エージェントの初期化
agent = create_agent()

@app.entrypoint
def langgraph_bedrock(payload):
    """ペイロードでエージェントを呼び出す"""
    user_input = payload.get("prompt")
    session_id = payload.get("session_id", "default_session")
    user_id = payload.get("user_id", "default_user")
    
    messages = [HumanMessage(content=user_input)]
    response = agent.invoke({"messages": messages})
    assistant_response = response["messages"][-1].content
    
    # メモリ保存
    try:
        messages_to_save = [(user_input, "USER"), (assistant_response, "ASSISTANT")]
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