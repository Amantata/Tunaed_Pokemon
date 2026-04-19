"""Status engine.

Manages status conditions (상태이상) and status changes (상태변화).
Status conditions and changes are independent concepts that can coexist.

Rules:
- A Pokémon can have at most one primary status condition (except sleep limit).
- Sleep (잠듦) is limited to max 2 across a party.
- Confusion (혼란) is treated as both a status change and status condition.
- Status changes are stackable/multiple and can coexist with conditions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from tunaed_pokemon.models.enums import StatusCondition, StatusChange


@dataclass
class PokemonStatusState:
    """Status state for a single Pokémon.

    Tracks both the primary status condition and all active status changes.
    """

    # Primary status condition (at most one non-NONE).
    condition: StatusCondition = StatusCondition.NONE
    condition_turns: int = 0  # Turns remaining (e.g. sleep counter).
    condition_data: dict[str, Any] = field(default_factory=dict)

    # Active status changes -> {change: {turns_remaining, data}}.
    changes: dict[StatusChange, dict[str, Any]] = field(default_factory=dict)

    def apply_condition(
        self,
        condition: StatusCondition,
        turns: int = 0,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Apply a status condition.

        Returns True if applied, False if blocked (already has a condition).
        A Pokémon can only have one primary condition at a time.
        """
        if self.condition != StatusCondition.NONE:
            return False
        self.condition = condition
        self.condition_turns = turns
        self.condition_data = data or {}
        return True

    def cure_condition(self) -> StatusCondition:
        """Remove the current status condition.

        Returns:
            The condition that was cured (NONE if nothing was cured).
        """
        previous = self.condition
        self.condition = StatusCondition.NONE
        self.condition_turns = 0
        self.condition_data = {}
        return previous

    def apply_change(
        self,
        change: StatusChange,
        turns: Optional[int] = None,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Apply a status change.

        Status changes can coexist. However, applying the same change
        again typically refreshes/replaces it.

        Returns True (always succeeds for now; more rules may apply later).
        """
        self.changes[change] = {
            "turns": turns,
            **(data or {}),
        }
        return True

    def remove_change(self, change: StatusChange) -> bool:
        """Remove a status change.

        Returns True if it was present, False otherwise.
        """
        if change in self.changes:
            del self.changes[change]
            return True
        return False

    def has_change(self, change: StatusChange) -> bool:
        """Check if a status change is active."""
        return change in self.changes

    def has_condition(self, condition: StatusCondition) -> bool:
        """Check if a specific condition is active."""
        return self.condition == condition

    def tick(self) -> dict[str, Any]:
        """Process end-of-turn for status.

        Decrements turn counters. Returns info about expired statuses.
        """
        result: dict[str, Any] = {}

        # Condition tick
        if self.condition != StatusCondition.NONE and self.condition_turns > 0:
            self.condition_turns -= 1
            if self.condition_turns <= 0:
                result["condition_expired"] = self.condition.value
                self.condition = StatusCondition.NONE
                self.condition_turns = 0
                self.condition_data = {}

        # Status changes tick
        expired_changes: list[str] = []
        to_remove: list[StatusChange] = []
        for change, info in self.changes.items():
            turns = info.get("turns")
            if turns is not None:
                remaining = turns - 1
                if remaining <= 0:
                    expired_changes.append(change.value)
                    to_remove.append(change)
                else:
                    info["turns"] = remaining
        for change in to_remove:
            del self.changes[change]
        if expired_changes:
            result["changes_expired"] = expired_changes

        return result

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "condition": self.condition.value,
            "condition_turns": self.condition_turns,
            "condition_data": self.condition_data,
            "changes": {c.value: d for c, d in self.changes.items()},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PokemonStatusState:
        """Deserialize from dict."""
        state = cls()
        state.condition = StatusCondition(d.get("condition", "없음"))
        state.condition_turns = d.get("condition_turns", 0)
        state.condition_data = d.get("condition_data", {})
        for name, data in d.get("changes", {}).items():
            state.changes[StatusChange(name)] = data
        return state


@dataclass
class StatusEngine:
    """Manages status states for all Pokémon in a battle.

    Tracks each active Pokémon's status by (side, slot) key.
    Also enforces party-wide constraints (e.g. sleep clause).
    """

    # (side, slot) -> PokemonStatusState
    _states: dict[tuple[int, int], PokemonStatusState] = field(default_factory=dict)

    def get_state(self, side: int, slot: int) -> PokemonStatusState:
        """Get or create the status state for a Pokémon."""
        key = (side, slot)
        if key not in self._states:
            self._states[key] = PokemonStatusState()
        return self._states[key]

    def apply_condition(
        self,
        side: int,
        slot: int,
        condition: StatusCondition,
        turns: int = 0,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Apply a status condition to a Pokémon.

        Enforces single-condition rule.
        """
        state = self.get_state(side, slot)
        return state.apply_condition(condition, turns, data)

    def cure_condition(self, side: int, slot: int) -> StatusCondition:
        """Cure the status condition of a Pokémon."""
        state = self.get_state(side, slot)
        return state.cure_condition()

    def apply_change(
        self,
        side: int,
        slot: int,
        change: StatusChange,
        turns: Optional[int] = None,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Apply a status change to a Pokémon."""
        state = self.get_state(side, slot)
        return state.apply_change(change, turns, data)

    def remove_change(
        self, side: int, slot: int, change: StatusChange
    ) -> bool:
        """Remove a status change from a Pokémon."""
        state = self.get_state(side, slot)
        return state.remove_change(change)

    def count_sleeping(self, side: int, party_size: int) -> int:
        """Count how many Pokémon on a side are asleep.

        Used to enforce the sleep limit (max 2 per party).
        """
        count = 0
        for slot in range(party_size):
            state = self.get_state(side, slot)
            if state.condition == StatusCondition.SLEEP:
                count += 1
        return count

    def can_apply_sleep(self, side: int, party_size: int, max_sleep: int = 2) -> bool:
        """Check if another Pokémon on this side can be put to sleep."""
        return self.count_sleeping(side, party_size) < max_sleep

    def tick_all(self) -> dict[tuple[int, int], dict[str, Any]]:
        """Process end-of-turn for all tracked Pokémon.

        Returns:
            Dict of (side, slot) -> tick result for Pokémon that had changes.
        """
        results: dict[tuple[int, int], dict[str, Any]] = {}
        for key, state in self._states.items():
            tick_result = state.tick()
            if tick_result:
                results[key] = tick_result
        return results

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            f"{side},{slot}": state.to_dict()
            for (side, slot), state in self._states.items()
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StatusEngine:
        """Deserialize from dict."""
        engine = cls()
        for key_str, state_dict in d.items():
            parts = key_str.split(",")
            side, slot = int(parts[0]), int(parts[1])
            engine._states[(side, slot)] = PokemonStatusState.from_dict(state_dict)
        return engine
