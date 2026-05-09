"""Status condition and status change engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional

from ..models.enums import StatusCondition

# Major status conditions that are mutually exclusive
_MAJOR_STATUS = {sc.value for sc in StatusCondition if sc != StatusCondition.CONFUSION}


@dataclass
class StatusState:
    """Runtime status state for one battle Pokémon."""
    major_status: Optional[str] = None    # one of the 7 major status condition values
    sleep_turns: int = 0
    bad_poison_counter: int = 0
    is_confused: bool = False
    status_changes: dict[str, Any] = field(default_factory=dict)  # name → value/turns

    def to_dict(self) -> dict[str, Any]:
        return {
            "major_status": self.major_status,
            "sleep_turns": self.sleep_turns,
            "bad_poison_counter": self.bad_poison_counter,
            "is_confused": self.is_confused,
            "status_changes": dict(self.status_changes),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StatusState":
        obj = cls()
        obj.major_status = d.get("major_status")
        obj.sleep_turns = d.get("sleep_turns", 0)
        obj.bad_poison_counter = d.get("bad_poison_counter", 0)
        obj.is_confused = d.get("is_confused", False)
        obj.status_changes = dict(d.get("status_changes", {}))
        return obj


class StatusEngine:
    """Applies and resolves status conditions and status changes."""

    def can_apply_major_status(self, state: StatusState) -> bool:
        return state.major_status is None

    def apply_major_status(self, state: StatusState, status: StatusCondition) -> bool:
        """Attempt to apply a major status. Returns True if applied."""
        if not self.can_apply_major_status(state):
            return False
        state.major_status = status.value
        if status == StatusCondition.SLEEP:
            state.sleep_turns = random.randint(1, 3)
        return True

    def remove_major_status(self, state: StatusState) -> None:
        state.major_status = None
        state.sleep_turns = 0
        state.bad_poison_counter = 0

    def apply_confusion(self, state: StatusState) -> bool:
        if state.is_confused:
            return False
        state.is_confused = True
        return True

    def remove_confusion(self, state: StatusState) -> None:
        state.is_confused = False

    def set_status_change(self, state: StatusState, name: str, value: Any = True) -> None:
        state.status_changes[name] = value

    def remove_status_change(self, state: StatusState, name: str) -> None:
        state.status_changes.pop(name, None)

    def has_status_change(self, state: StatusState, name: str) -> bool:
        return name in state.status_changes

    def end_of_turn_damage(self, state: StatusState, max_hp: int) -> int:
        """Calculate end-of-turn damage from status conditions. Returns damage amount."""
        ms = state.major_status
        if ms == StatusCondition.BURN.value:
            return max(1, max_hp // 8)
        if ms == StatusCondition.FROSTBITE.value:
            return max(1, max_hp // 16)
        if ms == StatusCondition.POISON.value:
            return max(1, max_hp // 8)
        if ms == StatusCondition.BAD_POISON.value:
            state.bad_poison_counter += 1
            return max(1, max_hp * state.bad_poison_counter // 16)
        return 0

    def on_switch_out(self, state: StatusState) -> None:
        """Reset volatile status changes on switch out (keep major status)."""
        state.is_confused = False
        # Remove volatile status changes but keep persistent ones
        volatile = {"혼란", "앵콜", "봉인", "도발", "트집", "분진", "요격"}
        for name in volatile:
            state.status_changes.pop(name, None)

    def get_display_text(self, state: StatusState) -> str:
        if state.major_status:
            return state.major_status
        if state.is_confused:
            return "혼란"
        return ""
