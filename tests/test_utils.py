"""Tests for type chart and stat calculation utilities."""

from __future__ import annotations

import pytest

from tunaed_pokemon.models.enums import PokemonType, StatType
from tunaed_pokemon.utils.type_chart import (
    get_type_effectiveness,
    get_dual_move_effectiveness,
    is_stab,
    TYPE_CHART,
)
from tunaed_pokemon.utils.stat_calc import (
    calculate_hp,
    calculate_stat,
    apply_rank_stage,
    apply_reinforcement,
    calculate_effective_stat,
    calculate_damage,
)


# ---------------------------------------------------------------------------
# Type Chart Tests
# ---------------------------------------------------------------------------

class TestTypeChart:
    def test_all_types_present(self) -> None:
        """Every type must be represented as both attacker and defender."""
        for t in PokemonType:
            assert t in TYPE_CHART, f"Missing attacker type: {t}"
            for d in PokemonType:
                assert d in TYPE_CHART[t], f"Missing defender type {d} for attacker {t}"

    def test_super_effective(self) -> None:
        assert get_type_effectiveness(PokemonType.FIRE, [PokemonType.GRASS]) == 2.0
        assert get_type_effectiveness(PokemonType.WATER, [PokemonType.FIRE]) == 2.0

    def test_not_very_effective(self) -> None:
        assert get_type_effectiveness(PokemonType.FIRE, [PokemonType.WATER]) == 0.5

    def test_immune(self) -> None:
        assert get_type_effectiveness(PokemonType.NORMAL, [PokemonType.GHOST]) == 0.0
        assert get_type_effectiveness(PokemonType.GROUND, [PokemonType.FLYING]) == 0.0

    def test_dual_type_defense(self) -> None:
        # Fire vs Grass/Steel = 2.0 * 2.0 = 4.0
        eff = get_type_effectiveness(
            PokemonType.FIRE, [PokemonType.GRASS, PokemonType.STEEL]
        )
        assert eff == 4.0

    def test_dual_type_cancel(self) -> None:
        # Electric vs Water/Ground = 2.0 * 0.0 = 0.0 (immune)
        eff = get_type_effectiveness(
            PokemonType.ELECTRIC, [PokemonType.WATER, PokemonType.GROUND]
        )
        assert eff == 0.0

    def test_stab(self) -> None:
        assert is_stab(PokemonType.FIRE, [PokemonType.FIRE]) is True
        assert is_stab(PokemonType.FIRE, [PokemonType.FIRE, PokemonType.FLYING]) is True
        assert is_stab(PokemonType.WATER, [PokemonType.FIRE]) is False

    def test_dual_move_effectiveness(self) -> None:
        # Single type move
        eff = get_dual_move_effectiveness(
            [PokemonType.FIRE], [PokemonType.GRASS]
        )
        assert eff == 2.0

        # Dual type move picks the better one
        eff = get_dual_move_effectiveness(
            [PokemonType.FIRE, PokemonType.WATER], [PokemonType.GRASS]
        )
        assert eff == 2.0  # Fire > Water vs Grass


# ---------------------------------------------------------------------------
# Stat Calculation Tests
# ---------------------------------------------------------------------------

class TestStatCalc:
    def test_hp_calculation(self) -> None:
        # Standard HP formula: ((2*100 + 0 + 0) * 50 / 100) + 50 + 10 = 160
        hp = calculate_hp(base=100, level=50)
        assert hp == 160

    def test_hp_shedinja(self) -> None:
        assert calculate_hp(base=1, level=100) == 1

    def test_stat_calculation(self) -> None:
        # ((2*100 + 0 + 0) * 50 / 100) + 5 = 105
        stat = calculate_stat(base=100, level=50)
        assert stat == 105

    def test_stat_with_iv(self) -> None:
        # ((2*100 + 31 + 0) * 50 / 100) + 5 = 120
        stat = calculate_stat(base=100, iv=31, level=50)
        assert stat == 120

    def test_stat_with_ev(self) -> None:
        # ((2*100 + 0 + 252/4) * 50 / 100) + 5 = 136
        stat = calculate_stat(base=100, ev=252, level=50)
        assert stat == 136

    def test_rank_stage_neutral(self) -> None:
        assert apply_rank_stage(100, 0) == 100

    def test_rank_stage_positive(self) -> None:
        # +1 stage = ×1.5
        assert apply_rank_stage(100, 1) == 150

    def test_rank_stage_negative(self) -> None:
        # -1 stage = ×(2/3) ≈ 66
        assert apply_rank_stage(100, -1) == 66

    def test_rank_stage_clamp(self) -> None:
        # Stage beyond ±6 should be clamped
        assert apply_rank_stage(100, 10) == apply_rank_stage(100, 6)
        assert apply_rank_stage(100, -10) == apply_rank_stage(100, -6)

    def test_reinforcement(self) -> None:
        """강화: direct multiplier (ST-02)."""
        assert apply_reinforcement(100, 2.0) == 200
        assert apply_reinforcement(100, 1.5) == 150
        assert apply_reinforcement(100, 0.5) == 50

    def test_effective_stat_combines_both(self) -> None:
        """ST-02: 상승 and 강화 are applied independently."""
        # Base 100, +1 rank (×1.5), ×2.0 reinforcement
        # = 100 × 1.5 = 150, then × 2.0 = 300
        result = calculate_effective_stat(100, rank_stage=1, reinforcement_multiplier=2.0)
        assert result == 300

    def test_damage_basic(self) -> None:
        damage = calculate_damage(
            level=50, power=80, attack_stat=100, defense_stat=100
        )
        assert damage > 0

    def test_damage_immune(self) -> None:
        damage = calculate_damage(
            level=50, power=80, attack_stat=100, defense_stat=100,
            type_effectiveness=0.0,
        )
        assert damage == 0

    def test_damage_stab(self) -> None:
        no_stab = calculate_damage(
            level=50, power=80, attack_stat=100, defense_stat=100, stab=False
        )
        with_stab = calculate_damage(
            level=50, power=80, attack_stat=100, defense_stat=100, stab=True
        )
        assert with_stab > no_stab

    def test_damage_critical(self) -> None:
        normal = calculate_damage(
            level=50, power=80, attack_stat=100, defense_stat=100, critical=False
        )
        crit = calculate_damage(
            level=50, power=80, attack_stat=100, defense_stat=100, critical=True
        )
        assert crit > normal
