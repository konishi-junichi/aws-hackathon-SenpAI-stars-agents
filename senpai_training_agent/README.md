# SenpAI Training Agent

新卒社員向けの問題集生成AIエージェントです。Amazon Bedrock Knowledge Baseから3択問題をJSON形式で生成します。

## 🎯 主な機能
1. **問題集生成** (`generate_quiz`): Knowledge Baseから新入社員向けの3択問題をJSON形式で自動生成
2. **パラメータ指定**: トピック、難易度、問題数を指定可能
3. **JSON出力**: 構造化されたデータ形式での問題提供

## ⚙️ 技術仕様
- **モデル**: Amazon Nova Micro (`us.amazon.nova-micro-v1:0`)
- **フレームワーク**: LangGraph + Amazon Bedrock
- **ランタイム**: Amazon Bedrock AgentCore Runtime
- **Knowledge Base**: Bedrock Knowledge Base連携

## 📁 ファイル構成

```
senpai_training_agent/
├── senpai_training_agent.py    # メインエージェントスクリプト
├── deploy.py                   # デプロイスクリプト
├── requirements.txt            # Python依存関係
└── README.md                  # このファイル
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

### 入力パラメータ
- `topic`: 問題のトピック（デフォルト: "IT知識"）
- `difficulty`: 難易度（初級、中級、上級）（デフォルト: "初級"）
- `num_questions`: 生成する問題数（デフォルト: 3）

### 出力形式
```json
{
  "questions": ["問題文1", "問題文2", "問題文3"],
  "selects": [
    {"A": "選択肢A", "B": "選択肢B", "C": "選択肢C"},
    {"A": "選択肢A", "B": "選択肢B", "C": "選択肢C"},
    {"A": "選択肢A", "B": "選択肢B", "C": "選択肢C"}
  ],
  "answers": ["A", "B", "C"],
  "explanations": ["解説1", "解説2", "解説3"]
}
```

## 🎯 目的

新卒社員の学習をサポートするため、Knowledge Baseから構造化された問題集を自動生成し、効率的な学習体験を提供します。

## 🔧 環境変数
- `AWS_REGION`: AWSリージョン（デフォルト: us-west-2）
- `KNOWLEDGE_BASE_ID`: Bedrock Knowledge BaseのID
- `MODEL_ARN`: 使用するモデルのARN
- `AWS_MEMORY_ID`: メモリ保存用のID