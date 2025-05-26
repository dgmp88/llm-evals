from typing import Literal, TypedDict

Role = Literal["user", "system", "assistant"]


class Message(TypedDict):
    content: str
    role: Role
