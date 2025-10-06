# AgentCore Runtime デプロイメント用ライブラリのインポート
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

# boto3セッションから現在のAWSリージョンを取得
boto_session = Session()
region = boto_session.region_name

# AgentCore Runtime インスタンスの初期化
agentcore_runtime = Runtime()

# エージェントデプロイメント設定の構成
agent_name = "senpai_main_agent"
response = agentcore_runtime.configure(
    entrypoint="senpai-main-agent.py",        # メインエージェントエントリーポイントファイル
    auto_create_execution_role=True,          # IAM実行ロールの自動作成
    auto_create_ecr=True,                     # ECRリポジトリの自動作成
    requirements_file="requirements.txt",     # Python依存関係ファイル
    region=region,                            # デプロイメント用AWSリージョン
    agent_name=agent_name                     # エージェント名識別子
)
print(response)

# エージェントをAgentCore Runtimeにデプロイ・起動
launch_result = agentcore_runtime.launch()
