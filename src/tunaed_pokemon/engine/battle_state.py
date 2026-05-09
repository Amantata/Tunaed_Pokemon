"""Battle state: snapshot, side state, Pokémon runtime state, turn history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .field_state import FieldStateManager
from .status import StatusState


@dataclass
class RankStages:
    """랭크 상승/하락 (rank stage changes) for each stat. Range −6 to +6.

    ST-02: 상승 (rank stage) uses the rank multiplier table.
    This is SEPARATE from 강화 (Reinforcements below).
    """
    attack: int = 0
    defense: int = 0
    sp_atk: int = 0
    sp_def: int = 0
    speed: int = 0
    accuracy: int = 0
    evasion: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "attack": self.attack, "defense": self.defense,
            "sp_atk": self.sp_atk, "sp_def": self.sp_def,
            "speed": self.speed, "accuracy": self.accuracy,
            "evasion": self.evasion,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RankStages":
        known = {"attack", "defense", "sp_atk", "sp_def", "speed", "accuracy", "evasion"}
        return cls(**{k: v for k, v in d.items() if k in known})

    def change(self, stat: str, amount: int) -> int:
        """Apply a rank stage change. Returns the actual applied change."""
        current = getattr(self, stat, 0)
        new_val = max(-6, min(6, current + amount))
        actual = new_val - current
        setattr(self, stat, new_val)
        return actual

    def reset(self) -> None:
        self.attack = self.defense = self.sp_atk = self.sp_def = 0
        self.speed = self.accuracy = self.evasion = 0


@dataclass
class Reinforcements:
    """강화 (direct stat multipliers, NOT rank stages).

    ST-02: 강화 = multiplier applied directly to the stat value.
    This is STRICTLY SEPARATE from 상승 (RankStages above).
    """
    attack: float = 1.0
    defense: float = 1.0
    sp_atk: float = 1.0
    sp_def: float = 1.0
    speed: float = 1.0

    def to_dict(self) -> dict[str, float]:
        return {
            "attack": self.attack, "defense": self.defense,
            "sp_atk": self.sp_atk, "sp_def": self.sp_def, "speed": self.speed,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Reinforcements":
        known = {"attack", "defense", "sp_atk", "sp_def", "speed"}
        return cls(**{k: v for k, v in d.items() if k in known})

    def reset(self) -> None:
        self.attack = self.defense = self.sp_atk = self.sp_def = self.speed = 1.0


@dataclass
class BattlePokemonState:
    """Runtime state of one Pokémon during battle."""
    pokemon_id: str
    name: str
    current_hp: int
    max_hp: int
    level: int = 50
    type1: str = "노말"
    type2: Optional[str] = None
    rank_stages: RankStages = field(default_factory=RankStages)
    reinforcements: Reinforcements = field(default_factory=Reinforcements)  # 강화
    status: StatusState = field(default_factory=StatusState)
    ability_name: str = ""    # current ability; may change mid-battle (SK-04)
    move_ids: list[str] = field(default_factory=list)
    is_fainted: bool = False
    # Computed battle stats for damage calculation.
    # Keys: hp, attack, defense, sp_atk, sp_def, speed (all int).
    # Populated from Pokemon entity data when the battle is set up.
    battle_stats: dict[str, int] = field(default_factory=lambda: {
        "hp": 0, "attack": 50, "defense": 50,
        "sp_atk": 50, "sp_def": 50, "speed": 50,
    })

    def to_dict(self) -> dict[str, Any]:
        return {
            "pokemon_id": self.pokemon_id,
            "name": self.name,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "level": self.level,
            "type1": self.type1,
            "type2": self.type2,
            "rank_stages": self.rank_stages.to_dict(),
            "reinforcements": self.reinforcements.to_dict(),
            "status": self.status.to_dict(),
            "ability_name": self.ability_name,
            "move_ids": list(self.move_ids),
            "is_fainted": self.is_fainted,
            "battle_stats": dict(self.battle_stats),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BattlePokemonState":
        d = d.copy()
        d["rank_stages"] = RankStages.from_dict(d.get("rank_stages", {}))
        d["reinforcements"] = Reinforcements.from_dict(d.get("reinforcements", {}))
        d["status"] = StatusState.from_dict(d.get("status", {}))
        known = {
            "pokemon_id", "name", "current_hp", "max_hp", "level",
            "type1", "type2", "rank_stages", "reinforcements",
            "status", "ability_name", "move_ids", "is_fainted", "battle_stats",
        }
        return cls(**{k: v for k, v in d.items() if k in known})

    @property
    def hp_fraction(self) -> float:
        if self.max_hp == 0:
            return 0.0
        return self.current_hp / self.max_hp


@dataclass
class BattleSideState:
    """Runtime state of one side (trainer + party) in the battle."""
    trainer_id: Optional[str]
    trainer_name: str
    party_id: Optional[str]
    pokemon_states: list[BattlePokemonState] = field(default_factory=list)
    active_indices: list[int] = field(default_factory=lambda: [0])

    def to_dict(self) -> dict[str, Any]:
        return {
            "trainer_id": self.trainer_id,
            "trainer_name": self.trainer_name,
            "party_id": self.party_id,
            "pokemon_states": [ps.to_dict() for ps in self.pokemon_states],
            "active_indices": list(self.active_indices),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BattleSideState":
        d = d.copy()
        d["pokemon_states"] = [BattlePokemonState.from_dict(ps) for ps in d.get("pokemon_states", [])]
        known = {"trainer_id", "trainer_name", "party_id", "pokemon_states", "active_indices"}
        return cls(**{k: v for k, v in d.items() if k in known})

    @property
    def active_pokemon(self) -> list[BattlePokemonState]:
        return [
            self.pokemon_states[i]
            for i in self.active_indices
            if 0 <= i < len(self.pokemon_states)
        ]

    @property
    def is_all_fainted(self) -> bool:
        return bool(self.pokemon_states) and all(ps.is_fainted for ps in self.pokemon_states)


@dataclass
class BattleStateSnapshot:
    """Complete serialisable snapshot of battle state at a point in time (B-01, B-02)."""
    turn_number: int = 0
    battle_format: str = "싱글"
    side1: BattleSideState = field(
        default_factory=lambda: BattleSideState(None, "플레이어 1", None)
    )
    side2: BattleSideState = field(
        default_factory=lambda: BattleSideState(None, "플레이어 2", None)
    )
    field_state: FieldStateManager = field(default_factory=FieldStateManager)
    log: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_number": self.turn_number,
            "battle_format": self.battle_format,
            "side1": self.side1.to_dict(),
            "side2": self.side2.to_dict(),
            "field_state": self.field_state.to_dict(),
            "log": list(self.log),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BattleStateSnapshot":
        obj = cls()
        obj.turn_number = d.get("turn_number", 0)
        obj.battle_format = d.get("battle_format", "싱글")
        obj.side1 = BattleSideState.from_dict(d.get("side1", {"trainer_id": None, "trainer_name": "플레이어 1", "party_id": None}))
        obj.side2 = BattleSideState.from_dict(d.get("side2", {"trainer_id": None, "trainer_name": "플레이어 2", "party_id": None}))
        obj.field_state = FieldStateManager.from_dict(d.get("field_state", {}))
        obj.log = list(d.get("log", []))
        return obj

    def deep_copy(self) -> "BattleStateSnapshot":
        return BattleStateSnapshot.from_dict(self.to_dict())

    def add_log(self, msg: str) -> None:
        self.log.append(msg)


class TurnHistory:
    """Ordered list of BattleStateSnapshots enabling Undo/Redo (B-02)."""

    def __init__(self) -> None:
        self._snapshots: list[BattleStateSnapshot] = []
        self._index: int = -1

    def push(self, snapshot: BattleStateSnapshot) -> None:
        """Record a new snapshot, discarding any future redo history."""
        self._snapshots = self._snapshots[: self._index + 1]
        self._snapshots.append(snapshot.deep_copy())
        self._index = len(self._snapshots) - 1

    def can_undo(self) -> bool:
        return self._index > 0

    def can_redo(self) -> bool:
        return self._index < len(self._snapshots) - 1

    def undo(self) -> Optional[BattleStateSnapshot]:
        if not self.can_undo():
            return None
        self._index -= 1
        return self._snapshots[self._index].deep_copy()

    def redo(self) -> Optional[BattleStateSnapshot]:
        if not self.can_redo():
            return None
        self._index += 1
        return self._snapshots[self._index].deep_copy()

    @property
    def current(self) -> Optional[BattleStateSnapshot]:
        if 0 <= self._index < len(self._snapshots):
            return self._snapshots[self._index]
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshots": [s.to_dict() for s in self._snapshots],
            "index": self._index,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TurnHistory":
        obj = cls()
        obj._snapshots = [BattleStateSnapshot.from_dict(s) for s in d.get("snapshots", [])]
        obj._index = d.get("index", -1)
        return obj
