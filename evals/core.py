from abc import ABC, abstractmethod
from typing import Callable

import numpy as np
from tqdm import tqdm

from evals.types import Message, Model, Role
from evals.util.db import EvalResult
from evals.util.llm import completion


class Agent(ABC):
    role: Role

    @abstractmethod
    def respond(self, chat_history: list[Message]) -> str:
        pass

    @abstractmethod
    def is_done(self) -> bool:
        pass


class Assistant(Agent):
    role = "assistant"

    def __init__(self, model: Model, system_prompt: str):
        super().__init__()
        self.model: Model = model
        self.system_message = Message(role="system", content=system_prompt)

    def respond(self, chat_history: list[Message]):
        ch = [self.system_message] + chat_history
        response = completion(self.model, ch)
        return response


class User(Agent):
    role = "user"


class Eval(ABC):
    name: str

    def __init__(
        self,
        model: Model,
        assistant: Assistant,
        user: User,
        user_first: bool,
        max_turns: int = 10,
    ):
        self.model: Model = model
        self.assistant = assistant
        self.user = user
        self.user_first = user_first
        self.max_turns = max_turns
        self.chat_history: list[Message] = []

    def run(self):
        current = self.user if self.user_first else self.assistant

        response: None | str = None

        for i in range(self.max_turns):
            response = current.respond(self.chat_history)
            self.chat_history.append(Message(role=current.role, content=response))
            if current.is_done():
                break
            current = self.assistant if current == self.user else self.user

        return self.evaluate()

    @abstractmethod
    def evaluate(self) -> float:
        pass


def batch_eval(num_runs: int, eval_factory: Callable[[], Eval]):
    np.random.seed(0)
    results: list[float] = []
    eval: Eval | None = None
    for _ in tqdm(range(num_runs)):
        eval = eval_factory()
        score = eval.run()
        results.append(score)

    if not eval:
        raise ValueError("No evaluations run")

    EvalResult(
        model_name=eval.model,
        eval_name=eval.name,
        result=np.mean(results),
    ).save()
