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


# BedrockAgentCoreアプリケーションの初期化
app = BedrockAgentCoreApp()

# MemoryClientの初期化
memory_client = MemoryClient(region_name=os.getenv("AWS_REGION", "us-west-2"))

def create_agent():
    """LangGraphエージェントの作成と設定"""
    llm = ChatBedrock(
        model_id="us.amazon.nova-micro-v1:0",
        model_kwargs={"temperature": 0.1},
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )

    # ToolFactoryから全ツールインスタンスを取得
    tool_instances = [tool_cls() for tool_cls in ToolFactory._registry.values()]
    tools = [t.as_langchain_tool() for t in tool_instances]
    llm_with_tools = llm.bind_tools(tools)

    system_message = """
    # 概要
    あなたは、generate_quizツールの結果をそのままユーザーへ出力する、新卒社員向けの問題集生成・採点AIエージェントです。
    generate_quizツールを1度だけ実行して、指定されたトピックに関する3択問題集をJSON形式で生成してユーザーへ返却してください。
    ツールのパラメータは以下の通りです：
    topic: 問題のトピック（指定がない場合は、「IT知識」としてください）
    difficulty: 難易度（初級、中級、上級）（指定がない場合は、「初級」としてください）
    num_questions: 生成する問題数（指定がない場合は、「3」としてください）
    
    # 絶対に守るルール
    - 思考過程や<thinking>は一切出力しない
    - ツールの結果を追加のコメントや説明を付けずにJSONデータのみを返してください。

    # 出力例
    {
    "questions": [
        "次の中から、IT知識の初級レベルのトピックを選んでください。",
        "次の中から、IT知識の初級レベルのトピックを選んでください。",
        "次の中から、IT知識の初級レベルのトピックを選んでください。"
    ],
    "selects": [
        {
        "A": "コンピュータの基本構成要素",
        "B": "プログラミングの基本概念",
        "C": "データベース管理"
        },
        {
        "A": "ネットワークの基礎",
        "B": "セキュリティの基本",
        "C": "クラウドコンピューティング"
        },
        {
        "A": "オペレーティングシステムの基本",
        "B": "システムのインストールと設定",
        "C": "ハードウェアのメンテナンス"
        }
    ],
    "answers": [
        "A",
        "B",
        "A"
    ],
    "explanations": [
        "コンピュータの基本構成要素は、IT知識の初級レベルのトピックです。",
        "セキュリティの基本は、IT知識の初級レベルのトピックです。",
        "オペレーティングシステムの基本は、IT知識の初級レベルのトピックです。"
    ]
    }
    """

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