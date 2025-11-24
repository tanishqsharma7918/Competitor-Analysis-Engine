import os
import asyncio
from typing import Dict, List, Any
from openai import OpenAI

# Load API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Sync OpenAI Client (we will wrap in async)
client = OpenAI(api_key=OPENAI_API_KEY)


# --------------------------------------------------------
# LOW-LEVEL RAW COMPLETION CALL (SYNC)
# --------------------------------------------------------
def call_openai(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
    """
    Standard OpenAI chat completion. Returns string output.
    By default uses gpt-4o-mini for FAST performance.
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=3000
    )
    return response.choices[0].message.content


# --------------------------------------------------------
# SYNC — JSON RETURNING VERSION
# --------------------------------------------------------
def call_openai_json(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Returns JSON output. MUCH safer for structured tasks.
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=4000,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content  # Already a JSON string


# --------------------------------------------------------
# ASYNC WRAPPERS — Thread Offloading
# --------------------------------------------------------
async def call_openai_async(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
    """Async version of call_openai using thread offloading."""
    return await asyncio.to_thread(call_openai, messages, model)


async def call_openai_json_async(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Async version of call_openai_json using thread offloading."""
    return await asyncio.to_thread(call_openai_json, messages, model)


# --------------------------------------------------------
# LOGGER CLASS (REQUIRED BY YOUR APP)
# --------------------------------------------------------
class AgentLogger:
    def __init__(self):
        self.logs = []

    def log_thought(self, text: str):
        self.logs.append(f"🧠 THOUGHT: {text}")

    def log_action(self, text: str):
        self.logs.append(f"⚡ ACTION: {text}")

    def log_observation(self, text: str):
        self.logs.append(f"👀 OBSERVATION: {text}")

    def get_logs(self):
        return self.logs
