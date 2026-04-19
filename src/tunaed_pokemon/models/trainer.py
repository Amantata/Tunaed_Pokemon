"""Trainer data model.

Represents a trainer with qualities (자질), command potentials (지령 포텐셜),
and unique potentials (고유포텐셜).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from tunaed_pokemon.models.enums import QualityRank


@dataclass
class TrainerQualities:
    """Four trainer qualities (자질): 지시, 통솔, 육성, 능력.

    At creation, distribute up to 34 (or 26) points across 4 qualities.
    Points per rank: E=0, D=2, C=4, B=6, A=10, AA=14, AAA=20, S=26.
    """

    command: QualityRank = QualityRank.E       # 지시
    leadership: QualityRank = QualityRank.E    # 통솔
    nurturing: QualityRank = QualityRank.E     # 육성
    ability: QualityRank = QualityRank.E       # 능력

    @property
    def command_kr(self) -> str:
        return f"지시：「{self.command.value}」"

    @property
    def leadership_kr(self) -> str:
        return f"통솔：「{self.leadership.value}」"

    @property
    def nurturing_kr(self) -> str:
        return f"육성：「{self.nurturing.value}」"

    @property
    def ability_kr(self) -> str:
        return f"능력：「{self.ability.value}」"


@dataclass
class CommandPotential:
    """A single command potential (지령 포텐셜).

    Attributes:
        name: Display name enclosed in 『』, e.g. 『물러나！』.
        description: Full effect text.
        uses_per_battle: Number of uses per battle (e.g. 1).
        timing: When the command can be used (선행, 임의, T시, etc.).
    """

    name: str
    description: str
    uses_per_battle: int = 1
    timing: str = ""


# Pre-defined basic 4 command potentials (기본 4식).
BASIC_COMMANDS: list[CommandPotential] = [
    CommandPotential(
        name="물러나！",
        description="1/시/선행/아군 포켓몬 1체에게의 「물리 기술」을 회피시킨다.",
        uses_per_battle=1,
        timing="선행",
    ),
    CommandPotential(
        name="피해라！",
        description="1/시/선행/아군 포켓몬 1체에게의 「특수 기술」을 회피시킨다.",
        uses_per_battle=1,
        timing="선행",
    ),
    CommandPotential(
        name="돌아와！",
        description="1/시/임의/아군의 통상 교대 시, 상대의 행동 후에 아군 포켓몬을 필드에 낼 수 있다.",
        uses_per_battle=1,
        timing="임의",
    ),
    CommandPotential(
        name="버텨라！",
        description="1/시/임의/아군 포켓몬 1체에게의 상대의 기술의 데미지를 반감해, 반드시 버틴다.",
        uses_per_battle=1,
        timing="임의",
    ),
]


@dataclass
class InnatePotential:
    """Trainer-unique potential (고유포텐셜).

    Every trainer has different 고유포텐셜.  This is separate from
    전용포텐셜 (Pokémon exclusive potential).
    """

    name: str
    description: str
    effect_script: str = ""


@dataclass
class Trainer:
    """A trainer (트레이너).

    Attributes:
        id: Unique identifier.
        name: Trainer name (이름).
        alias: Trainer alias/title (별칭).
        origin: Origin/hometown (출신).
        career: Career / background (경력).
        image_path: Path to trainer illustration image.
        qualities: The four quality ranks.
        command_potentials: Command potentials available to this trainer.
        innate_potentials: 고유포텐셜 — unique to this trainer.
    """

    id: Optional[int] = None
    name: str = ""
    alias: str = ""
    origin: str = ""
    career: str = ""
    image_path: str = ""
    qualities: TrainerQualities = field(default_factory=TrainerQualities)
    command_potentials: list[CommandPotential] = field(
        default_factory=lambda: list(BASIC_COMMANDS)
    )
    innate_potentials: list[InnatePotential] = field(default_factory=list)
