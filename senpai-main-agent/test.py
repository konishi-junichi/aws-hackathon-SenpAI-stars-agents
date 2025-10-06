import boto3
import json

# agent_arn = launch_result.agent_arn
agentcore_client = boto3.client(
    'bedrock-agentcore',
    region_name='us-east-1'
)

boto3_response = agentcore_client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:YOUR_ACCOUNT_ID:runtime/YOUR_AGENT_RUNTIME_ID',
    runtimeSessionId='test-session-123',
    qualifier="DEFAULT",
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
