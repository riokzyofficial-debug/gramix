from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum


class ChatType(StrEnum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


@dataclass(frozen=True, slots=True)
class Chat:
    id: int
    type: ChatType
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    @property
    def is_private(self) -> bool:
        return self.type == ChatType.PRIVATE

    @property
    def is_group(self) -> bool:
        return self.type in (ChatType.GROUP, ChatType.SUPERGROUP)

    @property
    def is_channel(self) -> bool:
        return self.type == ChatType.CHANNEL

    @property
    def display_name(self) -> str:
        if self.title:
            return self.title
        if self.first_name:
            parts = [self.first_name]
            if self.last_name:
                parts.append(self.last_name)
            return " ".join(parts)
        return str(self.id)

    @classmethod
    def from_dict(cls, data: dict) -> Chat:
        return cls(
            id=data["id"],
            type=ChatType(data["type"]),
            title=data.get("title"),
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
        )
