from abc import ABC, abstractmethod
from typing import Callable

import numpy as np
from tqdm import tqdm

from llm_evals.db import EvalResult
from llm_evals.llm import completion
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
        np.random.seed(0)
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
