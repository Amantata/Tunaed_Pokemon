"""Stat calculation utilities.

Handles HP/stat formulas, IV/EV, and the strict distinction between
강화 (reinforcement/multiplier) and 상승 (rank stage change) per ST-02.
"""

from __future__ import annotations

from tunaed_pokemon.models.enums import (
    StatType,
    STAT_RANK_STAGE_MULTIPLIERS,
    ACCURACY_EVASION_STAGE_MULTIPLIERS,
)


def calculate_hp(
    base: int,
    iv: int = 0,
    ev: int = 0,
    level: int = 50,
) -> int:
    """Calculate HP stat value.

    Uses the standard formula:
        HP = ((2*Base + IV + EV/4) * Level / 100) + Level + 10

    If base == 1 (Shedinja rule), HP is always 1.
    """
    if base == 1:
        return 1
    return int(((2 * base + iv + ev // 4) * level / 100) + level + 10)


def calculate_stat(
    base: int,
    iv: int = 0,
    ev: int = 0,
    level: int = 50,
    nature_modifier: float = 1.0,
) -> int:
    """Calculate a non-HP stat value.

    Uses the standard formula:
        Stat = (((2*Base + IV + EV/4) * Level / 100) + 5) * NatureModifier

    Nature modifier is 1.0 (neutral), 1.1 (beneficial), or 0.9 (hindering).
    """
    raw = int(((2 * base + iv + ev // 4) * level / 100) + 5)
    return int(raw * nature_modifier)


def apply_rank_stage(
    stat_value: int,
    stage: int,
    stat_type: StatType = StatType.ATTACK,
) -> int:
    """Apply a rank stage modifier (상승/하락) to a stat value.

    This is the 상승 (rank change) system per ST-02.
    Clamps stage to [-6, +6].
    Uses separate multiplier tables for accuracy/evasion vs. other stats.

    Args:
        stat_value: The base calculated stat value.
        stage: Rank stage (-6 to +6).
        stat_type: Which stat (determines multiplier table).

    Returns:
        Modified stat value (floored to int).
    """
    clamped = max(-6, min(6, stage))
    if stat_type in (StatType.ACCURACY, StatType.EVASION):
        multiplier = ACCURACY_EVASION_STAGE_MULTIPLIERS[clamped]
    else:
        multiplier = STAT_RANK_STAGE_MULTIPLIERS[clamped]
    return int(stat_value * multiplier)


def apply_reinforcement(
    stat_value: int,
    multiplier: float,
) -> int:
    """Apply a reinforcement multiplier (강화) to a stat value.

    This is the 강화 (reinforcement) system per ST-02.
    A direct multiplier (e.g. ×2, ×1.5, ×0.5) applied to the stat.
    This is completely independent of rank stages.

    Args:
        stat_value: The stat value to modify.
        multiplier: The reinforcement multiplier (e.g. 2.0, 1.5).

    Returns:
        Modified stat value (floored to int).
    """
    return int(stat_value * multiplier)


def calculate_effective_stat(
    base_stat: int,
    rank_stage: int = 0,
    reinforcement_multiplier: float = 1.0,
    stat_type: StatType = StatType.ATTACK,
) -> int:
    """Calculate the effective stat considering both 상승 and 강화.

    Per ST-02, these are applied independently:
    1. First apply rank stage (상승) to the base stat.
    2. Then apply reinforcement (강화) multiplier.

    Args:
        base_stat: The calculated stat value (from base/IV/EV/level).
        rank_stage: Current rank stage (-6 to +6).
        reinforcement_multiplier: Total reinforcement multiplier.
        stat_type: Which stat type.

    Returns:
        Final effective stat value.
    """
    after_rank = apply_rank_stage(base_stat, rank_stage, stat_type)
    return apply_reinforcement(after_rank, reinforcement_multiplier)


def calculate_damage(
    level: int,
    power: int,
    attack_stat: int,
    defense_stat: int,
    *,
    stab: bool = False,
    type_effectiveness: float = 1.0,
    critical: bool = False,
    other_multiplier: float = 1.0,
) -> int:
    """Calculate damage using the standard damage formula.

    Formula:
        Damage = ((2*Level/5 + 2) * Power * A/D) / 50 + 2
        × STAB (1.5) × TypeEffectiveness × Critical (2.0) × Other

    Critical hits (per rules):
    - Ignore attacker's stat decreases and defender's stat increases.
    - Ignore Reflect/Light Screen damage reduction.
    - These should be handled by the caller before passing stats.

    Args:
        level: Attacker's level.
        power: Move base power.
        attack_stat: Effective attack stat (after rank/reinforcement).
        defense_stat: Effective defense stat (after rank/reinforcement).
        stab: Whether Same-Type Attack Bonus applies.
        type_effectiveness: Combined type effectiveness multiplier.
        critical: Whether this is a critical hit.
        other_multiplier: Any additional multipliers (items, abilities, etc.).

    Returns:
        Final damage value (minimum 1 if not immune).
    """
    if type_effectiveness == 0.0:
        return 0

    base_damage = ((2 * level / 5 + 2) * power * attack_stat / defense_stat) / 50 + 2

    if stab:
        base_damage *= 1.5

    base_damage *= type_effectiveness

    if critical:
        base_damage *= 2.0

    base_damage *= other_multiplier

    return max(1, int(base_damage))
