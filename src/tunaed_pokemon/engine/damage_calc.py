"""Damage calculator for the battle engine.

ST-02 enforcement:
  강화 (reinforcement) — a direct multiplier on the stat value.
  상승 (rank stage)     — a rank-stage change resolved via the rank multiplier table.

These two modifiers are applied SEPARATELY in calculate() and must NEVER be merged.
See get_effective_stat() in utils/stat_calc.py for the low-level implementation.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from tunaed_pokemon.engine.battle_state import BattlePokemonState
from tunaed_pokemon.engine.field_state import FieldStateManager
from tunaed_pokemon.engine.type_chart import get_combined_effectiveness
from tunaed_pokemon.models.pokemon import MoveData
from tunaed_pokemon.models.enums import BattleCategory, Weather
from tunaed_pokemon.utils.stat_calc import get_effective_stat


@dataclass
class DamageContext:
    """All inputs required to compute one attack's damage."""
    attacker: BattlePokemonState
    defender: BattlePokemonState
    move: MoveData
    move_type: Optional[str] = None   # overrides move.type if a type-altering effect is active
    is_critical: bool = False
    apply_random: bool = True         # set False for deterministic unit tests
    field: Optional[FieldStateManager] = None


@dataclass
class DamageResult:
    """Output produced by DamageCalculator.calculate()."""
    base_damage: int = 0
    type_mult: float = 1.0
    stab_mult: float = 1.0
    critical_mult: float = 1.0
    weather_mult: float = 1.0
    final_damage: int = 0
    is_immune: bool = False
    messages: list[str] = field(default_factory=list)


class DamageCalculator:
    """Computes move damage using the Gen-5 base formula.

    Formula (simplified):
        base   = floor(floor((2*L/5+2) * Power * EffAtk / EffDef) / 50) + 2
        final  = floor(base × STAB × TypeEff × Critical × Weather × rand)

    ST-02:
        EffAtk = get_effective_stat(base_attack, rank_stage, reinforcement_mult)
        EffDef = get_effective_stat(base_defense, rank_stage, reinforcement_mult)
        rank_stage and reinforcement_mult are passed SEPARATELY to get_effective_stat,
        which first applies the rank multiplier table (상승) then the reinforcement
        multiplier (강화) — the two are never conflated.
    """

    CRIT_MULTIPLIER = 2.0   # Gen-5 basis; some moves may override to ×3

    def calculate(self, ctx: DamageContext) -> DamageResult:
        """Calculate damage for one move use and return a DamageResult."""
        move_type = ctx.move_type or ctx.move.type
        result = DamageResult()

        # Status moves deal no damage
        if ctx.move.category == BattleCategory.STATUS.value or not ctx.move.power:
            return result

        # ── Type effectiveness ────────────────────────────────────────────────
        type_mult = get_combined_effectiveness(
            move_type, ctx.defender.type1, ctx.defender.type2
        )
        result.type_mult = type_mult
        result.is_immune = (type_mult == 0.0)
        if result.is_immune:
            result.messages.append("효과가 없다…")
            return result

        # ── STAB ──────────────────────────────────────────────────────────────
        atk_types = {ctx.attacker.type1}
        if ctx.attacker.type2:
            atk_types.add(ctx.attacker.type2)
        result.stab_mult = 1.5 if move_type in atk_types else 1.0

        # ── Critical hit ──────────────────────────────────────────────────────
        result.critical_mult = self.CRIT_MULTIPLIER if ctx.is_critical else 1.0

        # ── Effective attack / defense (ST-02) ────────────────────────────────
        is_physical = (ctx.move.category == BattleCategory.PHYSICAL.value)
        if is_physical:
            atk_base  = ctx.attacker.battle_stats.get("attack",  50)
            def_base  = ctx.defender.battle_stats.get("defense", 50)
            atk_stage = ctx.attacker.rank_stages.attack
            def_stage = ctx.defender.rank_stages.defense
            atk_reinf = ctx.attacker.reinforcements.attack   # 강화 (ST-02)
            def_reinf = ctx.defender.reinforcements.defense  # 강화 (ST-02)
        else:
            atk_base  = ctx.attacker.battle_stats.get("sp_atk", 50)
            def_base  = ctx.defender.battle_stats.get("sp_def", 50)
            atk_stage = ctx.attacker.rank_stages.sp_atk
            def_stage = ctx.defender.rank_stages.sp_def
            atk_reinf = ctx.attacker.reinforcements.sp_atk
            def_reinf = ctx.defender.reinforcements.sp_def

        # On a critical hit: ignore negative attacker stages, positive defender stages
        if ctx.is_critical:
            atk_stage = max(0, atk_stage)
            def_stage = min(0, def_stage)

        # ST-02: get_effective_stat applies 상승 (rank stage) first, then 강화 (reinforcement)
        eff_atk = get_effective_stat(atk_base, atk_stage, atk_reinf)
        eff_def = max(1, get_effective_stat(def_base, def_stage, def_reinf))

        # ── Weather multiplier ────────────────────────────────────────────────
        result.weather_mult = self._weather_mult(ctx, move_type)

        # ── Base damage (Gen-5 formula) ───────────────────────────────────────
        level = ctx.attacker.level
        power = ctx.move.power
        base = math.floor(
            math.floor(
                math.floor((2 * level / 5 + 2) * power * eff_atk / eff_def) / 50
            ) + 2
        )

        # Random factor 85–100 % (skipped for deterministic tests)
        rand = random.randint(85, 100) / 100.0 if ctx.apply_random else 1.0

        result.base_damage = base
        result.final_damage = max(1, math.floor(
            base
            * result.stab_mult
            * type_mult
            * result.critical_mult
            * result.weather_mult
            * rand
        ))

        # ── Feedback messages ─────────────────────────────────────────────────
        if type_mult >= 4.0:
            result.messages.append("효과는 매우 굉장했다!!")
        elif type_mult >= 2.0:
            result.messages.append("효과는 굉장했다!")
        elif type_mult <= 0.25:
            result.messages.append("효과가 매우 별로인 것 같다…")
        elif type_mult < 1.0:
            result.messages.append("효과가 별로인 것 같다…")

        if ctx.is_critical:
            result.messages.append("급소에 맞았다!")

        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _weather_mult(self, ctx: DamageContext, move_type: str) -> float:
        """Return the weather-based damage multiplier for this move."""
        if ctx.field is None:
            return 1.0
        weather = ctx.field.weather
        if weather in (Weather.SUNNY.value, Weather.EXTREME_SUN.value):
            if move_type == "불꽃":
                return 1.5
            if move_type == "물":
                return 0.5
        elif weather in (Weather.RAIN.value, Weather.HEAVY_RAIN.value):
            if move_type == "물":
                return 1.5
            if move_type == "불꽃":
                return 0.5
        return 1.0
