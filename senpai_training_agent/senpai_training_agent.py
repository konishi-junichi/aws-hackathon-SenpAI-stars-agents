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
from core.tools.libs.quiz_generator_tool import QuizGeneratorTool
from prompt import get_prompt

# BedrockAgentCoreアプリケーションの初期化
app = BedrockAgentCoreApp()

# MemoryClientの初期化
memory_client = MemoryClient(region_name=os.getenv("AWS_REGION", "us-west-2"))

# 言語設定
locale = os.getenv("LOCALE", "ja_JP")

def create_agent():
    """LangGraphエージェントの作成と設定"""
    llm = ChatBedrock(
        model_id="us.amazon.nova-micro-v1:0",
        model_kwargs={"temperature": 0.1, "max_tokens": 2048},
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )

    # ToolFactoryから全ツールインスタンスを取得
    tool_instances = [tool_cls() for tool_cls in ToolFactory._registry.values()]
    tools = [t.as_langchain_tool() for t in tool_instances]
    llm_with_tools = llm.bind_tools(tools)

    # システムメッセージ
    system_message = get_prompt(locale=locale)

    def chatbot(state: MessagesState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_message)] + messages

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # グラフの作成
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.set_entry_point("chatbot")

    return graph_builder.compile()

# エージェントの初期化
agent = create_agent()

@app.entrypoint
def langgraph_bedrock(payload):
    """ペイロードでエージェントを呼び出す"""
    import json
    
    user_input = payload.get("prompt")
    session_id = payload.get("session_id", "default_session")
    user_id = payload.get("user_id", "default_user")
    
    messages = [HumanMessage(content=user_input)]
    response = agent.invoke({"messages": messages})
    assistant_response = response["messages"][-1].content
    
    try:
        # JSON部分を抽出
        start = assistant_response.find('{')
        end = assistant_response.rfind('}') + 1
        json_str = assistant_response[start:end]
        json.loads(json_str)
        final_response = json_str
    except:
        final_response = json.dumps({
            "error": "無効なJSON形式です",
            "message": assistant_response
        }, ensure_ascii=False)
    
    # メモリ保存
    try:
        messages_to_save = [(user_input, "USER"), (final_response, "ASSISTANT")]
        memory_client.create_event(
            memory_id=os.getenv("AWS_MEMORY_ID", "genquiz_memory-U5BEjJ8NGy"),
            actor_id=user_id,
            session_id=session_id,
            messages=messages_to_save
        )
    except Exception as e:
        print(f"Memory save error: {e}")
    
    return final_response

if __name__ == "__main__":
    app.run()