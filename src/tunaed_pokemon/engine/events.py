"""EventBus and BattleEvent types for the battle engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class BattleEventType(Enum):
    MOVE_USED = "move_used"
    DAMAGE_DEALT = "damage_dealt"
    STATUS_APPLIED = "status_applied"
    STATUS_REMOVED = "status_removed"
    POKEMON_FAINTED = "pokemon_fainted"
    POKEMON_SWITCHED = "pokemon_switched"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    FIELD_CHANGED = "field_changed"
    RANK_CHANGED = "rank_changed"
    HP_CHANGED = "hp_changed"
    MESSAGE = "message"
    BATTLE_END = "battle_end"


@dataclass
class BattleEvent:
    event_type: BattleEventType
    side: int = 0      # 0 = global, 1 = side1, 2 = side2
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "side": self.side,
            "data": self.data,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BattleEvent":
        return cls(
            event_type=BattleEventType(d["event_type"]),
            side=d.get("side", 0),
            data=d.get("data", {}),
            message=d.get("message", ""),
        )


class EventBus:
    """Simple pub/sub event bus for battle events (B-03)."""

    def __init__(self) -> None:
        self._handlers: dict[BattleEventType, list[Callable[[BattleEvent], None]]] = {}
        self._event_log: list[BattleEvent] = []

    def subscribe(self, event_type: BattleEventType, handler: Callable[[BattleEvent], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: BattleEventType, handler: Callable[[BattleEvent], None]) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def emit(self, event: BattleEvent) -> None:
        self._event_log.append(event)
        for handler in list(self._handlers.get(event.event_type, [])):
            handler(event)

    def emit_message(self, msg: str, side: int = 0) -> None:
        self.emit(BattleEvent(BattleEventType.MESSAGE, side=side, message=msg))

    @property
    def event_log(self) -> list[BattleEvent]:
        return list(self._event_log)

    def clear_log(self) -> None:
        self._event_log.clear()

    def export_log(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._event_log]
