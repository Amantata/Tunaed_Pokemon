"""Action order resolution for the battle engine.

Priority tiers (CLAUDE.md §4.2 / battle flow):
  가장 먼저  (Always First)    — move priority ≥ 5
  상대보다 먼저 (Before Opp.) — move priority 1–4
  기본 (Normal)               — move priority 0
  아무것도 없음 (Last)         — move priority ≤ −1

Switch actions always execute before move actions (treated as priority 99).

Within the same priority tier, speed (상승 and 강화 applied) determines order.
If Trick Room (트릭룸) is active, speed order is reversed.
Paralysis (마비) halves effective speed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tunaed_pokemon.engine.battle_state import BattlePokemonState
from tunaed_pokemon.engine.field_state import FieldStateManager
from tunaed_pokemon.models.pokemon import MoveData
from tunaed_pokemon.models.enums import StatusCondition
from tunaed_pokemon.utils.stat_calc import get_effective_stat


@dataclass
class ActionEntry:
    """One queued action by one Pokémon for this turn."""
    side: int                            # 1 or 2
    pokemon: BattlePokemonState
    action_type: str                     # "move" | "switch" | "flee"
    move: Optional[MoveData] = None      # set when action_type == "move"
    switch_target: Optional[int] = None  # party index when action_type == "switch"

    @property
    def move_priority(self) -> int:
        """Return the move's priority value (0 for non-move actions)."""
        if self.move is None or self.action_type != "move":
            return 0
        return self.move.priority


class ActionOrderResolver:
    """Sorts a list of ActionEntry objects into execution order.

    Sort key (descending — highest value runs first):
      1. Switches (virtual priority 99) before moves.
      2. Move priority value (higher = first).
      3. Effective speed (higher = first, reversed under Trick Room).
    """

    def sort(
        self,
        actions: list[ActionEntry],
        field: FieldStateManager,
    ) -> list[ActionEntry]:
        """Return a new list sorted into execution order for this turn."""
        trick_room = "트릭룸" in field.global_effects

        def sort_key(a: ActionEntry) -> tuple:
            # Switches always go first
            prio = 99 if a.action_type == "switch" else a.move_priority
            speed = self._effective_speed(a.pokemon)
            # Under Trick Room, slower Pokémon act first → negate speed
            if trick_room:
                speed = -speed
            return (prio, speed)

        return sorted(actions, key=sort_key, reverse=True)

    def _effective_speed(self, ps: BattlePokemonState) -> int:
        """Compute effective speed accounting for rank stages, 강화, and paralysis."""
        base  = ps.battle_stats.get("speed", 50)
        speed = get_effective_stat(base, ps.rank_stages.speed, ps.reinforcements.speed)
        if ps.status.major_status == StatusCondition.PARALYSIS.value:
            speed = speed // 2
        return max(1, speed)
