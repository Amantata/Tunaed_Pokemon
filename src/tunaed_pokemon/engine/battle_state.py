"""Battle state and snapshot management.

Provides the full serializable battle state for:
- Save/Load (B-01)
- Undo/Redo via turn history (B-02)
- Battle editor mode (B-04)
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from tunaed_pokemon.models.enums import (
    PokemonType,
    StatType,
    BASE_STAT_TYPES,
)
from tunaed_pokemon.engine.events import BattleEvent
from tunaed_pokemon.engine.field_state import FieldStateManager
from tunaed_pokemon.engine.status import StatusEngine


@dataclass
class BattlePokemonState:
    """Runtime state for a single Pokémon in battle.

    This is the mutable in-battle state, separate from the static Pokemon data model.
    Contains current HP, stat stages, active stat reinforcements, etc.
    """

    # Static identity
    pokemon_id: Optional[int] = None
    species: str = ""
    name: str = ""
    level: int = 50
    types: list[str] = field(default_factory=lambda: ["노말"])
    ability_name: str = ""
    original_ability_name: str = ""  # For tracking ability changes (SK-04)

    # HP
    max_hp: int = 1
    current_hp: int = 1

    # Calculated stats (base + IV/EV + nature, before battle modifiers)
    calculated_stats: dict[str, int] = field(default_factory=dict)

    # Rank stages (상승/하락) per stat — ST-02
    rank_stages: dict[str, int] = field(
        default_factory=lambda: {
            "공격": 0, "방어": 0, "특공": 0, "특방": 0, "속도": 0,
            "명중": 0, "회피": 0,
        }
    )

    # Reinforcement multipliers (강화) per stat — ST-02
    reinforcements: dict[str, float] = field(
        default_factory=lambda: {
            "공격": 1.0, "방어": 1.0, "특공": 1.0, "특방": 1.0, "속도": 1.0,
        }
    )

    # Held item
    item_id: Optional[int] = None
    item_name: str = ""
    item_consumed: bool = False

    # Move PP tracking: {move_id: current_pp}
    move_pp: dict[int, int] = field(default_factory=dict)

    # Flags
    is_fainted: bool = False
    is_active: bool = False  # Currently on the field
    has_moved_this_turn: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "pokemon_id": self.pokemon_id,
            "species": self.species,
            "name": self.name,
            "level": self.level,
            "types": self.types,
            "ability_name": self.ability_name,
            "original_ability_name": self.original_ability_name,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "calculated_stats": self.calculated_stats,
            "rank_stages": self.rank_stages,
            "reinforcements": self.reinforcements,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "item_consumed": self.item_consumed,
            "move_pp": {str(k): v for k, v in self.move_pp.items()},
            "is_fainted": self.is_fainted,
            "is_active": self.is_active,
            "has_moved_this_turn": self.has_moved_this_turn,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BattlePokemonState:
        """Deserialize from dict."""
        state = cls()
        state.pokemon_id = d.get("pokemon_id")
        state.species = d.get("species", "")
        state.name = d.get("name", "")
        state.level = d.get("level", 50)
        state.types = d.get("types", ["노말"])
        state.ability_name = d.get("ability_name", "")
        state.original_ability_name = d.get("original_ability_name", "")
        state.max_hp = d.get("max_hp", 1)
        state.current_hp = d.get("current_hp", 1)
        state.calculated_stats = d.get("calculated_stats", {})
        state.rank_stages = d.get("rank_stages", {
            "공격": 0, "방어": 0, "특공": 0, "특방": 0, "속도": 0,
            "명중": 0, "회피": 0,
        })
        state.reinforcements = d.get("reinforcements", {
            "공격": 1.0, "방어": 1.0, "특공": 1.0, "특방": 1.0, "속도": 1.0,
        })
        state.item_id = d.get("item_id")
        state.item_name = d.get("item_name", "")
        state.item_consumed = d.get("item_consumed", False)
        state.move_pp = {int(k): v for k, v in d.get("move_pp", {}).items()}
        state.is_fainted = d.get("is_fainted", False)
        state.is_active = d.get("is_active", False)
        state.has_moved_this_turn = d.get("has_moved_this_turn", False)
        return state


@dataclass
class BattleSideState:
    """State for one side (player) of the battle."""

    trainer_name: str = ""
    trainer_id: Optional[int] = None
    pokemon: list[BattlePokemonState] = field(default_factory=list)

    @property
    def active_pokemon(self) -> list[BattlePokemonState]:
        """Return the currently active Pokémon (on the field)."""
        return [p for p in self.pokemon if p.is_active and not p.is_fainted]

    @property
    def alive_pokemon(self) -> list[BattlePokemonState]:
        """Return all non-fainted Pokémon."""
        return [p for p in self.pokemon if not p.is_fainted]

    @property
    def all_fainted(self) -> bool:
        """Whether all Pokémon on this side have fainted."""
        return all(p.is_fainted for p in self.pokemon)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "trainer_name": self.trainer_name,
            "trainer_id": self.trainer_id,
            "pokemon": [p.to_dict() for p in self.pokemon],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BattleSideState:
        """Deserialize from dict."""
        state = cls()
        state.trainer_name = d.get("trainer_name", "")
        state.trainer_id = d.get("trainer_id")
        state.pokemon = [
            BattlePokemonState.from_dict(p) for p in d.get("pokemon", [])
        ]
        return state


@dataclass
class BattleStateSnapshot:
    """Complete serializable battle state.

    Used for save/load (B-01), Undo/Redo (B-02), and edit mode (B-04).
    """

    # Battle metadata
    turn_number: int = 0
    is_double_battle: bool = False
    battle_ended: bool = False
    winner_side: Optional[int] = None

    # Sides
    side_a: BattleSideState = field(default_factory=BattleSideState)
    side_b: BattleSideState = field(default_factory=BattleSideState)

    # Field state (FE-01 ~ FE-06)
    field_state: FieldStateManager = field(default_factory=FieldStateManager)

    # Status engine state
    status_state: StatusEngine = field(default_factory=StatusEngine)

    def get_side(self, side: int) -> BattleSideState:
        """Get side state by index (0=A, 1=B)."""
        if side == 0:
            return self.side_a
        return self.side_b

    def deep_copy(self) -> BattleStateSnapshot:
        """Create a deep copy for Undo/Redo history."""
        return BattleStateSnapshot.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete battle state to a dict for JSON persistence."""
        return {
            "turn_number": self.turn_number,
            "is_double_battle": self.is_double_battle,
            "battle_ended": self.battle_ended,
            "winner_side": self.winner_side,
            "side_a": self.side_a.to_dict(),
            "side_b": self.side_b.to_dict(),
            "field_state": self.field_state.to_dict(),
            "status_state": self.status_state.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BattleStateSnapshot:
        """Deserialize from a dict."""
        snap = cls()
        snap.turn_number = d.get("turn_number", 0)
        snap.is_double_battle = d.get("is_double_battle", False)
        snap.battle_ended = d.get("battle_ended", False)
        snap.winner_side = d.get("winner_side")
        snap.side_a = BattleSideState.from_dict(d.get("side_a", {}))
        snap.side_b = BattleSideState.from_dict(d.get("side_b", {}))
        snap.field_state = FieldStateManager.from_dict(d.get("field_state", {}))
        snap.status_state = StatusEngine.from_dict(d.get("status_state", {}))
        return snap

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> BattleStateSnapshot:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


class TurnHistory:
    """Stores turn-by-turn battle state snapshots for Undo/Redo (B-02).

    Also stores the event log for each turn for animation replay (B-03).
    """

    def __init__(self) -> None:
        self._snapshots: list[BattleStateSnapshot] = []
        self._event_logs: list[list[BattleEvent]] = []
        self._current_index: int = -1

    @property
    def current_index(self) -> int:
        """Current position in history (for Undo/Redo)."""
        return self._current_index

    @property
    def can_undo(self) -> bool:
        """Whether we can undo (go back one turn)."""
        return self._current_index > 0

    @property
    def can_redo(self) -> bool:
        """Whether we can redo (go forward one turn)."""
        return self._current_index < len(self._snapshots) - 1

    def push(
        self,
        snapshot: BattleStateSnapshot,
        events: list[BattleEvent] | None = None,
    ) -> None:
        """Push a new state snapshot and associated events.

        If we're in the middle of history (after undos), discard future states.
        """
        # Discard any future states beyond current position.
        self._snapshots = self._snapshots[: self._current_index + 1]
        self._event_logs = self._event_logs[: self._current_index + 1]

        self._snapshots.append(snapshot.deep_copy())
        self._event_logs.append(list(events or []))
        self._current_index = len(self._snapshots) - 1

    def undo(self) -> Optional[BattleStateSnapshot]:
        """Go back one turn. Returns the previous state, or None if at start."""
        if not self.can_undo:
            return None
        self._current_index -= 1
        return self._snapshots[self._current_index].deep_copy()

    def redo(self) -> Optional[BattleStateSnapshot]:
        """Go forward one turn. Returns the next state, or None if at end."""
        if not self.can_redo:
            return None
        self._current_index += 1
        return self._snapshots[self._current_index].deep_copy()

    def current_snapshot(self) -> Optional[BattleStateSnapshot]:
        """Return the current state snapshot."""
        if 0 <= self._current_index < len(self._snapshots):
            return self._snapshots[self._current_index].deep_copy()
        return None

    def get_events_for_turn(self, index: int) -> list[BattleEvent]:
        """Get the events for a specific turn index."""
        if 0 <= index < len(self._event_logs):
            return list(self._event_logs[index])
        return []

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full history."""
        return {
            "snapshots": [s.to_dict() for s in self._snapshots],
            "event_logs": [
                [e.to_dict() for e in events] for events in self._event_logs
            ],
            "current_index": self._current_index,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TurnHistory:
        """Deserialize from dict."""
        history = cls()
        history._snapshots = [
            BattleStateSnapshot.from_dict(s) for s in d.get("snapshots", [])
        ]
        history._event_logs = [
            [BattleEvent.from_dict(e) for e in events]
            for events in d.get("event_logs", [])
        ]
        history._current_index = d.get("current_index", -1)
        return history

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> TurnHistory:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
