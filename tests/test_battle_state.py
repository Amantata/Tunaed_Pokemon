"""Tests for BattleStateSnapshot and TurnHistory."""

import json

from tunaed_pokemon.engine.battle_state import (
    BattlePokemonState,
    BattleSideState,
    BattleStateSnapshot,
    TurnHistory,
)
from tunaed_pokemon.engine.events import BattleEvent, BattleEventType
from tunaed_pokemon.engine.field_state import FieldStateManager
from tunaed_pokemon.models.enums import Weather, Terrain, FieldEffect


class TestBattlePokemonState:
    """Tests for in-battle Pokémon state."""

    def test_default_state(self):
        state = BattlePokemonState()
        assert state.current_hp == 1
        assert state.is_fainted is False
        assert state.rank_stages["공격"] == 0
        assert state.reinforcements["공격"] == 1.0

    def test_rank_and_reinforcement_separate(self):
        """ST-02: rank stages and reinforcements are separate fields."""
        state = BattlePokemonState()
        state.rank_stages["공격"] = 2  # +2 rank stage (상승)
        state.reinforcements["공격"] = 1.5  # ×1.5 reinforcement (강화)
        assert state.rank_stages["공격"] == 2
        assert state.reinforcements["공격"] == 1.5

    def test_serialize_deserialize(self):
        state = BattlePokemonState(
            pokemon_id=1,
            species="리자몽",
            name="불꽃이",
            level=50,
            types=["불꽃", "비행"],
            max_hp=150,
            current_hp=100,
        )
        state.rank_stages["속도"] = 1
        state.reinforcements["공격"] = 2.0

        d = state.to_dict()
        restored = BattlePokemonState.from_dict(d)

        assert restored.species == "리자몽"
        assert restored.current_hp == 100
        assert restored.rank_stages["속도"] == 1
        assert restored.reinforcements["공격"] == 2.0

    def test_ability_change_tracking(self):
        """SK-04: ability changes are tracked."""
        state = BattlePokemonState()
        state.ability_name = "위협"
        state.original_ability_name = "위협"
        # Mid-battle ability change
        state.ability_name = "변환자재"
        assert state.ability_name != state.original_ability_name


class TestBattleSideState:
    """Tests for battle side state."""

    def test_active_pokemon(self):
        side = BattleSideState()
        p1 = BattlePokemonState(species="피카츄", is_active=True)
        p2 = BattlePokemonState(species="리자몽", is_active=False)
        side.pokemon = [p1, p2]
        assert len(side.active_pokemon) == 1
        assert side.active_pokemon[0].species == "피카츄"

    def test_all_fainted(self):
        side = BattleSideState()
        p1 = BattlePokemonState(is_fainted=True)
        p2 = BattlePokemonState(is_fainted=True)
        side.pokemon = [p1, p2]
        assert side.all_fainted

    def test_alive_pokemon(self):
        side = BattleSideState()
        p1 = BattlePokemonState(is_fainted=False)
        p2 = BattlePokemonState(is_fainted=True)
        p3 = BattlePokemonState(is_fainted=False)
        side.pokemon = [p1, p2, p3]
        assert len(side.alive_pokemon) == 2

    def test_serialize(self):
        side = BattleSideState(trainer_name="레드")
        side.pokemon = [BattlePokemonState(species="피카츄")]
        d = side.to_dict()
        restored = BattleSideState.from_dict(d)
        assert restored.trainer_name == "레드"
        assert len(restored.pokemon) == 1
        assert restored.pokemon[0].species == "피카츄"


class TestBattleStateSnapshot:
    """Tests for full battle state snapshot (B-01, B-04)."""

    def _make_snapshot(self) -> BattleStateSnapshot:
        """Create a sample snapshot for testing."""
        snap = BattleStateSnapshot(turn_number=3, is_double_battle=False)
        snap.side_a = BattleSideState(trainer_name="레드")
        snap.side_a.pokemon = [
            BattlePokemonState(species="피카츄", max_hp=100, current_hp=80, is_active=True),
            BattlePokemonState(species="리자몽", max_hp=150, current_hp=150),
        ]
        snap.side_b = BattleSideState(trainer_name="블루")
        snap.side_b.pokemon = [
            BattlePokemonState(species="거북왕", max_hp=160, current_hp=120, is_active=True),
        ]
        snap.field_state.set_weather(Weather.SUN, turns=3)
        return snap

    def test_get_side(self):
        snap = self._make_snapshot()
        assert snap.get_side(0).trainer_name == "레드"
        assert snap.get_side(1).trainer_name == "블루"

    def test_json_roundtrip(self):
        snap = self._make_snapshot()
        json_str = snap.to_json()
        restored = BattleStateSnapshot.from_json(json_str)
        assert restored.turn_number == 3
        assert restored.side_a.trainer_name == "레드"
        assert restored.field_state.weather == Weather.SUN

    def test_deep_copy(self):
        snap = self._make_snapshot()
        copy = snap.deep_copy()
        # Modify the copy
        copy.turn_number = 999
        copy.side_a.pokemon[0].current_hp = 0
        # Original is unchanged
        assert snap.turn_number == 3
        assert snap.side_a.pokemon[0].current_hp == 80

    def test_battle_ended_state(self):
        snap = BattleStateSnapshot()
        snap.battle_ended = True
        snap.winner_side = 0
        d = snap.to_dict()
        restored = BattleStateSnapshot.from_dict(d)
        assert restored.battle_ended is True
        assert restored.winner_side == 0


class TestTurnHistory:
    """Tests for Undo/Redo functionality (B-02)."""

    def test_push_and_current(self):
        history = TurnHistory()
        snap = BattleStateSnapshot(turn_number=0)
        history.push(snap)
        current = history.current_snapshot()
        assert current is not None
        assert current.turn_number == 0

    def test_undo_redo(self):
        history = TurnHistory()
        snap0 = BattleStateSnapshot(turn_number=0)
        snap1 = BattleStateSnapshot(turn_number=1)
        snap2 = BattleStateSnapshot(turn_number=2)

        history.push(snap0)
        history.push(snap1)
        history.push(snap2)

        assert history.current_index == 2
        assert history.can_undo
        assert not history.can_redo

        # Undo to turn 1
        state = history.undo()
        assert state is not None
        assert state.turn_number == 1
        assert history.can_undo
        assert history.can_redo

        # Undo to turn 0
        state = history.undo()
        assert state is not None
        assert state.turn_number == 0
        assert not history.can_undo

        # Redo to turn 1
        state = history.redo()
        assert state is not None
        assert state.turn_number == 1

    def test_undo_at_start_returns_none(self):
        history = TurnHistory()
        history.push(BattleStateSnapshot(turn_number=0))
        assert history.undo() is None

    def test_redo_at_end_returns_none(self):
        history = TurnHistory()
        history.push(BattleStateSnapshot(turn_number=0))
        assert history.redo() is None

    def test_push_after_undo_discards_future(self):
        history = TurnHistory()
        history.push(BattleStateSnapshot(turn_number=0))
        history.push(BattleStateSnapshot(turn_number=1))
        history.push(BattleStateSnapshot(turn_number=2))

        history.undo()  # Back to 1
        history.undo()  # Back to 0

        # Push new state - should discard turn 1 and 2
        history.push(BattleStateSnapshot(turn_number=10))
        assert history.current_index == 1
        assert not history.can_redo
        current = history.current_snapshot()
        assert current is not None
        assert current.turn_number == 10

    def test_event_log_per_turn(self):
        history = TurnHistory()
        events = [
            BattleEvent(event_type=BattleEventType.MOVE_USED, turn=0),
            BattleEvent(event_type=BattleEventType.DAMAGE_DEALT, turn=0),
        ]
        history.push(BattleStateSnapshot(turn_number=0), events)
        retrieved = history.get_events_for_turn(0)
        assert len(retrieved) == 2
        assert retrieved[0].event_type == BattleEventType.MOVE_USED

    def test_json_roundtrip(self):
        history = TurnHistory()
        history.push(
            BattleStateSnapshot(turn_number=0),
            [BattleEvent(event_type=BattleEventType.TURN_START, turn=0)],
        )
        history.push(
            BattleStateSnapshot(turn_number=1),
            [BattleEvent(event_type=BattleEventType.MOVE_USED, turn=1)],
        )

        json_str = history.to_json()
        restored = TurnHistory.from_json(json_str)

        assert restored.current_index == 1
        current = restored.current_snapshot()
        assert current is not None
        assert current.turn_number == 1
        events = restored.get_events_for_turn(0)
        assert len(events) == 1

    def test_deep_copy_isolation(self):
        """Ensure snapshots in history are deep-copied."""
        snap = BattleStateSnapshot(turn_number=0)
        snap.side_a.pokemon = [
            BattlePokemonState(species="피카츄", current_hp=100),
        ]
        history = TurnHistory()
        history.push(snap)

        # Modify original snapshot
        snap.side_a.pokemon[0].current_hp = 0

        # History should have the original value
        stored = history.current_snapshot()
        assert stored is not None
        assert stored.side_a.pokemon[0].current_hp == 100
