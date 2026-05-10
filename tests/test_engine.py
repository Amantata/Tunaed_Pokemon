"""Tests for engine modules: battle_state, field_state, status, events."""

from __future__ import annotations

import pytest

from tunaed_pokemon.engine.battle_state import (
    RankStages, Reinforcements, BattlePokemonState,
    BattleSideState, BattleStateSnapshot, TurnHistory,
)
from tunaed_pokemon.engine.events import EventBus, BattleEvent, BattleEventType
from tunaed_pokemon.engine.field_state import FieldStateManager, SideFieldState
from tunaed_pokemon.engine.status import StatusEngine, StatusState
from tunaed_pokemon.models.enums import StatusCondition, Weather, Terrain, SpecialField


# ── RankStages ────────────────────────────────────────────────────────────────

class TestRankStages:
    def test_change_clamps_at_plus_6(self):
        rs = RankStages()
        rs.change("attack", 10)
        assert rs.attack == 6

    def test_change_clamps_at_minus_6(self):
        rs = RankStages()
        rs.change("attack", -10)
        assert rs.attack == -6

    def test_change_returns_actual_applied(self):
        rs = RankStages()
        rs.attack = 5
        actual = rs.change("attack", 3)
        assert actual == 1   # only 1 more step allowed
        assert rs.attack == 6

    def test_round_trip_serialisation(self):
        rs = RankStages(attack=2, defense=-1, speed=3)
        assert RankStages.from_dict(rs.to_dict()).attack == 2

    def test_reset(self):
        rs = RankStages(attack=3, speed=-2)
        rs.reset()
        assert rs.attack == 0
        assert rs.speed == 0


# ── Reinforcements ────────────────────────────────────────────────────────────

class TestReinforcements:
    def test_default_is_1(self):
        r = Reinforcements()
        assert r.attack == 1.0

    def test_reset(self):
        r = Reinforcements(attack=2.0, speed=0.5)
        r.reset()
        assert r.attack == 1.0
        assert r.speed == 1.0

    def test_round_trip(self):
        r = Reinforcements(sp_atk=1.5)
        r2 = Reinforcements.from_dict(r.to_dict())
        assert r2.sp_atk == 1.5

    def test_strictly_separate_from_rank_stages(self):
        """ST-02: reinforcement and rank stage must be independent objects."""
        rs = RankStages(attack=2)
        r = Reinforcements(attack=2.0)
        # They must not share data — changing one does not affect the other
        rs.reset()
        assert r.attack == 2.0   # reinforcement unchanged


# ── BattleStateSnapshot ───────────────────────────────────────────────────────

class TestBattleStateSnapshot:
    def _make_snapshot(self) -> BattleStateSnapshot:
        ps = BattlePokemonState(
            pokemon_id="p1", name="テスト", current_hp=50, max_hp=100,
        )
        side = BattleSideState(
            trainer_id=None, trainer_name="P1", party_id=None,
            pokemon_states=[ps], active_indices=[0],
        )
        return BattleStateSnapshot(turn_number=1, side1=side)

    def test_deep_copy_is_independent(self):
        snap = self._make_snapshot()
        copy = snap.deep_copy()
        copy.side1.pokemon_states[0].current_hp = 0
        assert snap.side1.pokemon_states[0].current_hp == 50

    def test_round_trip_serialisation(self):
        snap = self._make_snapshot()
        snap.battle_over = True
        snap.winner_side = 1
        d = snap.to_dict()
        snap2 = BattleStateSnapshot.from_dict(d)
        assert snap2.turn_number == 1
        assert snap2.side1.pokemon_states[0].name == "テスト"
        assert snap2.battle_over is True
        assert snap2.winner_side == 1

    def test_hp_fraction(self):
        ps = BattlePokemonState(pokemon_id="x", name="X", current_hp=25, max_hp=100)
        assert ps.hp_fraction == pytest.approx(0.25)

    def test_is_all_fainted(self):
        ps = BattlePokemonState(pokemon_id="x", name="X", current_hp=0, max_hp=100, is_fainted=True)
        side = BattleSideState(trainer_id=None, trainer_name="P", party_id=None, pokemon_states=[ps])
        assert side.is_all_fainted


# ── TurnHistory ───────────────────────────────────────────────────────────────

class TestTurnHistory:
    def test_undo_redo(self):
        h = TurnHistory()
        s1 = BattleStateSnapshot(turn_number=1)
        s2 = BattleStateSnapshot(turn_number=2)
        h.push(s1)
        h.push(s2)
        undone = h.undo()
        assert undone.turn_number == 1
        redone = h.redo()
        assert redone.turn_number == 2

    def test_cannot_undo_past_start(self):
        h = TurnHistory()
        h.push(BattleStateSnapshot(turn_number=0))
        assert not h.can_undo()

    def test_push_discards_future(self):
        h = TurnHistory()
        h.push(BattleStateSnapshot(turn_number=1))
        h.push(BattleStateSnapshot(turn_number=2))
        h.undo()
        h.push(BattleStateSnapshot(turn_number=3))
        assert not h.can_redo()

    def test_round_trip(self):
        h = TurnHistory()
        h.push(BattleStateSnapshot(turn_number=5))
        h2 = TurnHistory.from_dict(h.to_dict())
        assert h2.current.turn_number == 5


# ── EventBus ─────────────────────────────────────────────────────────────────

class TestEventBus:
    def test_emit_calls_handler(self):
        bus = EventBus()
        received: list[BattleEvent] = []
        bus.subscribe(BattleEventType.MESSAGE, received.append)
        bus.emit_message("hello")
        assert len(received) == 1
        assert received[0].message == "hello"

    def test_unsubscribe(self):
        bus = EventBus()
        received: list[BattleEvent] = []
        bus.subscribe(BattleEventType.MESSAGE, received.append)
        bus.unsubscribe(BattleEventType.MESSAGE, received.append)
        bus.emit_message("hello")
        assert len(received) == 0

    def test_event_log_accumulates(self):
        bus = EventBus()
        bus.emit_message("a")
        bus.emit_message("b")
        assert len(bus.event_log) == 2

    def test_export_log(self):
        bus = EventBus()
        bus.emit_message("x")
        exported = bus.export_log()
        assert exported[0]["event_type"] == BattleEventType.MESSAGE.value


# ── FieldStateManager ─────────────────────────────────────────────────────────

class TestFieldStateManager:
    def test_set_weather(self):
        fs = FieldStateManager()
        fs.set_weather(Weather.RAIN, turns=5)
        assert fs.weather == Weather.RAIN.value
        assert fs.weather_turns == 5

    def test_terrain_separate_from_special_field(self):
        """FE-04 「필드」(Terrain) must be strictly separate from FE-06 《필드》(SpecialField)."""
        fs = FieldStateManager()
        fs.set_terrain(Terrain.ELECTRIC, turns=5)
        fs.set_special_field(SpecialField.SHADOW_REALM)
        assert fs.terrain == Terrain.ELECTRIC.value
        assert fs.special_field == SpecialField.SHADOW_REALM.value
        # Changing terrain must not affect special_field and vice versa
        fs.set_terrain(Terrain.NONE)
        assert fs.special_field == SpecialField.SHADOW_REALM.value

    def test_tick_decrements_weather(self):
        fs = FieldStateManager()
        fs.set_weather(Weather.SUNNY, turns=2)
        fs.tick()
        assert fs.weather_turns == 1
        fs.tick()
        assert fs.weather == Weather.NONE.value

    def test_global_effect_tick(self):
        fs = FieldStateManager()
        fs.set_global_effect("트릭룸", 3)
        fs.tick()
        assert fs.global_effects["트릭룸"] == 2

    def test_barrier_tick(self):
        fs = FieldStateManager()
        fs.side1.set_barrier("리플렉터", 2)
        fs.tick()
        assert "리플렉터" in fs.side1.barriers
        fs.tick()
        assert "리플렉터" not in fs.side1.barriers

    def test_round_trip(self):
        fs = FieldStateManager()
        fs.set_weather(Weather.RAIN, turns=3)
        fs2 = FieldStateManager.from_dict(fs.to_dict())
        assert fs2.weather == Weather.RAIN.value
        assert fs2.weather_turns == 3


# ── StatusEngine ─────────────────────────────────────────────────────────────

class TestStatusEngine:
    def test_apply_major_status(self):
        se = StatusEngine()
        state = StatusState()
        assert se.apply_major_status(state, StatusCondition.BURN)
        assert state.major_status == StatusCondition.BURN.value

    def test_cannot_apply_second_major_status(self):
        se = StatusEngine()
        state = StatusState()
        se.apply_major_status(state, StatusCondition.BURN)
        assert not se.apply_major_status(state, StatusCondition.PARALYSIS)
        assert state.major_status == StatusCondition.BURN.value

    def test_confusion_independent_of_major(self):
        """Confusion can coexist with a major status condition."""
        se = StatusEngine()
        state = StatusState()
        se.apply_major_status(state, StatusCondition.BURN)
        se.apply_confusion(state)
        assert state.major_status == StatusCondition.BURN.value
        assert state.is_confused

    def test_bad_poison_counter(self):
        se = StatusEngine()
        state = StatusState()
        se.apply_major_status(state, StatusCondition.BAD_POISON)
        dmg1 = se.end_of_turn_damage(state, 160)
        dmg2 = se.end_of_turn_damage(state, 160)
        assert dmg2 > dmg1   # counter increases each turn

    def test_burn_damage(self):
        se = StatusEngine()
        state = StatusState(major_status=StatusCondition.BURN.value)
        assert se.end_of_turn_damage(state, 160) == 20   # 160/8

    def test_switch_out_clears_confusion(self):
        se = StatusEngine()
        state = StatusState(major_status=StatusCondition.BURN.value, is_confused=True)
        se.on_switch_out(state)
        assert not state.is_confused
        assert state.major_status == StatusCondition.BURN.value   # kept
