"""Party data model.

A party consists of a trainer + party members (P-01).
Default: 1 trainer + 6 members; party size is variable 1-8 (P-02).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from tunaed_pokemon.models.trainer import Trainer
from tunaed_pokemon.models.pokemon import Pokemon


# Default party size and limits.
DEFAULT_PARTY_SIZE = 6
MIN_PARTY_SIZE = 1
MAX_PARTY_SIZE = 8


@dataclass
class Party:
    """A party: one trainer and their Pokémon team.

    Attributes:
        id: Unique identifier.
        trainer: The trainer leading this party.
        members: List of Pokémon in the party.
        max_size: Maximum number of party members (default 6, may vary 1-8).
    """

    id: Optional[int] = None
    trainer: Trainer = field(default_factory=Trainer)
    members: list[Pokemon] = field(default_factory=list)
    max_size: int = DEFAULT_PARTY_SIZE

    @property
    def size(self) -> int:
        """Current number of party members."""
        return len(self.members)

    @property
    def is_full(self) -> bool:
        """Whether the party has reached its maximum size."""
        return self.size >= self.max_size

    def add_member(self, pokemon: Pokemon) -> None:
        """Add a Pokémon to the party.

        Raises:
            ValueError: If the party is already full.
        """
        if self.is_full:
            raise ValueError(
                f"Party is full ({self.max_size} members maximum)."
            )
        self.members.append(pokemon)

    def remove_member(self, index: int) -> Pokemon:
        """Remove and return a Pokémon by index.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= self.size:
            raise IndexError(f"Index {index} out of range (party size {self.size}).")
        return self.members.pop(index)
