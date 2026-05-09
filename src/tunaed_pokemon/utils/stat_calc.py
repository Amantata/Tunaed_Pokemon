"""Stat calculation helpers (ST-01, ST-02)."""

from __future__ import annotations

import math

# Rank-stage multiplier table.
# ST-02: 상승 (rank stage change) applies these multipliers.
RANK_STAGE_MULTIPLIERS: dict[int, float] = {
    -6: 2 / 8,
    -5: 2 / 7,
    -4: 2 / 6,
    -3: 2 / 5,
    -2: 2 / 4,
    -1: 2 / 3,
     0: 1.0,
     1: 3 / 2,
     2: 4 / 2,
     3: 5 / 2,
     4: 6 / 2,
     5: 7 / 2,
     6: 8 / 2,
}


def calc_hp(base: int, iv: int, ev: int, level: int) -> int:
    """Calculate HP from base stat, IV, EV, and level (ST-01)."""
    return math.floor((2 * base + iv + math.floor(ev / 4)) * level / 100) + level + 10


def calc_stat(base: int, iv: int, ev: int, level: int, nature_mult: float = 1.0) -> int:
    """Calculate non-HP stat from base stat, IV, EV, level, and nature multiplier (ST-01)."""
    inner = math.floor((2 * base + iv + math.floor(ev / 4)) * level / 100) + 5
    return math.floor(inner * nature_mult)


def apply_rank_stage(stat_value: int, stage: int) -> int:
    """Apply a rank-stage multiplier to a stat.

    ST-02: 상승 (rank stage change) — uses the rank multiplier table.
    """
    stage = max(-6, min(6, stage))
    return math.floor(stat_value * RANK_STAGE_MULTIPLIERS[stage])


def apply_reinforcement(stat_value: int, multiplier: float) -> int:
    """Apply a direct reinforcement multiplier to a stat.

    ST-02: 강화 (reinforcement) = direct multiplier, NOT a rank stage.
    """
    return math.floor(stat_value * multiplier)


def get_effective_stat(base_stat_value: int, rank_stage: int, reinforcement: float) -> int:
    """Get the effective stat in battle.

    ST-02: 강화 (reinforcement) and 상승 (rank stage) are applied separately and
    must NEVER be conflated.
    """
    after_rank = apply_rank_stage(base_stat_value, rank_stage)
    return apply_reinforcement(after_rank, reinforcement)
