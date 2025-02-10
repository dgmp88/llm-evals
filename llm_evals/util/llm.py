from litellm import batch_completion as lite_batch_completion
from litellm import completion as lite_completion  # type: ignore

from llm_evals.types import Message, Model

DEFAULT_TEMPERATURE = 0.001  # 0 breaks some providers, so just set it super low
DEFAULT_MAX_TOKENS = 10


def completion(model: Model, messages: list[Message]) -> str:
    response = lite_completion(
        model=model,
        messages=messages,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
    )
    message = response.choices[0].message.content  # type: ignore

    return str(message)


def batch_completion(model: Model, messages: list[list[Message]]) -> list[str]:
    responses = lite_batch_completion(
        model=model,
        messages=messages,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
        num_retries=2,
    )
    return [str(response.choices[0].message.content) for response in responses]


if __name__ == "__main__":
    result = completion("gpt-4o-2024-08-06", [Message(content="hello", role="user")])
    print(result)
