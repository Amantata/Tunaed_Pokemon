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
from tunaed_pokemon.engine.battle_state import (
    BattleEventHistory,
    BattlePokemonState,
    BattleStateSnapshot,
)
from tunaed_pokemon.engine.damage_calc import DamageCalculator, DamageContext
from tunaed_pokemon.engine.events import BattleEvent, BattleEventType, EventBus
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

    When ``event_history`` is provided, a (state, event) pair is recorded before
    each atomic state mutation, enabling per-event undo/redo (B-02).
    """

    def __init__(
        self,
        bus: Optional[EventBus] = None,
        event_history: Optional[BattleEventHistory] = None,
    ) -> None:
        self._bus    = bus or EventBus()
        self._order  = ActionOrderResolver()
        self._damage = DamageCalculator()
        self._status = StatusEngine()
        self._event_history: Optional[BattleEventHistory] = event_history

    # ── Public API ────────────────────────────────────────────────────────────

    def set_event_history(self, history: BattleEventHistory) -> None:
        """Attach a BattleEventHistory for per-event undo tracking (B-02)."""
        self._event_history = history

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
        self._log(state, f"═══ {state.turn_number}턴 시작 ═══",
                  BattleEventType.TURN_START)

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

        msg = f"{action.pokemon.name}이(가) 돌아와! {target.name}, 나가!"
        event = BattleEvent(BattleEventType.POKEMON_SWITCHED, side=action.side,
                            data={"from": action.pokemon.name, "to": target.name},
                            message=msg)
        self._record_and_emit(state, event)
        side.active_indices = [target_idx]
        state.add_log(msg)

    def _do_move(
        self,
        state: BattleStateSnapshot,
        action: ActionEntry,
        move_data: dict[str, MoveData],
    ) -> None:
        attacker_side = state.side1 if action.side == 1 else state.side2
        attackers = attacker_side.active_pokemon
        if not attackers:
            return
        attacker = attackers[0]
        if attacker.is_fainted:
            return
        move = action.move
        if move is None:
            return

        # Deduct PP if tracked
        if move_id := (move.id if move else None):
            try:
                idx = attacker.move_ids.index(move_id)
                if idx < len(attacker.pp_remaining) and attacker.pp_remaining[idx] > 0:
                    attacker.pp_remaining[idx] -= 1
            except ValueError:
                pass

        defender_side = state.side2 if action.side == 1 else state.side1
        defenders = defender_side.active_pokemon
        if not defenders:
            return
        defender = defenders[0]

        move_msg = f"{attacker.name}이(가) 『{move.name}』을(를) 사용했다!"
        move_event = BattleEvent(BattleEventType.MOVE_USED, side=action.side,
                                 data={"pokemon": attacker.name, "move": move.name},
                                 message=move_msg)
        self._record_and_emit(state, move_event)
        state.add_log(move_msg)

        ctx = DamageContext(
            attacker=attacker,
            defender=defender,
            move=move,
            field=state.field_state,
        )
        result = self._damage.calculate(ctx)

        for msg in result.messages:
            state.add_log(msg)
            self._bus.emit_message(msg)

        if result.final_damage > 0:
            dmg_event = BattleEvent(BattleEventType.DAMAGE_DEALT, side=action.side,
                                    data={"target": defender.name,
                                          "damage": result.final_damage},
                                    message=f"{defender.name}에게 {result.final_damage}의 데미지!")
            self._record_and_emit(state, dmg_event)
            defender.current_hp = max(0, defender.current_hp - result.final_damage)
            state.add_log(dmg_event.message)
            if defender.current_hp == 0:
                defender.is_fainted = True
                faint_msg = f"{defender.name}은(는) 쓰러졌다!"
                faint_event = BattleEvent(BattleEventType.POKEMON_FAINTED,
                                          side=(2 if action.side == 1 else 1),
                                          data={"pokemon": defender.name},
                                          message=faint_msg)
                self._record_and_emit(state, faint_event)
                state.add_log(faint_msg)

    # ── Step 5 — End of turn (field tick) ─────────────────────────────────────

    def _step5_end_of_turn(self, state: BattleStateSnapshot) -> None:
        expired = state.field_state.tick()
        for msg in expired:
            self._log(state, msg, BattleEventType.FIELD_CHANGED)

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
                    cond = ps.status.major_status or ""
                    msg = f"{ps.name}은(는) {cond} 데미지를 받았다! (−{dmg}HP)"
                    evt = BattleEvent(BattleEventType.HP_CHANGED,
                                     data={"pokemon": ps.name, "delta": -dmg},
                                     message=msg)
                    self._record_and_emit(state, evt)
                    ps.current_hp = max(0, ps.current_hp - dmg)
                    state.add_log(msg)
                    if ps.current_hp == 0:
                        ps.is_fainted = True
                        faint_msg = f"{ps.name}은(는) 쓰러졌다!"
                        state.add_log(faint_msg)
                        self._bus.emit_message(faint_msg)
                        continue

                # Weather end-of-turn damage (모래바람, 싸라기눈/눈보라)
                weather_dmg = self._weather_damage(ps, state.field_state.weather)
                if weather_dmg > 0:
                    msg = f"날씨 데미지! {ps.name} (−{weather_dmg}HP)"
                    evt = BattleEvent(BattleEventType.HP_CHANGED,
                                     data={"pokemon": ps.name, "delta": -weather_dmg},
                                     message=msg)
                    self._record_and_emit(state, evt)
                    ps.current_hp = max(0, ps.current_hp - weather_dmg)
                    state.add_log(msg)
                    if ps.current_hp == 0:
                        ps.is_fainted = True
                        faint_msg = f"{ps.name}은(는) 쓰러졌다!"
                        state.add_log(faint_msg)
                        self._bus.emit_message(faint_msg)

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
            self._log(state, "양측의 포켓몬이 모두 쓰러졌다! 무승부!",
                      BattleEventType.BATTLE_END)
            return

        winner_side = 2 if side1_all_fainted else 1
        state.winner_side = winner_side
        winner_state = state.side1 if winner_side == 1 else state.side2
        winner_name = winner_state.trainer_name
        self._log(state, f"배틀 종료! 승자: {winner_name} (플레이어 {winner_side})!",
                  BattleEventType.BATTLE_END)

    def _record_and_emit(
        self, state: BattleStateSnapshot, event: BattleEvent
    ) -> None:
        """Record state+event pair to history (if attached) then emit on bus."""
        if self._event_history is not None:
            self._event_history.record(state, event)
        self._bus.emit(event)

    def _log(
        self,
        state: BattleStateSnapshot,
        msg: str,
        event_type: BattleEventType = BattleEventType.MESSAGE,
    ) -> None:
        state.add_log(msg)
        event = BattleEvent(event_type, message=msg)
        self._record_and_emit(state, event)
