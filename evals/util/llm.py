from typing import List

from openai import OpenAI

from evals.types import Message
from evals.util.env import ENV

DEFAULT_TEMPERATURE = 0.001  # 0 breaks some providers, so just set it super low
DEFAULT_MAX_TOKENS = 10


# Initialize OpenAI client with OpenRouter
def get_client() -> OpenAI:
    """Get OpenAI client configured for OpenRouter."""
    api_key = ENV.OPENROUTER_API_KEY
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def completion(model: str, messages: List[Message]) -> str:
    """Get a single completion from the model."""
    client = get_client()
    # type: ignore
    response = client.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
    )

    if response.choices and response.choices[0].message.content:
        return response.choices[0].message.content

    return ""


def batch_completion(model: str, messages: List[List[Message]]) -> List[str]:
    """Get multiple completions from the model."""
    results = []
    for message_list in messages:
        try:
            result = completion(model, message_list)
            results.append(result)
        except Exception as e:
            print(f"Error in batch completion: {e}")
            results.append("")

    return results


def test_llm(model: str):
    """Test the LLM with a simple message."""
    result = completion(model, [Message(content="hello", role="user")])
    print(result)


if __name__ == "__main__":
    import fire

    fire.Fire(
        {
            "test_llm": test_llm,
        }
    )
