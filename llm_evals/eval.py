from abc import ABC, abstractmethod
from typing import Callable

import numpy as np
from tqdm import tqdm

from llm_evals.db import EvalResult
from llm_evals.llm import completion
from llm_evals.system_prompt import SYSTEM_PROMPT
from llm_evals.types import Message, Model


class Agent(ABC):
    def __init__(self):
        self.chat_history: list[Message] = []

    @abstractmethod
    def respond(self, message: str | None = None) -> str:
        pass


class Assistant(Agent):
    def __init__(self, model: Model, system_prompt: str):
        super().__init__()
        self.model: Model = model
        self.chat_history.append(Message(role="system", content=system_prompt))

    def respond(self, message=None):
        if message is None:
            raise ValueError("message is None")
        self.chat_history.append(Message(role="user", content=message))
        response = completion(self.model, self.chat_history)
        self.chat_history.append(Message(role="assistant", content=response))
        return response


class User(Agent):
    @abstractmethod
    def evaluate(self, response: str) -> bool:
        pass


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


SEED = 0


class EvalRunner(ABC):
    def __init__(
        self,
        name: str,
        model: Model,
        assistant_factory: Callable[[Model], Assistant],
        user_factory: Callable[[Model], User],
    ):
        self.name = name
        self.model: Model = model
        self.assistant_factory = assistant_factory
        self.user_factory = user_factory

    def run(self, iterations: int = 50):
        np.random.seed(SEED)
        results = []
        for i in tqdm(range(0, iterations)):
            assistant = self.assistant_factory(self.model)
            user = self.user_factory(self.model)
            user_response = user.respond()
            assistant_response = assistant.respond(user_response)
            result = user.evaluate(assistant_response)
            results.append(result)

        percent_correct = sum(results) / iterations

        result = EvalResult(
            model_name=self.model, eval_name=self.name, result=percent_correct
        )
        result.save()


def math(model: Model, low=100, high=1000, num_problems: int = 50):
    """random numbers under 10, addition, subtraction, multiplication, division"""
    assistant_factory = lambda model: MathAssistant(model=model)
    user_factory = lambda model: MathUser(low=low, high=high)
    runner = EvalRunner(
        name="math_easy",
        model=model,
        assistant_factory=assistant_factory,
        user_factory=user_factory,
    )
    runner.run(iterations=num_problems)


if __name__ == "__main__":
    import fire

    fire.Fire({"math": math})
