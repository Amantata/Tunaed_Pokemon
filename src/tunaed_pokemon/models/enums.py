"""Enums for the battle simulator."""

from __future__ import annotations

from enum import Enum


class PokemonType(Enum):
    NORMAL = "노말"
    FIRE = "불꽃"
    WATER = "물"
    ELECTRIC = "전기"
    GRASS = "풀"
    ICE = "얼음"
    FIGHTING = "격투"
    POISON = "독"
    GROUND = "땅"
    FLYING = "비행"
    PSYCHIC = "에스퍼"
    BUG = "벌레"
    ROCK = "바위"
    GHOST = "고스트"
    DRAGON = "드래곤"
    DARK = "악"
    STEEL = "강철"
    FAIRY = "페어리"


class StatName(Enum):
    HP = "HP"
    ATTACK = "공격"
    DEFENSE = "방어"
    SP_ATK = "특공"
    SP_DEF = "특방"
    SPEED = "스피드"


class QualityName(Enum):
    COMMAND = "지시"
    LEADERSHIP = "통솔"
    TRAINING = "육성"
    ABILITY_Q = "능력"


class QualityRank(Enum):
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    AA = "AA"
    AAA = "AAA"
    S = "S"

    @property
    def points(self) -> int:
        return {
            "E": 0, "D": 2, "C": 4, "B": 6,
            "A": 10, "AA": 14, "AAA": 20, "S": 26,
        }[self.value]


class StatusCondition(Enum):
    BURN = "화상"
    FROSTBITE = "동상"
    POISON = "독"
    BAD_POISON = "맹독"
    SLEEP = "잠듦"
    PARALYSIS = "마비"
    FREEZE = "얼음"
    CONFUSION = "혼란"


class Weather(Enum):
    NONE = "맑음"
    SUNNY = "쾌청"
    RAIN = "비"
    SANDSTORM = "모래바람"
    HAIL = "싸라기눈"
    SNOWSTORM = "눈보라"
    HEAVY_RAIN = "폭우"
    EXTREME_SUN = "매우 강한 햇빛"
    STRONG_WINDS = "강한 바람"


class Terrain(Enum):
    """「필드」 효과 (FE-04) — persistent field effects, set by terrain-class moves (FE-02)."""
    NONE = "없음"
    ELECTRIC = "일렉트릭필드"
    GRASSY = "그래스필드"
    MISTY = "미스트필드"
    PSYCHIC = "사이코필드"


class SpecialField(Enum):
    """《필드》 (FE-06) — special arena/dimension; entirely separate concept from Terrain."""
    NONE = "없음"
    SHADOW_REALM = "이계"
    ARENA = "경기장"
    CUSTOM = "특수 경기장"


class BattleCategory(Enum):
    PHYSICAL = "물리"
    SPECIAL = "특수"
    STATUS = "변화"


class BattleFormat(Enum):
    SINGLE = "싱글"
    DOUBLE = "더블"


class CommandPotentialType(Enum):
    BASIC = "기본"
    MASTERY = "숙달"
    DEPLOYMENT = "전개"


class BaseStatRank(Enum):
    """종족치 랭크 (base stat total rank)."""
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    AA = "AA"
    AAA = "AAA"
    S = "S"
