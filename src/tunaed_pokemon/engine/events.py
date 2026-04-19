"""Battle event system.

Defines BattleEvent types emitted by the BattleEngine.
The EventBus distributes events to subscribers (GUI, Undo stack, animation player).
Satisfies: B-02 (event log for Undo/Redo), B-03 (animation playback).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class BattleEventType(str, Enum):
    """Types of battle events emitted during a turn."""

    # Turn lifecycle
    TURN_START = "turn_start"
    TURN_END = "turn_end"

    # Actions
    MOVE_USED = "move_used"
    MOVE_HIT = "move_hit"
    MOVE_MISSED = "move_missed"
    MOVE_FAILED = "move_failed"
    CRITICAL_HIT = "critical_hit"

    # Damage / healing
    DAMAGE_DEALT = "damage_dealt"
    DAMAGE_HEALED = "damage_healed"
    RECOIL_DAMAGE = "recoil_damage"

    # Stat modifications (ST-02: strictly separate)
    STAT_RANK_CHANGED = "stat_rank_changed"       # 상승/하락 (rank stage)
    STAT_REINFORCED = "stat_reinforced"            # 강화 (multiplier)

    # Status
    STATUS_CONDITION_APPLIED = "status_condition_applied"
    STATUS_CONDITION_CURED = "status_condition_cured"
    STATUS_CHANGE_APPLIED = "status_change_applied"
    STATUS_CHANGE_REMOVED = "status_change_removed"

    # Switching
    SWITCH_OUT = "switch_out"
    SWITCH_IN = "switch_in"
    FORCED_SWITCH = "forced_switch"

    # Fainting
    POKEMON_FAINTED = "pokemon_fainted"

    # Field / weather / terrain
    WEATHER_CHANGED = "weather_changed"
    TERRAIN_CHANGED = "terrain_changed"
    FIELD_EFFECT_SET = "field_effect_set"
    FIELD_EFFECT_REMOVED = "field_effect_removed"
    SPECIAL_FIELD_SET = "special_field_set"
    SPECIAL_FIELD_REMOVED = "special_field_removed"

    # Ability
    ABILITY_TRIGGERED = "ability_triggered"
    ABILITY_CHANGED = "ability_changed"

    # Potential
    POTENTIAL_TRIGGERED = "potential_triggered"

    # Item
    ITEM_USED = "item_used"
    ITEM_CONSUMED = "item_consumed"

    # Command potential (trainer)
    COMMAND_USED = "command_used"

    # Battle result
    BATTLE_ENDED = "battle_ended"

    # Edit mode (B-04)
    STATE_EDITED = "state_edited"


@dataclass
class BattleEvent:
    """A single battle event.

    Attributes:
        event_type: What happened.
        turn: Turn number when the event occurred.
        source_side: Which side triggered (0 or 1, or None for global).
        source_index: Index of the Pokémon/trainer that triggered.
        target_side: Target side (0 or 1, or None).
        target_index: Target Pokémon index.
        data: Arbitrary payload with event-specific details.
    """

    event_type: BattleEventType
    turn: int = 0
    source_side: Optional[int] = None
    source_index: Optional[int] = None
    target_side: Optional[int] = None
    target_index: Optional[int] = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict for JSON persistence."""
        return {
            "event_type": self.event_type.value,
            "turn": self.turn,
            "source_side": self.source_side,
            "source_index": self.source_index,
            "target_side": self.target_side,
            "target_index": self.target_index,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BattleEvent:
        """Deserialize from a dict."""
        return cls(
            event_type=BattleEventType(d["event_type"]),
            turn=d.get("turn", 0),
            source_side=d.get("source_side"),
            source_index=d.get("source_index"),
            target_side=d.get("target_side"),
            target_index=d.get("target_index"),
            data=d.get("data", {}),
        )


# Subscriber callback signature: receives a BattleEvent.
EventHandler = Callable[[BattleEvent], None]


class EventBus:
    """Event bus that distributes BattleEvents to registered subscribers.

    Subscribers can register for all events or specific event types.
    Events are also recorded in an ordered log for replay (B-03) and Undo (B-02).
    """

    def __init__(self) -> None:
        self._handlers: dict[BattleEventType | None, list[EventHandler]] = {}
        self._event_log: list[BattleEvent] = []

    def subscribe(
        self,
        handler: EventHandler,
        event_type: BattleEventType | None = None,
    ) -> None:
        """Register a handler.

        Args:
            handler: Callable receiving BattleEvent.
            event_type: Specific event type to listen for.
                        None means listen to ALL events.
        """
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(
        self,
        handler: EventHandler,
        event_type: BattleEventType | None = None,
    ) -> None:
        """Remove a previously registered handler."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def emit(self, event: BattleEvent) -> None:
        """Emit an event: log it and notify all matching subscribers."""
        self._event_log.append(event)

        # Notify type-specific handlers.
        for handler in self._handlers.get(event.event_type, []):
            handler(event)

        # Notify global handlers (subscribed with event_type=None).
        for handler in self._handlers.get(None, []):
            handler(event)

    @property
    def event_log(self) -> list[BattleEvent]:
        """Return the ordered list of all emitted events."""
        return list(self._event_log)

    def clear_log(self) -> None:
        """Clear the event log."""
        self._event_log.clear()
