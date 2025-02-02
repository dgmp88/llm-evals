from pydantic import BaseModel
from typing import Literal


Model = Literal[
    # https://docs.litellm.ai/docs/providers
    # OpenAI
    "gpt-4o-2024-08-06",
    "gpt-4o-2024-11-20",
    "gpt-4o-mini-2024-07-18",
    "o1-mini",
    "o1-preview",
    # Anthropic
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    # Google
    "gemini/gemini-1.5-flash",
    "gemini/gemini-1.5-pro",
    "gemini/gemini-2.0-flash-exp",
    # Ollama
    "ollama/llama3.1:8b",
    # Together
    "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "together_ai/meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
]


class Message(BaseModel):
    content: str
    role: Literal["user", "system", "assistant"]

