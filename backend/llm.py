import os
import json
from openai import OpenAI
from typing import List, Dict, Any

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


class AgentLogger:
    def __init__(self):
        self.logs = []
    
    def log_thought(self, thought: str):
        self.logs.append({"type": "thought", "content": thought})
    
    def log_action(self, action: str, details: str = ""):
        self.logs.append({"type": "action", "content": action, "details": details})
    
    def log_observation(self, observation: str):
        self.logs.append({"type": "observation", "content": observation})
    
    def get_logs(self) -> List[Dict[str, str]]:
        return self.logs


def call_openai(messages: List[Dict[str, str]], response_format: str = "text", model: str = "gpt-5") -> str:
    try:
        if response_format == "json":
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
        else:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI API call failed: {str(e)}")


def call_openai_json(messages: List[Dict[str, str]], model: str = "gpt-5") -> Dict[str, Any]:
    try:
        result = call_openai(messages, response_format="json", model=model)
        return json.loads(result)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response: {str(e)}")
    except Exception as e:
        raise e
