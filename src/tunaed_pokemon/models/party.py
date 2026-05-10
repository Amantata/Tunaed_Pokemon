"""Party data model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Party:
    """파티 = 트레이너 + 파티원 (P-01, P-02)."""
    id: str
    name: str
    trainer_id: Optional[str] = None
    pokemon_ids: list[str] = field(default_factory=list)   # 1–8 Pokémon IDs
    max_size: int = 6

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "trainer_id": self.trainer_id,
            "pokemon_ids": list(self.pokemon_ids),
            "max_size": self.max_size,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Party":
        known = {"id", "name", "trainer_id", "pokemon_ids", "max_size"}
        return cls(**{k: v for k, v in d.items() if k in known})

    @classmethod
    def new(cls, name: str) -> "Party":
        return cls(id=str(uuid.uuid4()), name=name)
