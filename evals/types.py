from typing import Literal

from pydantic import BaseModel

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
    ## Llama
    "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "together_ai/meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    "togther_ai/meta-llama/Llama-3.2-3B-Instruct-Turbo",
    ## Deepseek
    "together_ai/deepseek-ai/DeepSeek-V3",
    ## Qwen
    "together_ai/Qwen/Qwen2.5-7B-Instruct-Turbo"
    "together_ai/Qwen/Qwen2.5-72B-Instruct-Turbo",
    ## Google
    "together_ai/google/gemma-2-9b-it",
    "together_ai/google/gemma-2-27b-it",
    ## Mistral
    "together_ai/mistralai/Mistral-Small-24B-Instruct-2501",
]


class Message(BaseModel):
    content: str
    role: Literal["user", "system", "assistant"]
