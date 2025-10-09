# AgentCore Runtime デプロイメント用ライブラリのインポート
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import os
import sys
from dotenv import load_dotenv

# プロジェクトルートを追加（エージェントスクリプトにアクセスするため）
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 環境変数を読み込み
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# boto3セッションから現在のAWSリージョンを取得（環境変数で上書き可能）
boto_session = Session()
region = os.getenv('AWS_REGION', boto_session.region_name)

# AgentCore Runtime インスタンスの初期化
agentcore_runtime = Runtime()

# エージェントデプロイメント設定の構成
agent_name = os.getenv('AGENT_NAME')

# senpai-main-agentディレクトリに移動してデプロイ
agent_dir = os.path.join(os.path.dirname(__file__), '..', os.getenv('AGENT_ENDPOINT_NAME'))
os.chdir(agent_dir)

# Check if custom Dockerfile exists to prevent regeneration
custom_dockerfile_exists = os.path.exists('Dockerfile')

if not custom_dockerfile_exists:
    # copy ../core folder to current folder and remove after configure
    import shutil
    shutil.copytree(os.path.join(os.path.dirname(__file__), '..', 'core'), 'core')

    response = agentcore_runtime.configure(
        entrypoint=os.getenv('AGENT_ENDPOINT_NAME') + ".py",        # メインエージェントエントリーポイントファイル
        auto_create_execution_role=True,                            # IAM実行ロールの自動作成
        auto_create_ecr=True,                                       # ECRリポジトリの自動作成
        requirements_file="requirements.txt",                       # Python依存関係ファイル
        region=region,                                              # デプロイメント用AWSリージョン
        agent_name=agent_name,                                      # エージェント名識別子
    )

    shutil.rmtree('core') # remove copied core folder
print(response)
    
# エージェントをAgentCore Runtimeにデプロイ・起動
launch_result = agentcore_runtime.launch(auto_update_on_conflict=True)