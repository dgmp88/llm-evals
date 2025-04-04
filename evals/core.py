import time
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


TIMES = []


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
        t1 = time.time()
        response = completion(self.model, ch)
        print(f"Time taken: {time.time() - t1:.2f}s")
        TIMES.append(time.time() - t1)
        print(f"avg time: {np.mean(TIMES)}, max time: {np.max(TIMES)}")
        self.post_respond(chat_history, response)
        return response


class User(Agent):
    role = "user"


class Eval(ABC):
    name: str
    assistant: Assistant
    user: User
    max_turns: int = 10

    def __init__(
        self,
        rng_seed: int,
    ):
        self.rng = np.random.default_rng(seed=rng_seed)
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

        score = self.evaluate()
        self.print_chat()
        return score

    @abstractmethod
    def evaluate(self) -> float:
        pass

    def print_chat(self):
        for message in self.chat_history:
            print(f"{message['role']}: {message['content']}")


def batch_eval(num_runs: int, eval_factory: Callable[[int], Eval]):
    results: list[float] = []
    eval: Eval | None = None
    for i in tqdm(range(num_runs)):
        eval = eval_factory(i)
        print(eval.name)
        score = eval.run()
        results.append(score)

    if not eval:
        raise ValueError("No evaluations run")

    EvalResult(
        model_name=eval.assistant.model,
        eval_name=eval.name,
        result=np.mean(results),
        runs=len(results),
    ).save()
