"""Tests for the battle engine core: TypeChart, DamageCalculator,
ActionOrderResolver, and TurnPipeline."""

from __future__ import annotations

import math
import pytest

from tunaed_pokemon.engine.type_chart import get_effectiveness, get_combined_effectiveness
from tunaed_pokemon.engine.damage_calc import DamageCalculator, DamageContext, DamageResult
from tunaed_pokemon.engine.action_order import ActionEntry, ActionOrderResolver
from tunaed_pokemon.engine.turn_pipeline import TurnPipeline
from tunaed_pokemon.engine.battle_state import (
    BattlePokemonState,
    BattleSideState,
    BattleStateSnapshot,
    RankStages,
    Reinforcements,
)
from tunaed_pokemon.engine.field_state import FieldStateManager
from tunaed_pokemon.models.pokemon import MoveData
from tunaed_pokemon.models.enums import BattleCategory, Weather, Terrain, StatusCondition


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_pokemon(
    name: str = "테스트",
    type1: str = "노말",
    type2: str | None = None,
    attack: int = 100,
    defense: int = 100,
    sp_atk: int = 100,
    sp_def: int = 100,
    speed: int = 100,
    hp: int = 200,
    level: int = 50,
) -> BattlePokemonState:
    return BattlePokemonState(
        pokemon_id="test",
        name=name,
        current_hp=hp,
        max_hp=hp,
        level=level,
        type1=type1,
        type2=type2,
        battle_stats={
            "hp": hp, "attack": attack, "defense": defense,
            "sp_atk": sp_atk, "sp_def": sp_def, "speed": speed,
        },
    )


def _make_move(
    name: str = "기술",
    type_: str = "노말",
    category: str = "물리",
    power: int = 80,
    priority: int = 0,
) -> MoveData:
    return MoveData(
        id="m1",
        name=name,
        type=type_,
        category=category,
        power=power,
        priority=priority,
    )


def _make_snapshot(p1: BattlePokemonState, p2: BattlePokemonState) -> BattleStateSnapshot:
    side1 = BattleSideState(
        trainer_id=None, trainer_name="P1", party_id=None,
        pokemon_states=[p1], active_indices=[0],
    )
    side2 = BattleSideState(
        trainer_id=None, trainer_name="P2", party_id=None,
        pokemon_states=[p2], active_indices=[0],
    )
    return BattleStateSnapshot(side1=side1, side2=side2)


# ── TypeChart ─────────────────────────────────────────────────────────────────

class TestTypeChart:
    def test_super_effective(self):
        assert get_effectiveness("불꽃", "풀") == pytest.approx(2.0)

    def test_not_very_effective(self):
        assert get_effectiveness("불꽃", "물") == pytest.approx(0.5)

    def test_immune(self):
        assert get_effectiveness("노말", "고스트") == pytest.approx(0.0)

    def test_neutral(self):
        assert get_effectiveness("노말", "노말") == pytest.approx(1.0)

    def test_unknown_type_defaults_to_1(self):
        assert get_effectiveness("???", "노말") == pytest.approx(1.0)

    def test_dual_type_super_effective(self):
        # Water vs Fire/Rock = 2×2 = 4
        assert get_combined_effectiveness("물", "불꽃", "바위") == pytest.approx(4.0)

    def test_dual_type_cancel(self):
        # Electric vs Ground/Flying: Ground immune (0) → result 0
        assert get_combined_effectiveness("전기", "땅", "비행") == pytest.approx(0.0)

    def test_dual_type_no_second_type(self):
        assert get_combined_effectiveness("불꽃", "풀", None) == pytest.approx(2.0)

    def test_fairy_vs_dragon_immune(self):
        assert get_effectiveness("드래곤", "페어리") == pytest.approx(0.0)

    def test_ghost_vs_normal_immune(self):
        assert get_effectiveness("고스트", "노말") == pytest.approx(0.0)

    def test_fighting_vs_ghost_immune(self):
        assert get_effectiveness("격투", "고스트") == pytest.approx(0.0)

    def test_steel_vs_fairy_super(self):
        assert get_effectiveness("강철", "페어리") == pytest.approx(2.0)

    def test_all_18_types_have_entries(self):
        types = [
            "노말", "불꽃", "물", "전기", "풀", "얼음", "격투", "독",
            "땅", "비행", "에스퍼", "벌레", "바위", "고스트", "드래곤",
            "악", "강철", "페어리",
        ]
        # Every type must return a valid multiplier against every other type
        for atk in types:
            for def_ in types:
                m = get_effectiveness(atk, def_)
                assert m in (0.0, 0.5, 1.0, 2.0), f"Bad multiplier {atk}→{def_}: {m}"


# ── DamageCalculator ──────────────────────────────────────────────────────────

class TestDamageCalculator:
    def _calc(self, ctx: DamageContext) -> DamageResult:
        ctx.apply_random = False  # deterministic
        return DamageCalculator().calculate(ctx)

    def test_physical_deal_damage(self):
        attacker = _make_pokemon(attack=100)
        defender = _make_pokemon(defense=100, hp=300)
        move     = _make_move(type_="노말", category="물리", power=80)
        ctx = DamageContext(attacker=attacker, defender=defender, move=move)
        result = self._calc(ctx)
        assert result.final_damage > 0
        assert not result.is_immune

    def test_special_deal_damage(self):
        attacker = _make_pokemon(sp_atk=100)
        defender = _make_pokemon(sp_def=100, hp=300)
        move     = _make_move(type_="불꽃", category="특수", power=90)
        ctx = DamageContext(attacker=attacker, defender=defender, move=move)
        result = self._calc(ctx)
        assert result.final_damage > 0

    def test_immune_returns_zero(self):
        attacker = _make_pokemon(type1="노말")
        defender = _make_pokemon(type1="고스트")
        move     = _make_move(type_="노말", category="물리", power=80)
        ctx = DamageContext(attacker=attacker, defender=defender, move=move)
        result = self._calc(ctx)
        assert result.is_immune
        assert result.final_damage == 0
        assert "효과가 없다" in result.messages[0]

    def test_stab_applies(self):
        # Same-type attacker should deal more damage than non-STAB
        attacker_stab = _make_pokemon(type1="불꽃", attack=100)
        attacker_nonstab = _make_pokemon(type1="노말", attack=100)
        defender = _make_pokemon(hp=500)
        move = _make_move(type_="불꽃", category="물리", power=80)

        ctx_stab    = DamageContext(attacker=attacker_stab,    defender=defender, move=move)
        ctx_nonstab = DamageContext(attacker=attacker_nonstab, defender=defender, move=move)
        r_stab    = self._calc(ctx_stab)
        r_nonstab = self._calc(ctx_nonstab)

        assert r_stab.stab_mult == pytest.approx(1.5)
        assert r_nonstab.stab_mult == pytest.approx(1.0)
        assert r_stab.final_damage > r_nonstab.final_damage

    def test_critical_hit(self):
        attacker = _make_pokemon(type1="불꽃", attack=100)   # type: 불꽃
        defender = _make_pokemon(defense=100)
        # Use water move — NOT same type as attacker → no STAB, clean ×2 ratio
        move     = _make_move(type_="물", category="물리", power=80)
        ctx_normal = DamageContext(attacker=attacker, defender=defender, move=move,
                                   is_critical=False)
        ctx_crit   = DamageContext(attacker=attacker, defender=defender, move=move,
                                   is_critical=True)
        normal = self._calc(ctx_normal).final_damage
        crit   = self._calc(ctx_crit).final_damage
        assert crit == normal * 2

    def test_st02_rank_stage_and_reinforcement_independent(self):
        """ST-02: applying a rank stage must not affect the reinforcement and vice versa."""
        attacker = _make_pokemon(attack=100)
        defender = _make_pokemon(defense=100)
        move     = _make_move(power=80)

        # Baseline
        ctx_base = DamageContext(attacker=attacker, defender=defender, move=move)
        base_dmg = self._calc(ctx_base).final_damage

        # Add rank stage +1 to attacker only
        atk_with_stage = _make_pokemon(attack=100)
        atk_with_stage.rank_stages.attack = 1
        ctx_stage = DamageContext(attacker=atk_with_stage, defender=defender, move=move)
        stage_dmg = self._calc(ctx_stage).final_damage

        # Add reinforcement ×1.5 to attacker only
        atk_with_reinf = _make_pokemon(attack=100)
        atk_with_reinf.reinforcements.attack = 1.5
        ctx_reinf = DamageContext(attacker=atk_with_reinf, defender=defender, move=move)
        reinf_dmg = self._calc(ctx_reinf).final_damage

        # Both should be higher than baseline, but differ from each other
        assert stage_dmg > base_dmg
        assert reinf_dmg > base_dmg
        # Stage +1 multiplier = 1.5, reinforcement ×1.5 → same ratio here
        # key test: stage_dmg and reinf_dmg should be equal when ratio is the same
        assert stage_dmg == reinf_dmg

    def test_status_move_no_damage(self):
        attacker = _make_pokemon()
        defender = _make_pokemon()
        move = MoveData(id="m_status", name="상태이상기", type="노말",
                        category=BattleCategory.STATUS.value, power=None)
        ctx = DamageContext(attacker=attacker, defender=defender, move=move)
        result = self._calc(ctx)
        assert result.final_damage == 0

    def test_weather_fire_in_sun(self):
        fs = FieldStateManager()
        fs.set_weather(Weather.SUNNY, turns=5)
        attacker = _make_pokemon(type1="불꽃", sp_atk=100)
        defender = _make_pokemon(sp_def=100)
        move     = _make_move(type_="불꽃", category="특수", power=90)
        ctx = DamageContext(attacker=attacker, defender=defender, move=move, field=fs)
        r = self._calc(ctx)
        assert r.weather_mult == pytest.approx(1.5)

    def test_weather_water_in_rain(self):
        fs = FieldStateManager()
        fs.set_weather(Weather.RAIN, turns=5)
        attacker = _make_pokemon(type1="물", sp_atk=100)
        defender = _make_pokemon(sp_def=100)
        move     = _make_move(type_="물", category="특수", power=90)
        ctx = DamageContext(attacker=attacker, defender=defender, move=move, field=fs)
        r = self._calc(ctx)
        assert r.weather_mult == pytest.approx(1.5)


# ── ActionOrderResolver ───────────────────────────────────────────────────────

class TestActionOrderResolver:
    def _resolver(self):
        return ActionOrderResolver()

    def _field(self, trick_room: bool = False) -> FieldStateManager:
        fs = FieldStateManager()
        if trick_room:
            fs.set_global_effect("트릭룸", 5)
        return fs

    def test_faster_pokemon_acts_first(self):
        fast  = _make_pokemon("빠른", speed=200)
        slow  = _make_pokemon("느린",  speed=50)
        move  = _make_move()
        a_fast = ActionEntry(side=1, pokemon=fast, action_type="move", move=move)
        a_slow = ActionEntry(side=2, pokemon=slow, action_type="move", move=move)
        result = self._resolver().sort([a_slow, a_fast], self._field())
        assert result[0].pokemon.name == "빠른"
        assert result[1].pokemon.name == "느린"

    def test_higher_priority_acts_first_regardless_of_speed(self):
        fast   = _make_pokemon("빠른", speed=300)
        slow   = _make_pokemon("느린",  speed=10)
        quick  = _make_move(priority=1)   # 상대보다 먼저
        normal = _make_move(priority=0)
        a_fast = ActionEntry(side=1, pokemon=fast, action_type="move", move=normal)
        a_slow = ActionEntry(side=2, pokemon=slow, action_type="move", move=quick)
        result = self._resolver().sort([a_fast, a_slow], self._field())
        assert result[0].pokemon.name == "느린"   # higher priority wins

    def test_trick_room_reverses_speed(self):
        fast = _make_pokemon("빠른", speed=200)
        slow = _make_pokemon("느린",  speed=50)
        move = _make_move()
        a_fast = ActionEntry(side=1, pokemon=fast, action_type="move", move=move)
        a_slow = ActionEntry(side=2, pokemon=slow, action_type="move", move=move)
        result = self._resolver().sort([a_fast, a_slow], self._field(trick_room=True))
        assert result[0].pokemon.name == "느린"   # TR reverses order

    def test_switch_before_move(self):
        p1 = _make_pokemon("p1")
        p2 = _make_pokemon("p2")
        move_action   = ActionEntry(side=1, pokemon=p1, action_type="move",   move=_make_move())
        switch_action = ActionEntry(side=2, pokemon=p2, action_type="switch", switch_target=1)
        result = self._resolver().sort([move_action, switch_action], self._field())
        assert result[0].action_type == "switch"

    def test_paralysis_halves_speed(self):
        from tunaed_pokemon.engine.status import StatusState
        fast = _make_pokemon("빠른", speed=200)
        slow = _make_pokemon("느린",  speed=120)
        # Make "fast" paralyzed → effective speed 100 → slower than "느린" (120)
        fast.status = StatusState(major_status=StatusCondition.PARALYSIS.value)
        move = _make_move()
        a_fast = ActionEntry(side=1, pokemon=fast, action_type="move", move=move)
        a_slow = ActionEntry(side=2, pokemon=slow, action_type="move", move=move)
        result = self._resolver().sort([a_fast, a_slow], self._field())
        assert result[0].pokemon.name == "느린"


# ── TurnPipeline ──────────────────────────────────────────────────────────────

class TestTurnPipeline:
    def _make_state(self, p1_hp: int = 200, p2_hp: int = 200) -> BattleStateSnapshot:
        p1 = _make_pokemon("공격자", hp=p1_hp, attack=150, speed=100)
        p2 = _make_pokemon("수비자", hp=p2_hp, defense=50,  speed=50)
        return _make_snapshot(p1, p2)

    def test_turn_number_increments(self):
        state  = self._make_state()
        pipe   = TurnPipeline()
        new    = pipe.process_turn(state, [], {})
        assert new.turn_number == 1

    def test_move_deals_damage(self):
        state = self._make_state(p2_hp=500)
        p1    = state.side1.pokemon_states[0]
        p2    = state.side2.pokemon_states[0]
        move  = _make_move(type_="노말", category="물리", power=80)
        action = ActionEntry(side=1, pokemon=p1, action_type="move", move=move)
        pipe  = TurnPipeline()
        new   = pipe.process_turn(state, [action], {"m1": move})
        assert new.side2.pokemon_states[0].current_hp < 500

    def test_fainted_pokemon_cannot_act(self):
        state = self._make_state()
        p1    = state.side1.pokemon_states[0]
        p1.is_fainted = True
        move   = _make_move(power=80)
        action = ActionEntry(side=1, pokemon=p1, action_type="move", move=move)
        pipe   = TurnPipeline()
        new    = pipe.process_turn(state, [action], {"m1": move})
        # Defender should be untouched since attacker is fainted
        assert new.side2.pokemon_states[0].current_hp == 200

    def test_switch_action(self):
        p1a = _make_pokemon("선발", speed=100)
        p1b = _make_pokemon("후발", speed=80)
        side1 = BattleSideState(
            trainer_id=None, trainer_name="P1", party_id=None,
            pokemon_states=[p1a, p1b], active_indices=[0],
        )
        p2 = _make_pokemon("상대")
        side2 = BattleSideState(
            trainer_id=None, trainer_name="P2", party_id=None,
            pokemon_states=[p2], active_indices=[0],
        )
        state = BattleStateSnapshot(side1=side1, side2=side2)
        switch = ActionEntry(side=1, pokemon=p1a, action_type="switch", switch_target=1)
        pipe   = TurnPipeline()
        new    = pipe.process_turn(state, [switch], {})
        assert new.side1.active_indices == [1]

    def test_original_state_unchanged(self):
        """process_turn must return a deep copy; original state is immutable."""
        state  = self._make_state(p2_hp=500)
        p1     = state.side1.pokemon_states[0]
        move   = _make_move(power=80)
        action = ActionEntry(side=1, pokemon=p1, action_type="move", move=move)
        pipe   = TurnPipeline()
        pipe.process_turn(state, [action], {"m1": move})
        assert state.side2.pokemon_states[0].current_hp == 500  # unchanged

    def test_weather_damage_applied(self):
        """End-of-turn sandstorm should damage non-Rock/Ground/Steel types."""
        state  = self._make_state(p1_hp=160, p2_hp=160)
        state.field_state.set_weather(Weather.SANDSTORM, turns=5)
        pipe   = TurnPipeline()
        new    = pipe.process_turn(state, [], {})
        # p1 (노말 type) should take 160//16 = 10 sandstorm damage
        assert new.side1.pokemon_states[0].current_hp == 150

    def test_log_is_populated(self):
        state  = self._make_state()
        pipe   = TurnPipeline()
        new    = pipe.process_turn(state, [], {})
        assert any("턴" in entry for entry in new.log)

    def test_battle_finishes_when_one_side_all_fainted(self):
        state = self._make_state(p2_hp=1)
        p1 = state.side1.pokemon_states[0]
        move = _make_move(type_="노말", category="물리", power=80)
        action = ActionEntry(side=1, pokemon=p1, action_type="move", move=move)
        pipe = TurnPipeline()
        new = pipe.process_turn(state, [action], {"m1": move})
        assert new.battle_over is True
        assert new.winner_side == 1
        assert any("배틀 종료" in entry for entry in new.log)

    def test_finished_battle_does_not_advance_turn(self):
        state = self._make_state()
        state.battle_over = True
        state.winner_side = 1
        pipe = TurnPipeline()
        new = pipe.process_turn(state, [], {})
        assert new.turn_number == state.turn_number
        assert new.battle_over is True
        assert new.winner_side == 1


# ── 6v6 Full Battle End ───────────────────────────────────────────────────────

def _make_6v6_state(
    side1_hp: int = 10,
    side2_hp: int = 10,
) -> BattleStateSnapshot:
    """Build a 6v6 BattleStateSnapshot with all Pokémon at given HP.

    Both sides have 6 Pokémon; active index is [0] for each side.
    Stats are set so that a single 80-power physical move OHKOs the defender.
    """
    def _party(prefix: str, hp: int) -> list[BattlePokemonState]:
        return [
            _make_pokemon(f"{prefix}{i+1}", attack=300, defense=10, hp=hp)
            for i in range(6)
        ]

    side1 = BattleSideState(
        trainer_id=None, trainer_name="트레이너A", party_id=None,
        pokemon_states=_party("A", side1_hp), active_indices=[0],
    )
    side2 = BattleSideState(
        trainer_id=None, trainer_name="트레이너B", party_id=None,
        pokemon_states=_party("B", side2_hp), active_indices=[0],
    )
    return BattleStateSnapshot(side1=side1, side2=side2)


class TestSixVSixBattleEnd:
    """Criterion 3: when all 6 Pokémon on one side faint, battle_over is set
    and winner_side is stored in the snapshot."""

    def _ohko_move(self) -> MoveData:
        return _make_move(type_="노말", category="물리", power=200)

    def test_one_faint_does_not_end_battle(self):
        """Fainting the active Pokémon on side 2 alone should NOT end the battle
        when side 2 still has 5 non-fainted Pokémon."""
        state = _make_6v6_state(side1_hp=500, side2_hp=10)
        p1 = state.side1.pokemon_states[0]
        move = self._ohko_move()
        action = ActionEntry(side=1, pokemon=p1, action_type="move", move=move)
        pipe = TurnPipeline()
        new = pipe.process_turn(state, [action], {"m1": move})
        # Active on side 2 is fainted, but side 2 still has 5 others
        assert new.side2.pokemon_states[0].is_fainted
        assert not new.battle_over

    def test_all_six_fainted_side2_ends_battle(self):
        """When all 6 Pokémon on side 2 are pre-fainted except the active one,
        fainting the last one should set battle_over and winner_side=1."""
        state = _make_6v6_state(side1_hp=500, side2_hp=10)
        # Pre-faint Pokémon 1-5 on side 2
        for i in range(1, 6):
            state.side2.pokemon_states[i].is_fainted = True

        p1 = state.side1.pokemon_states[0]
        move = self._ohko_move()
        action = ActionEntry(side=1, pokemon=p1, action_type="move", move=move)
        pipe = TurnPipeline()
        new = pipe.process_turn(state, [action], {"m1": move})

        assert new.battle_over is True
        assert new.winner_side == 1
        assert any("배틀 종료" in msg for msg in new.log)

    def test_all_six_fainted_side1_ends_battle(self):
        """Symmetric test: all 6 of side 1 faint → winner_side=2."""
        state = _make_6v6_state(side1_hp=10, side2_hp=500)
        for i in range(1, 6):
            state.side1.pokemon_states[i].is_fainted = True

        p2 = state.side2.pokemon_states[0]
        move = self._ohko_move()
        action = ActionEntry(side=2, pokemon=p2, action_type="move", move=move)
        pipe = TurnPipeline()
        new = pipe.process_turn(state, [action], {"m1": move})

        assert new.battle_over is True
        assert new.winner_side == 2

    def test_battle_over_state_is_serializable(self):
        """Criterion 3+4: terminal state must round-trip through to_dict/from_dict."""
        state = _make_6v6_state(side1_hp=500, side2_hp=10)
        for i in range(1, 6):
            state.side2.pokemon_states[i].is_fainted = True
        p1 = state.side1.pokemon_states[0]
        move = self._ohko_move()
        action = ActionEntry(side=1, pokemon=p1, action_type="move", move=move)
        pipe = TurnPipeline()
        final = pipe.process_turn(state, [action], {"m1": move})

        d = final.to_dict()
        restored = BattleStateSnapshot.from_dict(d)
        assert restored.battle_over is True
        assert restored.winner_side == final.winner_side

    def test_draw_when_both_sides_faint(self):
        """If both active Pokémon faint from end-of-turn weather damage in the same
        turn, and all others are pre-fainted → draw (winner_side=None)."""
        # Each active Pokémon has exactly 1 HP; sandstorm deals max(1, hp//16)=1 damage
        state = _make_6v6_state(side1_hp=1, side2_hp=1)
        # Pre-faint Pokémon 1-5 on both sides
        for i in range(1, 6):
            state.side1.pokemon_states[i].is_fainted = True
            state.side2.pokemon_states[i].is_fainted = True

        # Set sandstorm so both active Pokémon take 1 damage at end of turn
        state.field_state.set_weather(Weather.SANDSTORM, turns=3)

        # No move actions — both take weather damage only
        pipe = TurnPipeline()
        new = pipe.process_turn(state, [], {"m1": _make_move()})

        assert new.battle_over is True
        assert new.winner_side is None
        assert any("무승부" in msg for msg in new.log)
