import boto3
import json
import os
from dotenv import load_dotenv

# 環境変数を読み込み（プロジェクトルートの.envファイルから）
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# agent_arn = launch_result.agent_arn
agentcore_client = boto3.client(
    'bedrock-agentcore',
    region_name=os.getenv('AWS_REGION')
)

boto3_response = agentcore_client.invoke_agent_runtime(
    agentRuntimeArn=os.getenv('AGENT_RUNTIME_ARN'),
    runtimeSessionId=os.getenv('RUNTIME_SESSION_ID'),
    qualifier=os.getenv('QUALIFIER', 'DEFAULT'),
    payload=json.dumps({"prompt": "こんにちは。あなたは誰ですか？"})
)

if "text/event-stream" in boto3_response.get("contentType", ""):
    content = []
    for line in boto3_response["response"].iter_lines(chunk_size=1):
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                line = line[6:]
                print(line)
                content.append(line)
    print(content)
else:
    try:
        events = []
        for event in boto3_response.get("response", []):
            events.append(event.decode('unicode_escape').encode('latin1').decode('utf-8'))
    except Exception as e:
        events = [f"Error reading EventStream: {e}"]
    print(events)