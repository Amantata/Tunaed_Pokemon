"""Turn pipeline — the 6-step turn execution engine (F-01, B-01–B-03).

Turn steps (CLAUDE.md §4.2 / Battle Flow):
  1. Start-of-turn processing
  2. Command input  (handled by UI; pipeline receives already-formed ActionEntry list)
  3. Action order determination
  4. Move / switch execution
  5. End-of-turn processing  (field effects tick)
  6. Turn-end effects: status / weather damage → drain → recovery
"""

from __future__ import annotations

from typing import Optional

from tunaed_pokemon.engine.action_order import ActionEntry, ActionOrderResolver
from tunaed_pokemon.engine.battle_state import BattlePokemonState, BattleStateSnapshot
from tunaed_pokemon.engine.damage_calc import DamageCalculator, DamageContext
from tunaed_pokemon.engine.events import EventBus
from tunaed_pokemon.engine.status import StatusEngine
from tunaed_pokemon.models.pokemon import MoveData
from tunaed_pokemon.models.enums import StatusCondition, Weather


class TurnPipeline:
    """Orchestrates one complete battle turn through the 6-step pipeline.

    Usage::

        pipeline = TurnPipeline(bus)
        new_state = pipeline.process_turn(state, actions, move_data)

    The returned snapshot is a *deep copy* of the input with all mutations applied.
    All battle events are emitted on the EventBus so that the UI / animation layer
    can consume them (B-03).
    """

    def __init__(self, bus: Optional[EventBus] = None) -> None:
        self._bus    = bus or EventBus()
        self._order  = ActionOrderResolver()
        self._damage = DamageCalculator()
        self._status = StatusEngine()

    # ── Public API ────────────────────────────────────────────────────────────

    def process_turn(
        self,
        state: BattleStateSnapshot,
        actions: list[ActionEntry],
        move_data: dict[str, MoveData],
    ) -> BattleStateSnapshot:
        """Process one complete turn and return a new (deep-copied) state."""
        state = state.deep_copy()
        if state.battle_over:
            return state

        state.turn_number += 1

        self._step1_start_of_turn(state)
        sorted_actions = self._step3_action_order(actions, state)
        self._step4_execute(state, sorted_actions, move_data)
        self._step5_end_of_turn(state)
        self._step6_turn_end_effects(state)
        self._finalize_battle_if_needed(state)

        return state

    # ── Step 1 — Start of turn ────────────────────────────────────────────────

    def _step1_start_of_turn(self, state: BattleStateSnapshot) -> None:
        self._log(state, f"═══ {state.turn_number}턴 시작 ═══")

    # ── Step 3 — Action order ─────────────────────────────────────────────────

    def _step3_action_order(
        self,
        actions: list[ActionEntry],
        state: BattleStateSnapshot,
    ) -> list[ActionEntry]:
        return self._order.sort(actions, state.field_state)

    # ── Step 4 — Execute ──────────────────────────────────────────────────────

    def _step4_execute(
        self,
        state: BattleStateSnapshot,
        actions: list[ActionEntry],
        move_data: dict[str, MoveData],
    ) -> None:
        for action in actions:
            if action.action_type == "switch":
                self._do_switch(state, action)
            elif action.action_type == "move":
                self._do_move(state, action, move_data)

    def _do_switch(self, state: BattleStateSnapshot, action: ActionEntry) -> None:
        side = state.side1 if action.side == 1 else state.side2
        target_idx = action.switch_target
        if target_idx is None:
            return
        if not (0 <= target_idx < len(side.pokemon_states)):
            return
        target = side.pokemon_states[target_idx]
        if target.is_fainted:
            return

        # Clear confusion on switch-out (persistent status conditions stay)
        if side.active_indices:
            outgoing = side.pokemon_states[side.active_indices[0]]
            self._status.on_switch_out(outgoing.status)

        side.active_indices = [target_idx]
        self._log(state, f"{action.pokemon.name}이(가) 돌아와! {target.name}, 나가!")

    def _do_move(
        self,
        state: BattleStateSnapshot,
        action: ActionEntry,
        move_data: dict[str, MoveData],
    ) -> None:
        attacker = action.pokemon
        if attacker.is_fainted:
            return
        move = action.move
        if move is None:
            return

        defender_side = state.side2 if action.side == 1 else state.side1
        defenders = defender_side.active_pokemon
        if not defenders:
            return
        defender = defenders[0]

        self._log(state, f"{attacker.name}이(가) 『{move.name}』을(를) 사용했다!")

        ctx = DamageContext(
            attacker=attacker,
            defender=defender,
            move=move,
            field=state.field_state,
        )
        result = self._damage.calculate(ctx)

        for msg in result.messages:
            self._log(state, msg)

        if result.final_damage > 0:
            defender.current_hp = max(0, defender.current_hp - result.final_damage)
            self._log(state, f"{defender.name}에게 {result.final_damage}의 데미지!")
            if defender.current_hp == 0:
                defender.is_fainted = True
                self._log(state, f"{defender.name}은(는) 쓰러졌다!")

    # ── Step 5 — End of turn (field tick) ─────────────────────────────────────

    def _step5_end_of_turn(self, state: BattleStateSnapshot) -> None:
        expired = state.field_state.tick()
        for msg in expired:
            self._log(state, msg)

    # ── Step 6 — Turn-end effects ─────────────────────────────────────────────

    def _step6_turn_end_effects(self, state: BattleStateSnapshot) -> None:
        """Apply status/weather damage, drain, and recovery for active Pokémon."""
        for side in (state.side1, state.side2):
            for ps in side.active_pokemon:
                if ps.is_fainted:
                    continue

                # Status end-of-turn damage (화상, 동상, 독, 맹독, …)
                dmg = self._status.end_of_turn_damage(ps.status, ps.max_hp)
                if dmg > 0:
                    ps.current_hp = max(0, ps.current_hp - dmg)
                    cond = ps.status.major_status or ""
                    self._log(state, f"{ps.name}은(는) {cond} 데미지를 받았다! (−{dmg}HP)")
                    if ps.current_hp == 0:
                        ps.is_fainted = True
                        self._log(state, f"{ps.name}은(는) 쓰러졌다!")
                        continue

                # Weather end-of-turn damage (모래바람, 싸라기눈/눈보라)
                weather_dmg = self._weather_damage(ps, state.field_state.weather)
                if weather_dmg > 0:
                    ps.current_hp = max(0, ps.current_hp - weather_dmg)
                    self._log(state, f"날씨 데미지! {ps.name} (−{weather_dmg}HP)")
                    if ps.current_hp == 0:
                        ps.is_fainted = True
                        self._log(state, f"{ps.name}은(는) 쓰러졌다!")

    def _weather_damage(self, ps: BattlePokemonState, weather: str) -> int:
        """Return end-of-turn weather damage (1/16 of max HP, or 0 if immune)."""
        if weather == Weather.SANDSTORM.value:
            immune = {"바위", "땅", "강철"}
            if ps.type1 in immune or (ps.type2 and ps.type2 in immune):
                return 0
            return max(1, ps.max_hp // 16)

        if weather in (Weather.HAIL.value, Weather.SNOWSTORM.value):
            if ps.type1 == "얼음" or ps.type2 == "얼음":
                return 0
            return max(1, ps.max_hp // 16)

        return 0

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _finalize_battle_if_needed(self, state: BattleStateSnapshot) -> None:
        """Finalize terminal state when one or both sides have all Pokémon fainted."""
        side1_all_fainted = state.side1.is_all_fainted
        side2_all_fainted = state.side2.is_all_fainted
        if not side1_all_fainted and not side2_all_fainted:
            return

        state.battle_over = True
        if side1_all_fainted and side2_all_fainted:
            state.winner_side = None
            self._log(state, "양측의 포켓몬이 모두 쓰러졌다! 무승부!")
            return

        winner_side = 2 if side1_all_fainted else 1
        state.winner_side = winner_side
        winner_state = state.side1 if winner_side == 1 else state.side2
        winner_name = winner_state.trainer_name
        self._log(state, f"배틀 종료! 승자: {winner_name} (플레이어 {winner_side})!")

    def _log(self, state: BattleStateSnapshot, msg: str) -> None:
        state.add_log(msg)
        self._bus.emit_message(msg)
