"""18-type effectiveness table (TypeChart).

Based on the standard Pokémon Gen 6+ type chart, using Korean type names
as defined in PokemonType (models/enums.py).

All 18 types: 노말, 불꽃, 물, 전기, 풀, 얼음, 격투, 독, 땅, 비행,
              에스퍼, 벌레, 바위, 고스트, 드래곤, 악, 강철, 페어리
"""

from __future__ import annotations

# Sparse representation: only entries that differ from 1.0 are stored.
# _RAW[attacker_type][defender_type] = multiplier
_RAW: dict[str, dict[str, float]] = {
    "노말": {
        "바위": 0.5, "강철": 0.5,
        "고스트": 0.0,
    },
    "불꽃": {
        "불꽃": 0.5, "물": 0.5, "바위": 0.5, "드래곤": 0.5,
        "풀": 2.0, "얼음": 2.0, "벌레": 2.0, "강철": 2.0,
    },
    "물": {
        "물": 0.5, "풀": 0.5, "드래곤": 0.5,
        "불꽃": 2.0, "땅": 2.0, "바위": 2.0,
    },
    "전기": {
        "전기": 0.5, "풀": 0.5, "드래곤": 0.5,
        "땅": 0.0,
        "물": 2.0, "비행": 2.0,
    },
    "풀": {
        "불꽃": 0.5, "풀": 0.5, "독": 0.5, "비행": 0.5,
        "벌레": 0.5, "드래곤": 0.5, "강철": 0.5,
        "물": 2.0, "땅": 2.0, "바위": 2.0,
    },
    "얼음": {
        "물": 0.5, "얼음": 0.5,
        "풀": 2.0, "땅": 2.0, "비행": 2.0, "드래곤": 2.0,
    },
    "격투": {
        "독": 0.5, "비행": 0.5, "에스퍼": 0.5, "벌레": 0.5, "페어리": 0.5,
        "고스트": 0.0,
        "노말": 2.0, "얼음": 2.0, "바위": 2.0, "악": 2.0, "강철": 2.0,
    },
    "독": {
        "독": 0.5, "땅": 0.5, "바위": 0.5, "고스트": 0.5,
        "강철": 0.0,
        "풀": 2.0, "페어리": 2.0,
    },
    "땅": {
        "풀": 0.5, "벌레": 0.5,
        "비행": 0.0,
        "불꽃": 2.0, "전기": 2.0, "독": 2.0, "바위": 2.0, "강철": 2.0,
    },
    "비행": {
        "전기": 0.5, "바위": 0.5, "강철": 0.5,
        "풀": 2.0, "격투": 2.0, "벌레": 2.0,
    },
    "에스퍼": {
        "에스퍼": 0.5, "강철": 0.5,
        "악": 0.0,
        "격투": 2.0, "독": 2.0,
    },
    "벌레": {
        "불꽃": 0.5, "격투": 0.5, "비행": 0.5,
        "고스트": 0.5, "강철": 0.5, "페어리": 0.5,
        "풀": 2.0, "에스퍼": 2.0, "악": 2.0,
    },
    "바위": {
        "격투": 0.5, "땅": 0.5, "강철": 0.5,
        "불꽃": 2.0, "얼음": 2.0, "비행": 2.0, "벌레": 2.0,
    },
    "고스트": {
        "노말": 0.0,
        "악": 0.5,
        "에스퍼": 2.0, "고스트": 2.0,
    },
    "드래곤": {
        "강철": 0.5,
        "페어리": 0.0,
        "드래곤": 2.0,
    },
    "악": {
        "격투": 0.5, "악": 0.5, "페어리": 0.5,
        "에스퍼": 2.0, "고스트": 2.0,
    },
    "강철": {
        "불꽃": 0.5, "물": 0.5, "전기": 0.5, "강철": 0.5,
        "얼음": 2.0, "바위": 2.0, "페어리": 2.0,
    },
    "페어리": {
        "불꽃": 0.5, "독": 0.5, "강철": 0.5,
        "격투": 2.0, "드래곤": 2.0, "악": 2.0,
    },
}


def get_effectiveness(attacker_type: str, defender_type: str) -> float:
    """Return the type effectiveness multiplier for a single type matchup.

    Args:
        attacker_type: Move type (Korean name, e.g. '불꽃').
        defender_type: Defender's type (Korean name).

    Returns:
        0.0 (immune), 0.5 (not very effective), 1.0 (normal), or 2.0 (super effective).
    """
    return _RAW.get(attacker_type, {}).get(defender_type, 1.0)


def get_combined_effectiveness(
    move_type: str,
    def_type1: str,
    def_type2: str | None,
) -> float:
    """Return combined type effectiveness against a potentially dual-typed defender.

    Both type matchups are multiplied together (standard dual-type defence rules).
    For example: Water vs Fire/Rock → 2.0 × 2.0 = 4.0.
    """
    mult = get_effectiveness(move_type, def_type1)
    if def_type2:
        mult *= get_effectiveness(move_type, def_type2)
    return mult
