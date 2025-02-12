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

    def pre_respond(self, chat_history: list[Message]):
        # Overloadable hook
        pass

    def post_respond(self, chat_history: list[Message], response: str):
        # Overloadable hook
        pass

    def respond(self, chat_history: list[Message]):
        self.pre_respond(chat_history)
        ch = [self.system_message] + chat_history
        response = completion(self.model, ch)
        self.post_respond(chat_history, response)
        return response


class User(Agent):
    role = "user"


class Eval(ABC):
    name: str

    def __init__(
        self,
        assistant: Assistant,
        user: User,
        max_turns: int = 10,
    ):
        self.assistant = assistant
        self.user = user
        self.max_turns = max_turns
        self.chat_history: list[Message] = []

    def run(self):
        # User always goes first for compatibility with Gemini, Claude etc.
        current = self.user

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

    def print_chat(self):
        for message in self.chat_history:
            print(f"{message.role}: {message.content}")


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
        model_name=eval.assistant.model,
        eval_name=eval.name,
        result=np.mean(results),
    ).save()
