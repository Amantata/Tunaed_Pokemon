"""Core enumerations and constants for the Tunaed Pokemon battle system.

Covers types, stats, ranks, status conditions, weather, field effects,
and potential categories as defined in the 오레마스 ruleset.
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# Pokémon Types (18-type system)
# ---------------------------------------------------------------------------

class PokemonType(str, Enum):
    """18 Pokémon types used in the battle system."""

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


# ---------------------------------------------------------------------------
# Move category
# ---------------------------------------------------------------------------

class MoveCategory(str, Enum):
    """Move damage category."""

    PHYSICAL = "물리"
    SPECIAL = "특수"
    STATUS = "변화"


class MoveContact(str, Enum):
    """Whether a move makes physical contact."""

    CONTACT = "접촉"
    NON_CONTACT = "비접촉"


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class StatType(str, Enum):
    """Six base stats + accuracy/evasion (for in-battle modifiers)."""

    HP = "체력"
    ATTACK = "공격"
    DEFENSE = "방어"
    SP_ATK = "특공"
    SP_DEF = "특방"
    SPEED = "속도"
    ACCURACY = "명중"
    EVASION = "회피"


# The six base stats (excluding accuracy/evasion which are battle-only).
BASE_STAT_TYPES: tuple[StatType, ...] = (
    StatType.HP,
    StatType.ATTACK,
    StatType.DEFENSE,
    StatType.SP_ATK,
    StatType.SP_DEF,
    StatType.SPEED,
)


# ---------------------------------------------------------------------------
# Species Stat Rank (종족치 랭크)
# ---------------------------------------------------------------------------

class StatRank(str, Enum):
    """Species stat rank tiers.

    Each rank covers a numeric range of base stat values.
    E.g. A- = 110, A = 111-134, A+ = 135, A++ up to 139.
    """

    E = "E"
    E_MINUS = "E-"
    E_PLUS = "E+"
    E_PLUS_PLUS = "E++"
    D = "D"
    D_MINUS = "D-"
    D_PLUS = "D+"
    D_PLUS_PLUS = "D++"
    C = "C"
    C_MINUS = "C-"
    C_PLUS = "C+"
    C_PLUS_PLUS = "C++"
    B = "B"
    B_MINUS = "B-"
    B_PLUS = "B+"
    B_PLUS_PLUS = "B++"
    A = "A"
    A_MINUS = "A-"
    A_PLUS = "A+"
    A_PLUS_PLUS = "A++"
    AA = "AA"
    AA_MINUS = "AA-"
    AA_PLUS = "AA+"
    AA_PLUS_PLUS = "AA++"
    AAA = "AAA"
    AAA_MINUS = "AAA-"
    AAA_PLUS = "AAA+"
    AAA_PLUS_PLUS = "AAA++"
    S = "S"


# Mapping: stat rank -> (min_value, max_value) inclusive.
STAT_RANK_RANGES: dict[str, tuple[int, int]] = {
    "E": (1, 35),
    "E++": (36, 39),
    "D-": (40, 40),
    "D": (41, 54),
    "D+": (55, 55),
    "D++": (56, 59),
    "C-": (60, 60),
    "C": (61, 84),
    "C+": (85, 85),
    "C++": (86, 89),
    "B-": (90, 90),
    "B": (91, 104),
    "B+": (105, 105),
    "B++": (106, 109),
    "A-": (110, 110),
    "A": (111, 134),
    "A+": (135, 135),
    "A++": (136, 139),
    "AA-": (140, 140),
    "AA": (141, 164),
    "AA+": (165, 165),
    "AA++": (166, 169),
    "AAA-": (170, 170),
    "AAA": (171, 194),
    "AAA+": (195, 195),
    "AAA++": (196, 199),
    "S": (200, 999),
}


def stat_value_to_rank(value: int) -> str:
    """Return the stat rank string for a given numeric stat value."""
    for rank, (lo, hi) in STAT_RANK_RANGES.items():
        if lo <= value <= hi:
            return rank
    if value < 1:
        return "E"
    return "S"


# ---------------------------------------------------------------------------
# Trainer Quality Rank (자질 랭크)
# ---------------------------------------------------------------------------

class QualityRank(str, Enum):
    """Trainer quality rank (E through S).

    Points required at creation: E=0, D=2, C=4, B=6, A=10, AA=14, AAA=20, S=26.
    """

    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    AA = "AA"
    AAA = "AAA"
    S = "S"


QUALITY_RANK_ORDER: list[QualityRank] = [
    QualityRank.E,
    QualityRank.D,
    QualityRank.C,
    QualityRank.B,
    QualityRank.A,
    QualityRank.AA,
    QualityRank.AAA,
    QualityRank.S,
]

QUALITY_RANK_POINTS: dict[QualityRank, int] = {
    QualityRank.E: 0,
    QualityRank.D: 2,
    QualityRank.C: 4,
    QualityRank.B: 6,
    QualityRank.A: 10,
    QualityRank.AA: 14,
    QualityRank.AAA: 20,
    QualityRank.S: 26,
}


def quality_rank_index(rank: QualityRank) -> int:
    """Return the ordinal index (0=E … 7=S) for a quality rank."""
    return QUALITY_RANK_ORDER.index(rank)


def quality_rank_difference(a: QualityRank, b: QualityRank) -> int:
    """Return how many ranks *a* is above *b* (negative if below)."""
    return quality_rank_index(a) - quality_rank_index(b)


# ---------------------------------------------------------------------------
# Status Conditions (상태이상) — at most 2 sleep + confusion overlay
# ---------------------------------------------------------------------------

class StatusCondition(str, Enum):
    """Primary status conditions (상태이상).

    A Pokémon can have at most one non-sleep status condition.
    Sleep (잠듦) is limited to 2 across a party.
    Confusion (혼란) is treated as both a status change and status condition.
    """

    NONE = "없음"
    BURN = "화상"
    FREEZE = "동상"
    POISON = "독"
    TOXIC = "맹독"
    SLEEP = "잠듦"
    PARALYSIS = "마비"
    ICE = "얼음"


# ---------------------------------------------------------------------------
# Status Changes (상태변화) — stackable/multiple
# ---------------------------------------------------------------------------

class StatusChange(str, Enum):
    """Status changes (상태변화) that can coexist alongside status conditions."""

    CONFUSION = "혼란"
    HEATED = "가열"
    CHARGED = "충전"
    COOLED = "냉각"
    SOAKED = "침수"
    ELECTRIFIED = "송전"
    VILLAIN = "악인"
    YAWN = "하품"
    HIBERNATION = "동면"
    COUNTER = "요격"
    RAGE = "분노"
    SILENCE = "침묵"
    AMNESIA = "망각"
    INFATUATION = "헤롱헤롱"
    DISABLE = "사슬묶기"
    ENCORE = "앵콜"
    IMPRISON = "봉인"
    TAUNT = "도발"
    TORMENT = "트집"
    POWDER = "분진"
    PERISH_COUNT = "죽음의 카운트"
    DESTINY_BOND = "길동무"
    AQUA_RING = "아쿠아링"
    INGRAIN = "뿌리박기"
    CURSE = "저주"
    LEECH_SEED = "씨뿌리기"
    IN_FIRE = "불꽃속"
    IN_WATER = "물속"
    IN_GROUND = "땅속"
    IN_DARKNESS = "어둠속"
    TELEKINESIS = "텔레키네시스"
    FORESIGHT = "꿰뚫어보기"
    MIRACLE_EYE = "미라클아이"
    BOMB = "폭탄"
    MIND_READER = "마음의눈"
    HEAL_BLOCK = "회복봉인"
    BIND = "조이기"
    MEAN_LOOK = "검은눈빛"
    SUBSTITUTE = "대타출동"
    OUTRAGE = "난동부리기"
    TRANSFORM = "변신"
    FUTURE_SIGHT = "미래예지"


# ---------------------------------------------------------------------------
# Weather (날씨)
# ---------------------------------------------------------------------------

class Weather(str, Enum):
    """Weather conditions active on the field."""

    NONE = "없음"
    SUN = "쾌청"
    RAIN = "비"
    SANDSTORM = "모래바람"
    HAIL = "싸라기눈"


# ---------------------------------------------------------------------------
# Terrain (테라인 / 대지 설치, FE-02 / FE-04)
# ---------------------------------------------------------------------------

class Terrain(str, Enum):
    """Terrain effects (grounded persistent field effects, 「필드」)."""

    NONE = "없음"
    ELECTRIC = "일렉트릭필드"
    GRASSY = "그래스필드"
    MISTY = "미스트필드"
    PSYCHIC = "사이코필드"


# ---------------------------------------------------------------------------
# Field Effects (전체 설치, FE-01 / FE-03)
# ---------------------------------------------------------------------------

class FieldEffect(str, Enum):
    """Side or global field effects (barriers, rooms, winds, etc.)."""

    REFLECT = "리플렉터"
    LIGHT_SCREEN = "빛의장벽"
    AURORA_VEIL = "오로라베일"
    TRICK_ROOM = "트릭룸"
    TAILWIND = "테일윈드"
    STEALTH_ROCK = "스텔스록"
    SPIKES = "압정뿌리기"
    TOXIC_SPIKES = "독압정"
    STICKY_WEB = "끈적끈적네트"
    SAFEGUARD = "신비의부적"
    MIST = "흰안개"
    GRAVITY = "중력"
    MAGIC_ROOM = "매직룸"
    WONDER_ROOM = "원더룸"


# ---------------------------------------------------------------------------
# Special Field (《필드》, FE-06) — arena / alternate dimension
# ---------------------------------------------------------------------------

class SpecialField(str, Enum):
    """Special arena-type fields (《필드》).

    Distinct from Terrain (「필드」). These represent alternate dimensions
    or special battle arenas set by trainer or Pokémon potentials.
    """

    NONE = "없음"


# ---------------------------------------------------------------------------
# Potential categories
# ---------------------------------------------------------------------------

class PotentialCategory(str, Enum):
    """Potential slot categories for Pokémon (포텐셜 카테고리)."""

    ROLE = "역할"
    CLASSIFICATION = "분류"
    MASTER = "주인"
    ALIAS = "이명"
    TIER_1 = "계제 ①"
    TIER_2 = "계제 ②"
    TIER_3 = "계제 ③"
    TIER_4 = "계제 ④"
    AFFINITY = "속별"
    BOND = "유대"
    PREEMPTIVE = "선제"
    EVASION = "회피"
    RESISTANCE = "내성"
    STRIKE = "격"
    GENERAL = "범용"
    SECONDARY = "부수"
    PRIVILEGE = "특권"
    PT_1 = "PT ①"
    PT_2 = "PT ②"
    EXCLUSIVE = "전용포텐셜"


# Categories that every Pokémon always has.
ALWAYS_PRESENT_POTENTIALS: frozenset[PotentialCategory] = frozenset({
    PotentialCategory.TIER_1,
    PotentialCategory.TIER_2,
    PotentialCategory.AFFINITY,
    PotentialCategory.PREEMPTIVE,
    PotentialCategory.EVASION,
    PotentialCategory.RESISTANCE,
    PotentialCategory.STRIKE,
    PotentialCategory.GENERAL,
})

# Categories that vary depending on party allocation and training level.
VARIABLE_POTENTIALS: frozenset[PotentialCategory] = frozenset({
    PotentialCategory.ROLE,
    PotentialCategory.CLASSIFICATION,
    PotentialCategory.MASTER,
    PotentialCategory.ALIAS,
    PotentialCategory.TIER_3,
    PotentialCategory.TIER_4,
    PotentialCategory.BOND,
    PotentialCategory.SECONDARY,
    PotentialCategory.PRIVILEGE,
    PotentialCategory.PT_1,
    PotentialCategory.PT_2,
})


# ---------------------------------------------------------------------------
# Stat modification distinction: 강화 (reinforcement/multiplier) vs 상승 (rank stage)
# These are strictly separate per ST-02.
# ---------------------------------------------------------------------------

class StatModificationType(str, Enum):
    """How a stat is being modified — ST-02 strict distinction.

    REINFORCEMENT (강화): a direct multiplier applied to the stat value.
    RANK_CHANGE (상승/하락): a rank stage change (+1, -1, etc.) that uses
                            the standard rank multiplier table.
    """

    REINFORCEMENT = "강화"
    RANK_CHANGE = "상승"


# Standard rank stage multiplier table (Gen 5 basis).
# Stage -6 to +6. Accuracy/Evasion uses a different table.
STAT_RANK_STAGE_MULTIPLIERS: dict[int, float] = {
    -6: 2.0 / 8.0,
    -5: 2.0 / 7.0,
    -4: 2.0 / 6.0,
    -3: 2.0 / 5.0,
    -2: 2.0 / 4.0,
    -1: 2.0 / 3.0,
    0: 1.0,
    1: 3.0 / 2.0,
    2: 4.0 / 2.0,
    3: 5.0 / 2.0,
    4: 6.0 / 2.0,
    5: 7.0 / 2.0,
    6: 8.0 / 2.0,
}

# Accuracy / Evasion rank stage multiplier table.
ACCURACY_EVASION_STAGE_MULTIPLIERS: dict[int, float] = {
    -6: 3.0 / 9.0,
    -5: 3.0 / 8.0,
    -4: 3.0 / 7.0,
    -3: 3.0 / 6.0,
    -2: 3.0 / 5.0,
    -1: 3.0 / 4.0,
    0: 1.0,
    1: 4.0 / 3.0,
    2: 5.0 / 3.0,
    3: 6.0 / 3.0,
    4: 7.0 / 3.0,
    5: 8.0 / 3.0,
    6: 9.0 / 3.0,
}


# ---------------------------------------------------------------------------
# Critical hit probability table (5세대 기준)
# ---------------------------------------------------------------------------

# C+N -> probability (as fraction)
CRITICAL_HIT_PROBABILITY: dict[int, tuple[int, int]] = {
    0: (1, 16),
    1: (1, 8),
    2: (1, 4),
    3: (1, 3),
    4: (1, 2),
}

CRITICAL_HIT_MULTIPLIER: float = 2.0


# ---------------------------------------------------------------------------
# Gender
# ---------------------------------------------------------------------------

class Gender(str, Enum):
    """Pokémon gender."""

    MALE = "♂"
    FEMALE = "♀"
    GENDERLESS = "-"


# ---------------------------------------------------------------------------
# Action priority tiers
# ---------------------------------------------------------------------------

class ActionPriority(str, Enum):
    """Action order priority tiers (행동 순서)."""

    FASTEST = "가장 먼저"
    BEFORE_OPPONENT = "상대보다 먼저"
    PRIORITY = "우선도"
    SPEED = "속도"
