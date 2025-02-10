import numpy as np

from evals.core import Assistant, EvalRunner, User
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


class MathUser(User):
    def __init__(self, low: int, high: int):
        super().__init__()
        self.low = low
        self.high = high

        x, y = np.random.randint(low=self.low, high=self.high, size=2)
        operation = np.random.choice(["+", "-", "*", "/"])
        self.problem = f"{x} {operation} {y}"

    def respond(self, message=None):
        return self.problem

    def evaluate(self, response: str) -> bool:
        self.gt: float = eval(self.problem)
        self.gt = round(self.gt, 2)  # round to 2 decimal places as in the system prompt

        pred: float | None = None
        try:
            pred = float(response)
        except ValueError:
            pass

        correct = pred == self.gt
        if not correct:
            print(f"{self.problem} - wrong with: {pred} (gt: {self.gt})")
        return correct


def math(model: Model, low=100, high=1000, num_problems: int = 50):
    """random numbers under 10, addition, subtraction, multiplication, division"""
    runner = EvalRunner(
        name="math_easy",
        model=model,
        assistant_factory=lambda model: MathAssistant(model=model),
        user_factory=lambda _model: MathUser(low=low, high=high),
    )
    runner.run(iterations=num_problems)


if __name__ == "__main__":
    import fire

    fire.Fire({"math": math})
