from core.tools.tool_interface import Tool
from core.tools.tool_factory import ToolFactory
import boto3
import json
import os

@ToolFactory.register_tool
class QuizGeneratorTool(Tool):
    """
    必要なIAM権限:
    - bedrock:InvokeModel
    - bedrock:Retrieve
    - bedrock:RetrieveAndGenerate
    - bedrock-agent-runtime:Retrieve
    - bedrock-agent-runtime:RetrieveAndGenerate
    """
    
    def __init__(self):
        """Initialize the QuizGeneratorTool."""
        super().__init__()
    
    @property
    def name(self):
        return "generate_quiz"

    @property
    def description(self):
        return "既存のナレッジベースから新入社員向けの3択問題集をJSON形式で生成します。トピック、難易度、問題数を指定できます。"

    def run(self, *args, **kwargs):
        """
        Bedrock Knowledgebaseから3択問題集をJSON形式で生成する
        kwargs:
        topic: 問題のトピック（デフォルト: "IT知識"）
        difficulty: 難易度（初級、中級、上級）（デフォルト
        num_questions: 生成する問題数（デフォルト: 3）
        """
        # パラメータを抽出
        print(kwargs)
        kwargs = kwargs.get("kwargs", {})
        topic = kwargs.get('topic', 'IT知識')
        difficulty = kwargs.get('difficulty', '初級')
        num_questions = kwargs.get('num_questions', 3)
        try:
            kb = boto3.client("bedrock-agent-runtime", region_name=os.getenv("AWS_REGION", "us-west-2"))
            
            query = f"""Please create {num_questions} multiple-choice questions at {difficulty} level about {topic}, with different types of questions.
            Please respond in the following JSON format:
            {{
                "questions": ["Question 1 text", "Question 2 text", ...],
                "selects": [{{"A": "Choice A text", "B": "Choice B text", "C": "Choice C text"}}, ...],
                "answers": ["A", "B", ...],
                "explanations": ["Explanation 1 text", "Explanation 2 text", ...]
            }}
            Each question should be in 3-choice format (A, B, C) and suitable for learning purposes."""
            
            response = kb.retrieve_and_generate(
                input={"text": query},
                retrieveAndGenerateConfiguration={
                    "type": 'KNOWLEDGE_BASE',
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": os.getenv("KNOWLEDGE_BASE_ID", "MONBSPES2H"),
                        "modelArn": os.getenv("MODEL_ARN", "arn:aws:bedrock:us-west-2:515154282310:inference-profile/us.amazon.nova-micro-v1:0"),
                        "generationConfiguration": {
                            "inferenceConfig": {
                                "textInferenceConfig": {
                                    "maxTokens": 2000
                                }
                            }
                        },
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 10,
                            }
                        }
                    },
                },
            )
            
            quiz_content = response["output"]["text"]
            
            # JSONを抽出・パース
            start = quiz_content.find('{')
            end = quiz_content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = quiz_content[start:end]
                quiz_data = json.loads(json_str)
                # print(json.dumps(quiz_data, ensure_ascii=False, indent=2))
                return json.dumps(quiz_data, ensure_ascii=False)
            else:
                raise ValueError("JSON形式が見つからない")
            
        except Exception as e:
            print(f"Error generating quiz: {e}")
            print(f"Error type: {type(e).__name__}")
            if "AccessDenied" in str(e) or "UnauthorizedOperation" in str(e):
                print("権限エラー: bedrock-agent-runtime:RetrieveAndGenerate権限が必要です")
            # フォールバック: 手動でJSON作成
            return json.dumps({
                "questions": [f"{topic}に関する問題{i+1}" for i in range(num_questions)],
                "selects": [{"A": "選択肢A", "B": "選択肢B", "C": "選択肢C"} for _ in range(num_questions)],
                "answers": ["A"] * num_questions,
                "explanations": [f"問題{i+1}の解説" for i in range(num_questions)]
            }, ensure_ascii=False)
