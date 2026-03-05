from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class AIProvider(Protocol):
    name: str

    def generate(self, prompt: str, snapshot: dict[str, Any]) -> str:
        ...


@dataclass(frozen=True)
class AIResult:
    provider: str
    text: str
    warning: str | None
    used_fallback: bool
