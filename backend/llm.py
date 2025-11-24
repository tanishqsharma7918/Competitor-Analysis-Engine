import os
import json
import asyncio
from typing import Dict, List, Any
from openai import OpenAI

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


# --------------------------------------------------------
# RAW COMPLETION (STRING OUTPUT)
# --------------------------------------------------------
def call_openai(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
    """
    Standard chat completion returning pure text.
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=3000
    )
    return response.choices[0].message.content


# --------------------------------------------------------
# JSON COMPLETION (RETURNS PYTHON DICT)
# --------------------------------------------------------
def call_openai_json(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Returns JSON output parsed into a Python dict.
    Fixes: strings → dict to avoid .get() errors.
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=4000,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content  # string
    try:
        data = json.loads(raw)                 # parse into dict
        return data
    except json.JSONDecodeError:
        raise ValueError(f"OpenAI returned invalid JSON:\n\n{raw}")


# --------------------------------------------------------
# ASYNC VERSIONS (SAFE VIA THREAD OFFLOADING)
# --------------------------------------------------------
async def call_openai_async(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
    """Async version of call_openai using threads."""
    return await asyncio.to_thread(call_openai, messages, model)


async def call_openai_json_async(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Async version of call_openai_json using threads."""
    return await asyncio.to_thread(call_openai_json, messages, model)


# --------------------------------------------------------
# LOGGER CLASS (STRUCTURED LOGS FOR UI)
# --------------------------------------------------------
class AgentLogger:
    """
    Stores structured logs compatible with helpers.format_log_entry().
    """
    def __init__(self):
        self.logs = []

    def log_thought(self, text: str):
        self.logs.append({"type": "thought", "content": text})

    def log_action(self, text: str):
        self.logs.append({"type": "action", "content": text})

    def log_observation(self, text: str):
        self.logs.append({"type": "observation", "content": text})

    def get_logs(self):
        return self.logs
