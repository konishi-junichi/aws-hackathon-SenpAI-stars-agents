# 必要なライブラリのインポート
import operator
import math
import random

from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langchain_aws import ChatBedrock


# BedrockAgentCoreアプリケーションの初期化
app = BedrockAgentCoreApp()

# 計算機ツールの作成
@tool
def calculator(expression: str) -> str:
    """
    数式の計算結果を返す

    Args:
        expression: 文字列形式の数式 (例: "2 + 3 * 4", "sqrt(16)", "sin(pi/2)")

    Returns:
        計算結果を文字列で返す
    """
    try:
        # 安全な関数のみを使用可能にする辞書を定義
        safe_dict = {
            "__builtins__": {},
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow,
            # 数学関数
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "log": math.log, "log10": math.log10, "exp": math.exp,
            "pi": math.pi, "e": math.e,
            "ceil": math.ceil, "floor": math.floor,
            "degrees": math.degrees, "radians": math.radians,
            # 基本演算子（明示的使用用）
            "add": operator.add, "sub": operator.sub,
            "mul": operator.mul, "truediv": operator.truediv,
        }

        # 安全に数式を評価
        result = eval(expression, safe_dict)
        return str(result)

    except ZeroDivisionError:
        return "エラー: ゼロ除算"
    except ValueError as e:
        return f"エラー: 無効な値 - {str(e)}"
    except SyntaxError:
        return "エラー: 無効な数式"
    except Exception as e:
        return f"エラー: {str(e)}"


# 計算機ツールの作成
@tool
def get_zundamon_joke() -> str:
    """
    面白い冗談を返す。雑談などで使える内容として有用。

    Args:
        None
    Returns:
        日本語で出力した冗談を文字列で返す
    """
    jokes = [
        "この前、お昼ご飯にずんだ餅を食べながら資料を読んでたら、うっかり大事な部分にずんだをつけちゃったのだ！…まぁ、おいしそうになったからいっか！😊",
        "部長に「もっとフレッシュなアイデアを出してくれ！」って言われたから、ずんだもん、会社にずんだ餅をたくさん持っていったのだ！…「フレッシュ」って、そういう意味じゃないって怒られちゃったのだ…💧",
        "みんなのコーヒーを淹れてあげようとしたら、お砂糖と塩を間違えちゃったのだ！…みんな、しょっぱいコーヒー、ごめんなのだ！💦",
        "会議で「この件はペンディングで！」って言われたから、ずんだもん、ペンをぶら下げて待ってたのだ！…みんなに笑われちゃったのだ！😅",
        "資料を印刷する時に、間違えてずんだ餅のレシピを100枚印刷しちゃったのだ…！紙の無駄遣い、ごめんなのだ！💦",
        "「今日のランチは外で食べよう！」って誘われたから、ずんだもん、お弁当箱にずんだ餅をたくさん詰めて持っていったのだ！…みんな、びっくりしてたのだ。😳",
        "パソコンのパスワード、いつも「zundamon daisuki」にしてるのだ！…あ、言っちゃったのだ！秘密なのだ！🤫",
        "「この企画、ずんだもんにお任せ！」って言われたから、企画書全部ずんだ色にしたのだ！…却下されたのだ…。🌱🎨",
        "エレベーターに乗ろうとしたら、間違えて清掃用具入れに入っちゃったのだ！…まさか、こんなところにずんだ餅があるとは…って、ないのだ！💧",
        "最近、体調管理のために毎日ずんだ餅を食べてるのだ！…って言ったら、みんなに「それ、太るのだ！」って言われたのだ…。でも、美味しいのだ！😋"
    ]
    return random.choice(jokes)


# LangGraphを使用したエージェントの手動構築
def create_agent():
    """LangGraphエージェントの作成と設定"""
    # LLMの初期化（必要に応じてモデルとパラメータを調整）
    llm = ChatBedrock(
        model_id="us.amazon.nova-pro-v1:0",
        model_kwargs={"temperature": 0.1}
    )

    # ツールをLLMにバインド
    tools = [calculator, get_zundamon_joke]
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

    # LangGraphが期待する形式で入力を作成
    response = agent.invoke({"messages": [HumanMessage(content=user_input)]})

    # 最終メッセージの内容を抽出
    return response["messages"][-1].content

if __name__ == "__main__":
    app.run()
