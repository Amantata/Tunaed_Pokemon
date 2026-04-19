"""Tests for the StatusEngine."""

from tunaed_pokemon.engine.status import (
    PokemonStatusState,
    StatusEngine,
)
from tunaed_pokemon.models.enums import StatusChange, StatusCondition


class TestPokemonStatusState:
    """Tests for individual Pokémon status management."""

    def test_apply_condition(self):
        state = PokemonStatusState()
        assert state.apply_condition(StatusCondition.BURN)
        assert state.condition == StatusCondition.BURN

    def test_cannot_stack_conditions(self):
        state = PokemonStatusState()
        state.apply_condition(StatusCondition.BURN)
        assert not state.apply_condition(StatusCondition.PARALYSIS)
        assert state.condition == StatusCondition.BURN

    def test_cure_condition(self):
        state = PokemonStatusState()
        state.apply_condition(StatusCondition.POISON)
        cured = state.cure_condition()
        assert cured == StatusCondition.POISON
        assert state.condition == StatusCondition.NONE

    def test_cure_when_none(self):
        state = PokemonStatusState()
        cured = state.cure_condition()
        assert cured == StatusCondition.NONE

    def test_apply_status_change(self):
        state = PokemonStatusState()
        assert state.apply_change(StatusChange.CONFUSION, turns=3)
        assert state.has_change(StatusChange.CONFUSION)

    def test_status_change_coexists_with_condition(self):
        state = PokemonStatusState()
        state.apply_condition(StatusCondition.BURN)
        state.apply_change(StatusChange.CONFUSION, turns=3)
        assert state.condition == StatusCondition.BURN
        assert state.has_change(StatusChange.CONFUSION)

    def test_remove_status_change(self):
        state = PokemonStatusState()
        state.apply_change(StatusChange.TAUNT, turns=3)
        assert state.remove_change(StatusChange.TAUNT)
        assert not state.has_change(StatusChange.TAUNT)
        assert not state.remove_change(StatusChange.TAUNT)

    def test_multiple_status_changes(self):
        state = PokemonStatusState()
        state.apply_change(StatusChange.CONFUSION)
        state.apply_change(StatusChange.TAUNT, turns=3)
        state.apply_change(StatusChange.LEECH_SEED)
        assert state.has_change(StatusChange.CONFUSION)
        assert state.has_change(StatusChange.TAUNT)
        assert state.has_change(StatusChange.LEECH_SEED)

    def test_tick_condition_expires(self):
        state = PokemonStatusState()
        state.apply_condition(StatusCondition.SLEEP, turns=1)
        result = state.tick()
        assert "condition_expired" in result
        assert state.condition == StatusCondition.NONE

    def test_tick_condition_decrements(self):
        state = PokemonStatusState()
        state.apply_condition(StatusCondition.SLEEP, turns=3)
        result = state.tick()
        assert "condition_expired" not in result
        assert state.condition == StatusCondition.SLEEP
        assert state.condition_turns == 2

    def test_tick_status_change_expires(self):
        state = PokemonStatusState()
        state.apply_change(StatusChange.TAUNT, turns=1)
        result = state.tick()
        assert "changes_expired" in result
        assert "도발" in result["changes_expired"]
        assert not state.has_change(StatusChange.TAUNT)

    def test_tick_indefinite_change_persists(self):
        state = PokemonStatusState()
        state.apply_change(StatusChange.LEECH_SEED, turns=None)
        result = state.tick()
        assert "changes_expired" not in result
        assert state.has_change(StatusChange.LEECH_SEED)

    def test_serialize_deserialize(self):
        state = PokemonStatusState()
        state.apply_condition(StatusCondition.TOXIC, turns=5)
        state.apply_change(StatusChange.CONFUSION, turns=3)
        state.apply_change(StatusChange.LEECH_SEED)

        d = state.to_dict()
        restored = PokemonStatusState.from_dict(d)

        assert restored.condition == StatusCondition.TOXIC
        assert restored.condition_turns == 5
        assert restored.has_change(StatusChange.CONFUSION)
        assert restored.has_change(StatusChange.LEECH_SEED)


class TestStatusEngine:
    """Tests for the multi-Pokémon StatusEngine."""

    def test_apply_condition_to_pokemon(self):
        engine = StatusEngine()
        assert engine.apply_condition(0, 0, StatusCondition.BURN)
        state = engine.get_state(0, 0)
        assert state.condition == StatusCondition.BURN

    def test_separate_pokemon_states(self):
        engine = StatusEngine()
        engine.apply_condition(0, 0, StatusCondition.BURN)
        engine.apply_condition(1, 0, StatusCondition.PARALYSIS)
        assert engine.get_state(0, 0).condition == StatusCondition.BURN
        assert engine.get_state(1, 0).condition == StatusCondition.PARALYSIS

    def test_sleep_count(self):
        engine = StatusEngine()
        engine.apply_condition(0, 0, StatusCondition.SLEEP, turns=3)
        engine.apply_condition(0, 1, StatusCondition.SLEEP, turns=2)
        assert engine.count_sleeping(0, 6) == 2

    def test_can_apply_sleep_under_limit(self):
        engine = StatusEngine()
        assert engine.can_apply_sleep(0, 6, max_sleep=2)
        engine.apply_condition(0, 0, StatusCondition.SLEEP, turns=3)
        assert engine.can_apply_sleep(0, 6, max_sleep=2)
        engine.apply_condition(0, 1, StatusCondition.SLEEP, turns=3)
        assert not engine.can_apply_sleep(0, 6, max_sleep=2)

    def test_cure_condition(self):
        engine = StatusEngine()
        engine.apply_condition(0, 0, StatusCondition.POISON)
        cured = engine.cure_condition(0, 0)
        assert cured == StatusCondition.POISON

    def test_apply_and_remove_change(self):
        engine = StatusEngine()
        engine.apply_change(0, 0, StatusChange.SUBSTITUTE)
        assert engine.get_state(0, 0).has_change(StatusChange.SUBSTITUTE)
        engine.remove_change(0, 0, StatusChange.SUBSTITUTE)
        assert not engine.get_state(0, 0).has_change(StatusChange.SUBSTITUTE)

    def test_tick_all(self):
        engine = StatusEngine()
        engine.apply_condition(0, 0, StatusCondition.SLEEP, turns=1)
        engine.apply_change(1, 0, StatusChange.TAUNT, turns=1)

        results = engine.tick_all()
        assert (0, 0) in results
        assert (1, 0) in results

    def test_serialize_deserialize(self):
        engine = StatusEngine()
        engine.apply_condition(0, 0, StatusCondition.BURN)
        engine.apply_change(0, 0, StatusChange.CONFUSION, turns=3)
        engine.apply_condition(1, 0, StatusCondition.PARALYSIS)

        d = engine.to_dict()
        restored = StatusEngine.from_dict(d)

        assert restored.get_state(0, 0).condition == StatusCondition.BURN
        assert restored.get_state(0, 0).has_change(StatusChange.CONFUSION)
        assert restored.get_state(1, 0).condition == StatusCondition.PARALYSIS
