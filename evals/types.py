from typing import Literal, TypedDict

Role = Literal["user", "system", "assistant"]

PlayerRole = Literal["opponent", "llm"]

PlayerRoleMap: dict[PlayerRole, Role] = {"opponent": "user", "llm": "assistant"}


class Message(TypedDict):
    content: str
    role: Role
