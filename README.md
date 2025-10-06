# AWS Hackathon SenpAI Stars Agents
Amazon Bedrock AgentCore RuntimeとLangGraphを使用したAIエージェントのサンプル実装です。

## 概要
このプロジェクトは以下の技術を使用してAIエージェントをAgentCore Runtime上でホストします：
- **Amazon Bedrock AgentCore Runtime**: エージェントのランタイム環境
- **LangGraph**: エージェントのワークフロー管理
- **Amazon Nova Pro**: Amazon Bedrockの言語モデル
- **Docker**: コンテナ化とデプロイメント

## ファイル構成
```
.
├── senpai-main-agent/        # メインエージェント
│   ├── senpai-main-agent.py  # エージェントスクリプト
│   ├── deploy.py             # デプロイスクリプト
│   ├── requirements.txt      # Python依存関係
│   └── README.md             # エージェント説明
├── requirements.txt          # 共通Python依存関係
└── README.md                 # このファイル
```

**注意**: Dockerfileは各エージェントのdeploy.pyを実行することで自動生成されます。

## 前提条件
- Python 3.12（推奨）
- AWS CLI インストール済み
- Docker インストール済み
- 適切なIAMロール権限（Bedrock、ECR、AgentCore Runtime）

### AWS設定

AWS CLIの設定を行います：

```bash
aws configure
```

以下の情報を入力してください：
- **AWS Access Key ID**: あなたのアクセスキーID
- **AWS Secret Access Key**: あなたのシークレットアクセスキー
- **Default region name**: `us-east-1`
- **Default output format**: `json`

## セットアップ・実行方法

### 1. Python環境のセットアップ

```bash
python3.12 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. エージェントのデプロイ

各エージェントディレクトリで個別にデプロイします：

```bash
cd agents/senpai-main-agent
python deploy.py
```

### 4. テスト

デプロイ後、テストスクリプトを実行してエージェントの動作を確認：

```bash
python test.py
```

## 利用可能なエージェント

### SenpAI Main Agent
- **機能**: 新卒社員研修サポート、計算機能、ジョーク機能
- **キャラクター**: ずんだもん（親しみやすい先輩AI）
- **場所**: `agents/senpai-main-agent/`

## 設定

- **モデル**: Amazon Nova Pro (`us.amazon.nova-pro-v1:0`)
- **ポート**: 8080（AgentCore Runtime）
- **ランタイム**: Python 3.12（推奨）

## 必要なIAM権限

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock-agentcore:*",
        "ecr:*",
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
```
