"""Pokémon data model.

Represents a party member (Pokémon) with stats, potentials, moves,
ability, and exclusive potential (전용포텐셜).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from tunaed_pokemon.models.enums import (
    Gender,
    PokemonType,
    PotentialCategory,
    StatType,
    BASE_STAT_TYPES,
)


@dataclass
class PokemonStats:
    """Six-stat block for a Pokémon.

    Each stat has a base value (종족치), individual value (개체치, IV),
    and effort value (노력치, EV — defaults to 0 per ST-01).
    """

    base: dict[StatType, int] = field(
        default_factory=lambda: {s: 0 for s in BASE_STAT_TYPES}
    )
    iv: dict[StatType, int] = field(
        default_factory=lambda: {s: 0 for s in BASE_STAT_TYPES}
    )
    ev: dict[StatType, int] = field(
        default_factory=lambda: {s: 0 for s in BASE_STAT_TYPES}
    )

    @property
    def total_base(self) -> int:
        """Sum of all base stat values (종족치 총합)."""
        return sum(self.base.values())


@dataclass
class PotentialSlot:
    """A single potential slot for a Pokémon.

    Attributes:
        category: Which potential slot this is (역할, 계제①, etc.).
        name: Display name of the potential.
        description: Full effect text.
        effect_script: Python snippet for sandbox execution.
    """

    category: PotentialCategory
    name: str = ""
    description: str = ""
    effect_script: str = ""


@dataclass
class ExclusivePotential:
    """Pokémon-exclusive potential (전용포텐셜).

    Particularly powerful potential that is hidden from normal encyclopedia.
    Stored separately from regular potentials (per PT-05).
    """

    name: str = ""
    description: str = ""
    effect_script: str = ""


@dataclass
class PokemonPotentials:
    """All potential slots for a Pokémon, including 전용포텐셜."""

    slots: dict[PotentialCategory, PotentialSlot] = field(default_factory=dict)
    exclusive: ExclusivePotential = field(default_factory=ExclusivePotential)

    def get(self, category: PotentialCategory) -> Optional[PotentialSlot]:
        """Get a potential slot by category, or None if not set."""
        return self.slots.get(category)

    def set_slot(self, slot: PotentialSlot) -> None:
        """Set or overwrite a potential slot."""
        self.slots[slot.category] = slot


@dataclass
class Pokemon:
    """A Pokémon (party member / 파티원).

    Attributes:
        id: Unique identifier.
        species: Species name.
        name: Nickname (may differ from species).
        gender: Gender (♂, ♀, or genderless).
        is_alien_species: 아인종 여부 (variant species flag).
        type1: Primary type.
        type2: Secondary type (None if single-type).
        ability_id: Reference to the Ability master table.
        ability_name: Denormalized ability name for display.
        level: Pokémon level.
        image_path: Path to Pokémon illustration image.
        stats: Six-stat block with base/IV/EV.
        moves: List of move IDs this Pokémon knows.
        extended_moves: Additional moves granted by 기능확장 potential.
        potentials: All potential slots.
    """

    id: Optional[int] = None
    species: str = ""
    name: str = ""
    gender: Gender = Gender.GENDERLESS
    is_alien_species: bool = False
    type1: PokemonType = PokemonType.NORMAL
    type2: Optional[PokemonType] = None
    ability_id: Optional[int] = None
    ability_name: str = ""
    level: int = 50
    image_path: str = ""
    stats: PokemonStats = field(default_factory=PokemonStats)
    moves: list[int] = field(default_factory=list)
    extended_moves: list[int] = field(default_factory=list)
    potentials: PokemonPotentials = field(default_factory=PokemonPotentials)

    @property
    def types(self) -> list[PokemonType]:
        """Return list of types (1 or 2)."""
        if self.type2 is not None:
            return [self.type1, self.type2]
        return [self.type1]

    @property
    def max_move_count(self) -> int:
        """Maximum number of moves based on total base stat.

        4 base, +1 for every 50 total base above a threshold (up to 8).
        This is a simplified heuristic; actual formula may vary.
        """
        total = self.stats.total_base
        if total >= 600:
            return 8
        if total >= 500:
            return 7
        if total >= 400:
            return 6
        if total >= 300:
            return 5
        return 4
