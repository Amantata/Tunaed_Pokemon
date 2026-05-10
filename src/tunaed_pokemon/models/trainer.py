"""Trainer data model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .enums import QualityName, QualityRank


@dataclass
class Quality:
    """자질 (trainer quality) with rank."""
    name: str   # QualityName value
    rank: str = QualityRank.E.value

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "rank": self.rank}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Quality":
        return cls(name=d["name"], rank=d.get("rank", QualityRank.E.value))


@dataclass
class CommandPotential:
    """지령 포텐셜 (command potential) for a trainer."""
    name: str
    effect: str = ""
    command_type: str = "기본"   # CommandPotentialType value

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "effect": self.effect, "command_type": self.command_type}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CommandPotential":
        return cls(name=d["name"], effect=d.get("effect", ""), command_type=d.get("command_type", "기본"))


@dataclass
class InnatePotential:
    """고유포텐셜 — a unique potential specific to this trainer (PT-05, SEPARATE field)."""
    name: str
    effect: str = ""
    script: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "effect": self.effect, "script": self.script}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "InnatePotential":
        return cls(name=d["name"], effect=d.get("effect", ""), script=d.get("script", ""))


def _default_qualities() -> list[Quality]:
    return [
        Quality(QualityName.COMMAND.value),
        Quality(QualityName.LEADERSHIP.value),
        Quality(QualityName.TRAINING.value),
        Quality(QualityName.ABILITY_Q.value),
    ]


@dataclass
class Trainer:
    """Trainer data model (P-01)."""
    id: str
    name: str
    alias: str = ""     # 별칭
    origin: str = ""    # 출신
    career: str = ""    # 경력
    qualities: list[Quality] = field(default_factory=_default_qualities)
    command_potentials: list[CommandPotential] = field(default_factory=list)
    # 고유포텐셜 is kept in a SEPARATE field per PT-05 naming rules
    innate_potentials: list[InnatePotential] = field(default_factory=list)
    image_path: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "alias": self.alias,
            "origin": self.origin,
            "career": self.career,
            "qualities": [q.to_dict() for q in self.qualities],
            "command_potentials": [cp.to_dict() for cp in self.command_potentials],
            "innate_potentials": [ip.to_dict() for ip in self.innate_potentials],
            "image_path": self.image_path,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Trainer":
        d = d.copy()
        d["qualities"] = [Quality.from_dict(q) for q in d.get("qualities", [])]
        d["command_potentials"] = [CommandPotential.from_dict(cp) for cp in d.get("command_potentials", [])]
        d["innate_potentials"] = [InnatePotential.from_dict(ip) for ip in d.get("innate_potentials", [])]
        known = {
            "id", "name", "alias", "origin", "career",
            "qualities", "command_potentials", "innate_potentials",
            "image_path", "notes",
        }
        return cls(**{k: v for k, v in d.items() if k in known})

    @classmethod
    def new(cls, name: str) -> "Trainer":
        return cls(id=str(uuid.uuid4()), name=name)
