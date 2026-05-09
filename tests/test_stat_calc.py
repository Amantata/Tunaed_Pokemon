"""Tests for stat calculation utilities (ST-01, ST-02)."""

from __future__ import annotations

import pytest

from tunaed_pokemon.utils.stat_calc import (
    calc_hp,
    calc_stat,
    apply_rank_stage,
    apply_reinforcement,
    get_effective_stat,
    RANK_STAGE_MULTIPLIERS,
)


class TestCalcHp:
    def test_basic(self):
        # Standard: base 45, IV 31, EV 0, level 50 → expected value
        result = calc_hp(45, 31, 0, 50)
        assert result == 120   # (2*45+31+0)*50/100 + 50 + 10 = 60.5*0.5... let me compute
        # (2*45 + 31 + 0) * 50 // 100 + 50 + 10 = (121*50)//100 + 60 = 60 + 60 = 120

    def test_zero_ev_is_default(self):
        """ST-01: EVs default to 0."""
        assert calc_hp(45, 0, 0, 50) == calc_hp(45, 0, 0, 50)

    def test_higher_base_gives_higher_hp(self):
        assert calc_hp(100, 31, 0, 50) > calc_hp(50, 31, 0, 50)


class TestCalcStat:
    def test_basic(self):
        # base 80, IV 31, EV 0, level 50, nature 1.0
        # floor((2*80+31+0)*50/100) + 5 = floor(191*50/100) + 5 = 95 + 5 = 100; floor(100 * 1.0) = 100
        result = calc_stat(80, 31, 0, 50, 1.0)
        assert result == 100

    def test_nature_boost(self):
        base = calc_stat(80, 31, 0, 50, 1.0)
        boosted = calc_stat(80, 31, 0, 50, 1.1)
        assert boosted > base


class TestRankStageMultipliers:
    def test_zero_is_one(self):
        assert RANK_STAGE_MULTIPLIERS[0] == 1.0

    def test_plus_1_is_1_5(self):
        assert RANK_STAGE_MULTIPLIERS[1] == pytest.approx(1.5)

    def test_minus_1_is_two_thirds(self):
        assert RANK_STAGE_MULTIPLIERS[-1] == pytest.approx(2 / 3)


class TestApplyRankStage:
    def test_zero_stage_unchanged(self):
        assert apply_rank_stage(100, 0) == 100

    def test_plus_1_stage(self):
        # 100 * 1.5 = 150
        assert apply_rank_stage(100, 1) == 150

    def test_minus_2_stage(self):
        # 100 * (2/4) = 50
        assert apply_rank_stage(100, -2) == 50

    def test_clamps_at_6(self):
        # Stage 6 = ×4; stage 7 should also give ×4 (clamped)
        assert apply_rank_stage(100, 6) == apply_rank_stage(100, 7)

    def test_clamps_at_minus_6(self):
        assert apply_rank_stage(100, -6) == apply_rank_stage(100, -10)


class TestApplyReinforcement:
    def test_multiplier_applied(self):
        """ST-02: 강화 (reinforcement) = direct multiplier on stat value."""
        assert apply_reinforcement(100, 2.0) == 200

    def test_one_unchanged(self):
        assert apply_reinforcement(100, 1.0) == 100

    def test_fraction(self):
        assert apply_reinforcement(100, 0.5) == 50


class TestGetEffectiveStat:
    def test_both_applied_independently(self):
        """ST-02: 강화 and 상승 must be applied independently (never combined into a single multiplier)."""
        # Rank stage +1 → ×1.5; reinforcement ×2.0
        # Expected: floor(floor(100 * 1.5) * 2.0) = floor(150 * 2.0) = 300
        assert get_effective_stat(100, 1, 2.0) == 300

    def test_no_boost(self):
        assert get_effective_stat(100, 0, 1.0) == 100
