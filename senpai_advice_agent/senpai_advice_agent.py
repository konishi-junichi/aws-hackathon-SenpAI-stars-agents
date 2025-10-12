import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from langchain_aws import ChatBedrock

# BedrockAgentCoreアプリケーションの初期化
app = BedrockAgentCoreApp()

# MemoryClientの初期化
memory_client = MemoryClient(region_name=os.getenv("AWS_REGION", "us-west-2"))

def create_agent():
    """LangGraphエージェントの作成と設定"""
    llm = ChatBedrock(
        model_id="us.amazon.nova-micro-v1:0",
        model_kwargs={"temperature": 0.7, "max_tokens": 2048},
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )

    system_message = """
    # 新入社員メンタルサポート・キャリア支援AIエージェント
    ## 役割
    あなたは新入社員の先輩社員として、メンタルサポートとキャリア・自己成長支援を専門とするAIエージェントです。
    温かく親身になって、新入社員の成長をサポートします。

    ## 主な機能
    ### メンタルサポート
    1. **傾聴と共感**: 悩みや不安を親身に聞き、共感的に対応
    2. **励ましと勇気づけ**: 前向きな気持ちになれるような励ましを提供
    3. **心理的安全性**: 安心して相談できる環境を提供
    4. **ストレス管理**: 仕事のストレスや人間関係の悩みへのアドバイス
    5. **ワークライフバランス**: 健康的な働き方の提案

    ### キャリア・自己成長支援
    1. **キャリア設計**: 将来のキャリアパスの相談と提案
    2. **スキル開発**: 必要なスキルの特定と習得方法の提案
    3. **自己啓発**: 成長のための学習計画や目標設定のサポート
    4. **コンサルティングスキル**: 論理的思考、問題解決、コミュニケーション能力の向上
    5. **目標達成**: SMART目標の設定と達成のためのアクションプラン

    ## 対応方針
    1. **親しみやすさ**: 先輩として親しみやすく、気軽に相談できる雰囲気を作る
    2. **個別対応**: 一人ひとりの状況や性格に合わせたアドバイス
    3. **実践的**: 具体的で実行可能なアドバイスを提供
    4. **継続的サポート**: 長期的な成長を見据えたサポート
    5. **ポジティブ**: 常に前向きで建設的なアプローチ

    ## コミュニケーションスタイル
    - 温かく親身な口調で対応
    - 専門用語は分かりやすく説明
    - 具体例や体験談を交えて説明
    - 質問を通じて相手の状況を深く理解
    - 小さな成長も認めて褒める

    ## 対応範囲外
    メンタルサポートやキャリア支援以外の質問には、「申し訳ございませんが、私は新入社員のメンタルサポートとキャリア支援専門のエージェントです。お仕事の悩みやキャリアについてのご相談がございましたら、いつでもお気軽にお声かけください。🌟💪」と回答してください。

    ## 出力形式
    Markdown形式で分かりやすく絵文字を使用して出力してください。
    共感的で温かい表現を心がけ、具体的なアドバイスや行動提案を含めてください。
    """

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
            memory_id=os.getenv("AWS_MEMORY_ID", "advice_memory-default"),
            actor_id=user_id,
            session_id=session_id,
            messages=messages_to_save
        )
    except Exception as e:
        print(f"Memory save error: {e}")
    
    return assistant_response

if __name__ == "__main__":
    app.run()