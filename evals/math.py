from typing import cast

import numpy as np

from evals.core import Eval, LLMPlayer, OpponentPlayer, batch_eval
from evals.registry import register_eval
from evals.types import Message

SYSTEM_PROMPT = """Answer the math problem with the numeric result only. Round to two decimal places if necessary. Do not include newlines, commas, or any other characters in your response."""

# Convert to  list of messages
MESSAGES: list[Message] = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "1 + 1"},
    {"role": "assistant", "content": "2"},
    {"role": "user", "content": "234/2"},
    {"role": "assistant", "content": "117"},
    {"role": "user", "content": "10/2 - 5"},
    {"role": "assistant", "content": "0"},
    {"role": "user", "content": "823 * 377"},
    {"role": "assistant", "content": "310271"},
    {"role": "user", "content": "1/3"},
    {"role": "assistant", "content": "0.33"},
]


class MathAssistant(LLMPlayer):
    def __init__(self, model: str):
        super().__init__(model=model, messages=MESSAGES)

    def is_done(self):
        return True


class MathUser(OpponentPlayer):
    def __init__(self, rng: np.random.Generator, low: int = 100, high: int = 1000):
        super().__init__()
        self.low = low
        self.high = high

        x, y = rng.integers(low=self.low, high=self.high, size=2)
        operation = rng.choice(["+", "-", "*", "/"])
        self.problem = f"{x} {operation} {y}"

    def make_move(self, chat_history):
        return self.problem

    def is_done(self):
        return False


class MathEval(Eval):
    name = "math_eval"

    def __init__(self, model: str, rng_seed: int, low: int = 100, high: int = 1000):
        super().__init__(rng_seed=rng_seed)
        self.assistant = MathAssistant(model=model)
        self.user = MathUser(rng=self.rng, low=low, high=high)

    def evaluate(self) -> float:
        user = cast(MathUser, self.user)
        gt: float = eval(user.problem)
        gt = round(gt, 2)  # round to 2 decimal places as in the system prompt

        response = self.chat_history[-1]["content"]
        pred: float | None = None
        try:
            pred = float(response.strip())
            pred = round(pred, 2)  # round to match expected precision
        except ValueError:
            # Keep pred as None if parsing fails
            pass

        correct = pred == gt
        if not correct:
            print(f"{user.problem} - wrong with: {pred} (gt: {gt})")
        return float(correct)


def math(model: str, num_problems: int = 50):
    """random numbers under 10, addition, subtraction, multiplication, division"""

    def eval_factory(seed: int):
        return MathEval(
            model=model,
            rng_seed=seed,
        )

    batch_eval(num_problems, eval_factory)


# Register the evaluation
register_eval(
    name="math",
    factory=MathEval,
    description="Basic arithmetic problems with random integers",
    default_runs=50,
    low=100,
    high=1000,
)


if __name__ == "__main__":
    import fire

    fire.Fire(math)
