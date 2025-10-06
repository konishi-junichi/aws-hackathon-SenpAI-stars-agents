# SenpAI Main Agent

新卒社員の研修をサポートするAIエージェント「ずんだもん」です。

## 🌸 キャラクター設定
- **ペルソナ**: ずんだもん（新卒研修担当の先輩AI）
- **口調**: 明るく親しみやすい「〜なのだ」口調
- **性格**: ちょっとおっちょこちょいだけど、頼れる先輩として精一杯サポート

## 🎯 主な機能
1. **計算機能** (`calculator`): 数学的な計算や業務データ処理をサポート
2. **ジョーク機能** (`get_zundamon_joke`): 疲れた時や元気がない時に面白い冗談で笑顔に

## 🗣️ コミュニケーション特徴
- 絵文字を多用した親しみやすい表現（🌱✨😊💡💧）
- 新卒社員の質問に丁寧かつ分かりやすく回答
- 失敗に寛容で、励ましとアドバイスを提供
- 積極的な声かけとサポート

## ⚙️ 技術仕様
- **モデル**: Amazon Nova Pro (`us.amazon.nova-pro-v1:0`)
- **フレームワーク**: LangGraph + Amazon Bedrock
- **ランタイム**: Amazon Bedrock AgentCore Runtime

## 📁 ファイル構成

```
senpai-main-agent/
├── senpai-main-agent.py    # メインエージェントスクリプト
├── deploy.py               # デプロイスクリプト
├── requirements.txt        # Python依存関係
└── README.md              # このファイル
```

## 🚀 セットアップ・デプロイ方法

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. エージェントのデプロイ
```bash
python deploy.py
```

## 💬 使用例

### AgentCore Runtime経由での呼び出し
```python
import boto3
import json

client = boto3.client('bedrock-agentcore')
response = client.invoke_agent_runtime(
    agentRuntimeArn='<AGENT_ARN>',
    qualifier='DEFAULT',
    payload=json.dumps({"prompt": "2+2の計算をお願いします"})
)
```

### 質問例
- 「2+2の計算をお願いします」
- 「疲れたので何か面白い話をしてください」
- 「新人研修で気をつけることを教えてください」
- 「sqrt(16) + 3 * 4を計算してください」

## 🎯 目的

新卒社員が「仕事って楽しいのだ！」と思えるよう、業務面と精神面の両方をサポートする教育特化型エージェントです。