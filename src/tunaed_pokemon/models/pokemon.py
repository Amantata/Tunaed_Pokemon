"""Pokemon (party member) data model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class IVs:
    """개체치 (Individual Values) for each stat."""
    hp: int = 0
    attack: int = 0
    defense: int = 0
    sp_atk: int = 0
    sp_def: int = 0
    speed: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "hp": self.hp, "attack": self.attack, "defense": self.defense,
            "sp_atk": self.sp_atk, "sp_def": self.sp_def, "speed": self.speed,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IVs":
        fields = {"hp", "attack", "defense", "sp_atk", "sp_def", "speed"}
        return cls(**{k: v for k, v in d.items() if k in fields})


@dataclass
class EVs:
    """노력치 (Effort Values) for each stat — default 0 per ST-01."""
    hp: int = 0
    attack: int = 0
    defense: int = 0
    sp_atk: int = 0
    sp_def: int = 0
    speed: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "hp": self.hp, "attack": self.attack, "defense": self.defense,
            "sp_atk": self.sp_atk, "sp_def": self.sp_def, "speed": self.speed,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EVs":
        fields = {"hp", "attack", "defense", "sp_atk", "sp_def", "speed"}
        return cls(**{k: v for k, v in d.items() if k in fields})


@dataclass
class MoveData:
    """A move/technique entry in the master list (SK-01)."""
    id: str
    name: str
    type: str = "노말"
    category: str = "변화"
    power: Optional[int] = None
    accuracy: Optional[int] = None
    pp: int = 5
    priority: int = 0   # move priority; ≥5 = 가장 먼저, 1-4 = 상대보다 먼저, 0 = normal, <0 = last
    effect: str = ""
    effect_script: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "type": self.type,
            "category": self.category, "power": self.power, "accuracy": self.accuracy,
            "pp": self.pp, "priority": self.priority,
            "effect": self.effect, "effect_script": self.effect_script,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MoveData":
        known = {"id", "name", "type", "category", "power", "accuracy", "pp", "priority", "effect", "effect_script"}
        return cls(**{k: v for k, v in d.items() if k in known})

    @classmethod
    def new(cls, name: str) -> "MoveData":
        return cls(id=str(uuid.uuid4()), name=name)


@dataclass
class AbilityData:
    """An ability entry in the master list (SK-03)."""
    id: str
    name: str
    effect: str = ""
    effect_script: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "effect": self.effect, "effect_script": self.effect_script}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AbilityData":
        known = {"id", "name", "effect", "effect_script"}
        return cls(**{k: v for k, v in d.items() if k in known})

    @classmethod
    def new(cls, name: str) -> "AbilityData":
        return cls(id=str(uuid.uuid4()), name=name)


@dataclass
class PotentialData:
    """A potential template in the master list (PT-02)."""
    id: str
    category: str
    name: str
    trigger: str = ""
    effect: str = ""
    script: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "category": self.category, "name": self.name,
            "trigger": self.trigger, "effect": self.effect, "script": self.script,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PotentialData":
        known = {"id", "category", "name", "trigger", "effect", "script"}
        return cls(**{k: v for k, v in d.items() if k in known})

    @classmethod
    def new(cls, category: str, name: str) -> "PotentialData":
        return cls(id=str(uuid.uuid4()), category=category, name=name)


@dataclass
class AssignedPotential:
    """A potential assigned to a specific Pokémon (may have custom script override)."""
    slot: str
    template_id: Optional[str] = None
    name: str = ""
    trigger: str = ""
    effect: str = ""
    script: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot": self.slot, "template_id": self.template_id,
            "name": self.name, "trigger": self.trigger,
            "effect": self.effect, "script": self.script,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AssignedPotential":
        known = {"slot", "template_id", "name", "trigger", "effect", "script"}
        return cls(**{k: v for k, v in d.items() if k in known})


# All potential slots for a Pokémon (PT-05). 전용포텐셜 is stored as a SEPARATE field.
POKEMON_POTENTIAL_SLOTS = [
    "역할", "분류", "주인", "이명",
    "계제①", "계제②", "계제③", "계제④",
    "속별", "유대", "선제", "회피", "내성", "격",
    "범용", "부수", "특권", "PT①", "PT②",
]

# Potentials all Pokémon always possess
MANDATORY_POTENTIAL_SLOTS = {"계제①", "계제②", "속별", "선제", "회피", "내성", "격", "범용"}


@dataclass
class Pokemon:
    """Party member (포켓몬/파티원) data model."""
    id: str
    name: str
    gender: str = ""             # ♂ / ♀ / -
    is_alien: bool = False       # 아인종 여부
    type1: str = "노말"          # PokemonType value
    type2: Optional[str] = None
    ability_id: Optional[str] = None
    ability_name: str = ""
    level: int = 50
    ivs: IVs = field(default_factory=IVs)
    evs: EVs = field(default_factory=EVs)
    base_stats: dict[str, int] = field(default_factory=lambda: {
        "hp": 50, "attack": 50, "defense": 50,
        "sp_atk": 50, "sp_def": 50, "speed": 50,
    })
    move_ids: list[str] = field(default_factory=list)       # refs to MoveData.id (4–8, SK-01)
    potentials: list[AssignedPotential] = field(default_factory=list)
    # 전용포텐셜 is kept in a SEPARATE field per PT-05 naming rules
    exclusive_potential: Optional[AssignedPotential] = None
    image_path: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "is_alien": self.is_alien,
            "type1": self.type1,
            "type2": self.type2,
            "ability_id": self.ability_id,
            "ability_name": self.ability_name,
            "level": self.level,
            "ivs": self.ivs.to_dict(),
            "evs": self.evs.to_dict(),
            "base_stats": dict(self.base_stats),
            "move_ids": list(self.move_ids),
            "potentials": [p.to_dict() for p in self.potentials],
            "exclusive_potential": self.exclusive_potential.to_dict() if self.exclusive_potential else None,
            "image_path": self.image_path,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Pokemon":
        d = d.copy()
        if isinstance(d.get("ivs"), dict):
            d["ivs"] = IVs.from_dict(d["ivs"])
        if isinstance(d.get("evs"), dict):
            d["evs"] = EVs.from_dict(d["evs"])
        d["potentials"] = [AssignedPotential.from_dict(p) for p in d.get("potentials", [])]
        if isinstance(d.get("exclusive_potential"), dict):
            d["exclusive_potential"] = AssignedPotential.from_dict(d["exclusive_potential"])
        known = {
            "id", "name", "gender", "is_alien", "type1", "type2",
            "ability_id", "ability_name", "level", "ivs", "evs",
            "base_stats", "move_ids", "potentials", "exclusive_potential",
            "image_path", "notes",
        }
        return cls(**{k: v for k, v in d.items() if k in known})

    @classmethod
    def new(cls, name: str) -> "Pokemon":
        return cls(id=str(uuid.uuid4()), name=name)
