from __future__ import annotations
from dataclasses import dataclass, field

from gramix.types.user import User


@dataclass(slots=True)
class PollOption:
    text: str
    voter_count: int

    @classmethod
    def from_dict(cls, data: dict) -> PollOption:
        return cls(
            text=data["text"],
            voter_count=data["voter_count"],
        )


@dataclass(slots=True)
class Poll:
    id: str
    question: str
    options: list[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    poll_type: str
    allows_multiple_answers: bool
    correct_option_id: int | None = None
    explanation: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Poll:
        return cls(
            id=data["id"],
            question=data["question"],
            options=[PollOption.from_dict(o) for o in data["options"]],
            total_voter_count=data["total_voter_count"],
            is_closed=data.get("is_closed", False),
            is_anonymous=data.get("is_anonymous", True),
            poll_type=data.get("type", "regular"),
            allows_multiple_answers=data.get("allows_multiple_answers", False),
            correct_option_id=data.get("correct_option_id"),
            explanation=data.get("explanation"),
        )


@dataclass(slots=True)
class PollAnswer:
    poll_id: str
    option_ids: list[int] = field(default_factory=list)
    user: User | None = None
    voter_chat: dict | None = None

    @property
    def retracted(self) -> bool:
        return len(self.option_ids) == 0

    @classmethod
    def from_dict(cls, data: dict) -> PollAnswer:
        user: User | None = None
        voter_chat: dict | None = None
        if "user" in data:
            user = User.from_dict(data["user"])
        if "voter_chat" in data:
            voter_chat = data["voter_chat"]
        return cls(
            poll_id=data["poll_id"],
            option_ids=data.get("option_ids", []),
            user=user,
            voter_chat=voter_chat,
        )
