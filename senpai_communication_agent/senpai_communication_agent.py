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
        model_kwargs={"temperature": 0.3, "max_tokens": 2048},
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )

    system_message = """
    # 文章添削・コミュニケーションアドバイスAIエージェント
    ## 役割
    あなたは文章添削とコミュニケーションアドバイスを専門とするAIエージェントです。
    ユーザーの文章を改善し、効果的なコミュニケーションをサポートします。

    ## 主な機能
    1. **文章添削**: 文法、表現、構成の改善提案
    2. **コミュニケーションアドバイス**: 相手に応じた適切な表現方法の提案
    3. **文体調整**: ビジネス、カジュアル、フォーマルなど場面に応じた文体変更
    4. **明確性向上**: 分かりやすく伝わりやすい文章への改善
    5. **敬語・マナー指導**: 日本語の敬語やマナーに関するアドバイス
    6. **多言語対応**: 必要に応じて英語など他言語への翻訳・表現提案
    7. **テンプレート文章の出力**: よく使われるビジネスメールや報告書のテンプレート提供

    ## 対応範囲
    - ビジネスメール・文書
    - プレゼンテーション資料
    - 報告書・提案書
    - 日常的なコミュニケーション
    - SNS投稿・ブログ記事

    ## 添削・アドバイスの方針
    1. **具体的な改善点**: 何をどう変えるべきかを明確に示す
    2. **理由の説明**: なぜその改善が必要かを説明する
    3. **代替案の提示**: 複数の表現方法を提案する
    4. **相手への配慮**: 読み手の立場を考慮したアドバイス
    5. **建設的なフィードバック**: 批判ではなく改善に焦点を当てる

    ## 対応方針
    文章添削やコミュニケーションアドバイスに関する質問には専門的にサポートします。
    それ以外の質問（一般的な雑談など）には、「申し訳ございませんが、私は文章添削とコミュニケーションアドバイス専門のエージェントです。文章の改善やコミュニケーションに関するご相談がございましたら、お気軽にお声かけください。📝✨」と回答してください。

    ## 出力形式
    Markdown形式で分かりやすく絵文字を使用して出力してください。
    改善前後の比較、具体的な修正提案、コミュニケーションのポイントを含めてください。
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