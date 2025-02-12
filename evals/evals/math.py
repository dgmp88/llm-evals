from typing import cast

import numpy as np

from evals.core import Assistant, Eval, User, batch_eval
from evals.types import Model

SYSTEM_PROMPT = """Answer the math problem with the numeric result only. Round to two decimal places if necessary. Do not add newlines, commas, or any other characters.

Examples: 

User: 1 + 1 
Assistant: 2
----
User: 234/2
Assistant: 117
----
User: 10/2- 5
Assistant: 0
----
User: 823 * 377 
Assistant: 310271
----
User: 1/3
Assistant: 0.33"""


class MathAssistant(Assistant):
    def __init__(self, model: Model):
        super().__init__(model=model, system_prompt=SYSTEM_PROMPT)

    def is_done(self):
        return True


class MathUser(User):
    def __init__(self, rng: np.random.Generator, low: int, high: int):
        super().__init__()
        self.low = low
        self.high = high

        x, y = rng.integers(low=self.low, high=self.high, size=2)
        operation = rng.choice(["+", "-", "*", "/"])
        self.problem = f"{x} {operation} {y}"

    def respond(self, chat_history):
        return self.problem

    def is_done(self):
        return False


class MathEval(Eval):
    name = "math_eval"

    def __init__(self, model: Model, rng_seed: int):
        self.assistant = MathAssistant(model=model)
        self.user = MathUser(rng=self.rng, low=100, high=1000)

    def evaluate(self):
        user = cast(MathUser, self.user)
        gt: float = eval(user.problem)
        gt = round(gt, 2)  # round to 2 decimal places as in the system prompt

        response = self.chat_history[-1].content
        pred: float | None = None
        try:
            pred = float(response)
        except ValueError:
            pass

        correct = pred == gt
        if not correct:
            print(f"{user.problem} - wrong with: {pred} (gt: {gt})")
        return correct


def math(model: Model, num_problems: int = 50):
    """random numbers under 10, addition, subtraction, multiplication, division"""

    def eval_factory(seed: int):
        return MathEval(
            model=model,
            rng_seed=seed,
        )

    batch_eval(num_problems, eval_factory)


if __name__ == "__main__":
    import fire

    fire.Fire(math)
