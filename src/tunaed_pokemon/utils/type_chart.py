"""18-type effectiveness chart.

Type matchup table used for damage calculation.
Values: 2.0 = super effective, 0.5 = not very effective,
        0.0 = immune, 1.0 = neutral.
"""

from __future__ import annotations

from tunaed_pokemon.models.enums import PokemonType

# Shorthand aliases
_T = PokemonType

# fmt: off
# TYPE_CHART[attacking_type][defending_type] = effectiveness multiplier
TYPE_CHART: dict[PokemonType, dict[PokemonType, float]] = {
    _T.NORMAL: {
        _T.NORMAL: 1.0, _T.FIRE: 1.0, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 1.0, _T.ICE: 1.0, _T.FIGHTING: 1.0, _T.POISON: 1.0,
        _T.GROUND: 1.0, _T.FLYING: 1.0, _T.PSYCHIC: 1.0, _T.BUG: 1.0,
        _T.ROCK: 0.5, _T.GHOST: 0.0, _T.DRAGON: 1.0, _T.DARK: 1.0,
        _T.STEEL: 0.5, _T.FAIRY: 1.0,
    },
    _T.FIRE: {
        _T.NORMAL: 1.0, _T.FIRE: 0.5, _T.WATER: 0.5, _T.ELECTRIC: 1.0,
        _T.GRASS: 2.0, _T.ICE: 2.0, _T.FIGHTING: 1.0, _T.POISON: 1.0,
        _T.GROUND: 1.0, _T.FLYING: 1.0, _T.PSYCHIC: 1.0, _T.BUG: 2.0,
        _T.ROCK: 0.5, _T.GHOST: 1.0, _T.DRAGON: 0.5, _T.DARK: 1.0,
        _T.STEEL: 2.0, _T.FAIRY: 1.0,
    },
    _T.WATER: {
        _T.NORMAL: 1.0, _T.FIRE: 2.0, _T.WATER: 0.5, _T.ELECTRIC: 1.0,
        _T.GRASS: 0.5, _T.ICE: 1.0, _T.FIGHTING: 1.0, _T.POISON: 1.0,
        _T.GROUND: 2.0, _T.FLYING: 1.0, _T.PSYCHIC: 1.0, _T.BUG: 1.0,
        _T.ROCK: 2.0, _T.GHOST: 1.0, _T.DRAGON: 0.5, _T.DARK: 1.0,
        _T.STEEL: 1.0, _T.FAIRY: 1.0,
    },
    _T.ELECTRIC: {
        _T.NORMAL: 1.0, _T.FIRE: 1.0, _T.WATER: 2.0, _T.ELECTRIC: 0.5,
        _T.GRASS: 0.5, _T.ICE: 1.0, _T.FIGHTING: 1.0, _T.POISON: 1.0,
        _T.GROUND: 0.0, _T.FLYING: 2.0, _T.PSYCHIC: 1.0, _T.BUG: 1.0,
        _T.ROCK: 1.0, _T.GHOST: 1.0, _T.DRAGON: 0.5, _T.DARK: 1.0,
        _T.STEEL: 1.0, _T.FAIRY: 1.0,
    },
    _T.GRASS: {
        _T.NORMAL: 1.0, _T.FIRE: 0.5, _T.WATER: 2.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 0.5, _T.ICE: 1.0, _T.FIGHTING: 1.0, _T.POISON: 0.5,
        _T.GROUND: 2.0, _T.FLYING: 0.5, _T.PSYCHIC: 1.0, _T.BUG: 0.5,
        _T.ROCK: 2.0, _T.GHOST: 1.0, _T.DRAGON: 0.5, _T.DARK: 1.0,
        _T.STEEL: 0.5, _T.FAIRY: 1.0,
    },
    _T.ICE: {
        _T.NORMAL: 1.0, _T.FIRE: 0.5, _T.WATER: 0.5, _T.ELECTRIC: 1.0,
        _T.GRASS: 2.0, _T.ICE: 0.5, _T.FIGHTING: 1.0, _T.POISON: 1.0,
        _T.GROUND: 2.0, _T.FLYING: 2.0, _T.PSYCHIC: 1.0, _T.BUG: 1.0,
        _T.ROCK: 1.0, _T.GHOST: 1.0, _T.DRAGON: 2.0, _T.DARK: 1.0,
        _T.STEEL: 0.5, _T.FAIRY: 1.0,
    },
    _T.FIGHTING: {
        _T.NORMAL: 2.0, _T.FIRE: 1.0, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 1.0, _T.ICE: 2.0, _T.FIGHTING: 1.0, _T.POISON: 0.5,
        _T.GROUND: 1.0, _T.FLYING: 0.5, _T.PSYCHIC: 0.5, _T.BUG: 0.5,
        _T.ROCK: 2.0, _T.GHOST: 0.0, _T.DRAGON: 1.0, _T.DARK: 2.0,
        _T.STEEL: 2.0, _T.FAIRY: 0.5,
    },
    _T.POISON: {
        _T.NORMAL: 1.0, _T.FIRE: 1.0, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 2.0, _T.ICE: 1.0, _T.FIGHTING: 1.0, _T.POISON: 0.5,
        _T.GROUND: 0.5, _T.FLYING: 1.0, _T.PSYCHIC: 1.0, _T.BUG: 1.0,
        _T.ROCK: 0.5, _T.GHOST: 0.5, _T.DRAGON: 1.0, _T.DARK: 1.0,
        _T.STEEL: 0.0, _T.FAIRY: 2.0,
    },
    _T.GROUND: {
        _T.NORMAL: 1.0, _T.FIRE: 2.0, _T.WATER: 1.0, _T.ELECTRIC: 2.0,
        _T.GRASS: 0.5, _T.ICE: 1.0, _T.FIGHTING: 1.0, _T.POISON: 2.0,
        _T.GROUND: 1.0, _T.FLYING: 0.0, _T.PSYCHIC: 1.0, _T.BUG: 0.5,
        _T.ROCK: 2.0, _T.GHOST: 1.0, _T.DRAGON: 1.0, _T.DARK: 1.0,
        _T.STEEL: 2.0, _T.FAIRY: 1.0,
    },
    _T.FLYING: {
        _T.NORMAL: 1.0, _T.FIRE: 1.0, _T.WATER: 1.0, _T.ELECTRIC: 0.5,
        _T.GRASS: 2.0, _T.ICE: 1.0, _T.FIGHTING: 2.0, _T.POISON: 1.0,
        _T.GROUND: 1.0, _T.FLYING: 1.0, _T.PSYCHIC: 1.0, _T.BUG: 2.0,
        _T.ROCK: 0.5, _T.GHOST: 1.0, _T.DRAGON: 1.0, _T.DARK: 1.0,
        _T.STEEL: 0.5, _T.FAIRY: 1.0,
    },
    _T.PSYCHIC: {
        _T.NORMAL: 1.0, _T.FIRE: 1.0, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 1.0, _T.ICE: 1.0, _T.FIGHTING: 2.0, _T.POISON: 2.0,
        _T.GROUND: 1.0, _T.FLYING: 1.0, _T.PSYCHIC: 0.5, _T.BUG: 1.0,
        _T.ROCK: 1.0, _T.GHOST: 1.0, _T.DRAGON: 1.0, _T.DARK: 0.0,
        _T.STEEL: 0.5, _T.FAIRY: 1.0,
    },
    _T.BUG: {
        _T.NORMAL: 1.0, _T.FIRE: 0.5, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 2.0, _T.ICE: 1.0, _T.FIGHTING: 0.5, _T.POISON: 0.5,
        _T.GROUND: 1.0, _T.FLYING: 0.5, _T.PSYCHIC: 2.0, _T.BUG: 1.0,
        _T.ROCK: 1.0, _T.GHOST: 0.5, _T.DRAGON: 1.0, _T.DARK: 2.0,
        _T.STEEL: 0.5, _T.FAIRY: 0.5,
    },
    _T.ROCK: {
        _T.NORMAL: 1.0, _T.FIRE: 2.0, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 1.0, _T.ICE: 2.0, _T.FIGHTING: 0.5, _T.POISON: 1.0,
        _T.GROUND: 0.5, _T.FLYING: 2.0, _T.PSYCHIC: 1.0, _T.BUG: 2.0,
        _T.ROCK: 1.0, _T.GHOST: 1.0, _T.DRAGON: 1.0, _T.DARK: 1.0,
        _T.STEEL: 0.5, _T.FAIRY: 1.0,
    },
    _T.GHOST: {
        _T.NORMAL: 0.0, _T.FIRE: 1.0, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 1.0, _T.ICE: 1.0, _T.FIGHTING: 1.0, _T.POISON: 1.0,
        _T.GROUND: 1.0, _T.FLYING: 1.0, _T.PSYCHIC: 2.0, _T.BUG: 1.0,
        _T.ROCK: 1.0, _T.GHOST: 2.0, _T.DRAGON: 1.0, _T.DARK: 0.5,
        _T.STEEL: 1.0, _T.FAIRY: 1.0,
    },
    _T.DRAGON: {
        _T.NORMAL: 1.0, _T.FIRE: 1.0, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 1.0, _T.ICE: 1.0, _T.FIGHTING: 1.0, _T.POISON: 1.0,
        _T.GROUND: 1.0, _T.FLYING: 1.0, _T.PSYCHIC: 1.0, _T.BUG: 1.0,
        _T.ROCK: 1.0, _T.GHOST: 1.0, _T.DRAGON: 2.0, _T.DARK: 1.0,
        _T.STEEL: 0.5, _T.FAIRY: 0.0,
    },
    _T.DARK: {
        _T.NORMAL: 1.0, _T.FIRE: 1.0, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 1.0, _T.ICE: 1.0, _T.FIGHTING: 0.5, _T.POISON: 1.0,
        _T.GROUND: 1.0, _T.FLYING: 1.0, _T.PSYCHIC: 2.0, _T.BUG: 1.0,
        _T.ROCK: 1.0, _T.GHOST: 2.0, _T.DRAGON: 1.0, _T.DARK: 0.5,
        _T.STEEL: 0.5, _T.FAIRY: 0.5,
    },
    _T.STEEL: {
        _T.NORMAL: 1.0, _T.FIRE: 0.5, _T.WATER: 0.5, _T.ELECTRIC: 0.5,
        _T.GRASS: 1.0, _T.ICE: 2.0, _T.FIGHTING: 1.0, _T.POISON: 1.0,
        _T.GROUND: 1.0, _T.FLYING: 1.0, _T.PSYCHIC: 1.0, _T.BUG: 1.0,
        _T.ROCK: 2.0, _T.GHOST: 1.0, _T.DRAGON: 1.0, _T.DARK: 1.0,
        _T.STEEL: 0.5, _T.FAIRY: 2.0,
    },
    _T.FAIRY: {
        _T.NORMAL: 1.0, _T.FIRE: 0.5, _T.WATER: 1.0, _T.ELECTRIC: 1.0,
        _T.GRASS: 1.0, _T.ICE: 1.0, _T.FIGHTING: 2.0, _T.POISON: 0.5,
        _T.GROUND: 1.0, _T.FLYING: 1.0, _T.PSYCHIC: 1.0, _T.BUG: 1.0,
        _T.ROCK: 1.0, _T.GHOST: 1.0, _T.DRAGON: 2.0, _T.DARK: 2.0,
        _T.STEEL: 0.5, _T.FAIRY: 1.0,
    },
}
# fmt: on


def get_type_effectiveness(
    attack_type: PokemonType,
    defend_types: list[PokemonType],
) -> float:
    """Calculate combined type effectiveness multiplier.

    For dual-type defenders, the multipliers are multiplied together.
    E.g. Fire vs Grass/Steel = 2.0 * 2.0 = 4.0.
    """
    result = 1.0
    for def_type in defend_types:
        result *= TYPE_CHART[attack_type][def_type]
    return result


def get_dual_move_effectiveness(
    attack_types: list[PokemonType],
    defend_types: list[PokemonType],
) -> float:
    """Calculate effectiveness for a dual-type move.

    Per rules: use the more favorable type compatibility;
    both type effects apply.
    """
    if len(attack_types) == 1:
        return get_type_effectiveness(attack_types[0], defend_types)

    eff1 = get_type_effectiveness(attack_types[0], defend_types)
    eff2 = get_type_effectiveness(attack_types[1], defend_types)
    return max(eff1, eff2)


def is_stab(
    move_type: PokemonType,
    pokemon_types: list[PokemonType],
) -> bool:
    """Check if a move gets STAB (Same-Type Attack Bonus)."""
    return move_type in pokemon_types
