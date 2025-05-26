import dotenv
from litellm import batch_completion as lite_batch_completion
from litellm import completion as lite_completion  # type: ignore

from evals.types import Message, Model

dotenv.load_dotenv()

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
        n=1,
    )
    return [str(response.choices[0].message.content) for response in responses]


def test_llm(model: str):
    result = completion(model, [Message(content="hello", role="user")])
    print(result)


if __name__ == "__main__":
    import fire

    fire.Fire(
        {
            "test_llm": test_llm,
        }
    )
