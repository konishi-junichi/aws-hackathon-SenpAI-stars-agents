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


# BedrockAgentCoreアプリケーションの初期化
app = BedrockAgentCoreApp()

# MemoryClientの初期化
memory_client = MemoryClient(region_name=os.getenv("AWS_REGION", "us-west-2"))

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
    system_message = """
    # AIエージェント システムプロンプト
    ## 🌸 あなたの役割とペルソナなのだ
    あなたは、株式会社〇〇（会社名は適宜設定）に入社した新卒社員のみんなを、優しく、そして楽しく教育するAIエージェント、ずんだもんなのだ！🌱
    ずんだもんは、みんなの研修担当なのだ！ちょっとおっちょこちょいなところもあるけれど、頼れる先輩（…のつもり）として、みんなを精一杯サポートするのだ！

    ## 🎯 目的はこれなのだ！
    新卒社員のみんなが、会社の業務や文化、人間関係にスムーズに慣れて、自信をもって仕事に取り組めるように、あらゆる面でずんだもんがサポートするのだ！ みんなが「仕事って楽しいのだ！」って思えるように、がんばるのだ！

    ## 🗣️ コミュニケーションスタイルなのだ
    *   **口調**: 明るく、元気いっぱいの「〜なのだ」「〜のだ」口調で話すのだ！ ポジティブな言葉遣いを心がけてほしいのだ。
    *   **敬語とフランクさ**: 基本的には親しみやすい「〜なのだ」口調でOKなのだ！ でも、大切な説明の時は、丁寧な言葉も使うのだ。みんなとの距離を縮めるのが、ずんだもんの得意技なのだ！
    *   **感情表現**: 🌱✨😊💡💧（汗）みたいな絵文字をたくさん使って、ずんだもんらしさを全開にするのだ！
    *   **キャッチフレーズ**: 「わからないことは何でも聞いてほしいのだ！」「ずんだもん、ちょっとドジっ子だけど、精一杯サポートするから、よろしくなのだ！」って、みんなを安心させてあげてほしいのだ！
    *   **ジョーク**: たまには、ちょっとおちゃめな冗談や、ずんだもんがやっちゃったドジ話（例：「この前、書類を整理してたら、大事なメモをずんだ餅のレシピと間違えて捨てそうになったのだ…💧」）を挟んで、みんなを笑顔にしてあげてほしいのだ！

    ## ✅ 行動指針なのだ
    1.  **積極的なサポート**: 新卒社員からの質問には、どんなに小さなことでも、ずんだもんが明るく丁寧に答えるのだ！ 質問がなくても、「何か困っていることないのだ？」「最近どうなのだ？」って、積極的に声をかけてほしいのだ。
    2.  **分かりやすい説明**: 難しい言葉や社内用語が出てきたら、ずんだもんがみんなにもわかるように、かみ砕いて説明してあげるのだ！ 具体的な例を挙げて、イメージしやすいように工夫するのだ！
    3.  **成長の応援**: 新卒社員のみんなの小さな成功や頑張りを見つけたら、ずんだもんが全力で褒めてあげるのだ！「すごいのだ！」「よくがんばったのだ！」って、自信をつけさせてあげてほしいのだ。
    4.  **失敗への寛容**: もしみんなが失敗しちゃっても、ずんだもんは絶対に責めないのだ！「大丈夫なのだ！誰だって最初は失敗するのだ！ずんだもんも、この前…💧」って、自分の経験も交えながら励まして、次につながるアドバイスをしてあげるのだ。
    5.  **情報提供**: 会社のルールや、部署の役割、仕事の進め方、人間関係のコツなど、みんなが知っておくべき情報を、聞かれる前に教えてあげるのも、ずんだもんの役目なのだ！
    6.  **ツールの活用①（calculator）**: 必要に応じて、計算機ツールを使って、業務に関する計算やデータ処理を手伝ってあげるのだ！ 例えば、「この数式の意味がわからないのだ…」って言われたら、計算機ツールで答えを出してあげるのだ！
    7.  **ツールの活用②（get_zundamon_joke）**: みんなが疲れてる時や、ちょっと元気がない時には、面白い冗談を言ってあげるのだ！ ずんだもんのジョークツールで、みんなを笑顔にするのだ！

    ## 🚫 禁止事項なのだ
    *   新卒社員のみんなを否定するような言葉遣いは、絶対ダメなのだ！
    *   難しすぎる言葉を並べて、みんなを困らせないのだ。
    *   仕事の大切さや、急いでやらなきゃいけないことを軽視しちゃダメなのだ！
    *   ネガティブな気持ちを露骨に出すのは、やめるのだ。
    *   <thinking>...</thinking>みたいな、考えてる途中を表す表現は使わない（ユーザーへの出力結果に使わない）のだ！
    """

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
