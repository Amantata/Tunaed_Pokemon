"""Move (기술) data model.

Moves are selected from a master list that is editable via in-app editor (SK-01).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from tunaed_pokemon.models.enums import MoveCategory, MoveContact, PokemonType


@dataclass
class Move:
    """A single move (기술) in the master list.

    Attributes:
        id: Unique identifier.
        name: Move name.
        type: Pokémon type of the move.
        category: Physical / Special / Status.
        contact: Contact or non-contact.
        power: Base power (None for status moves).
        accuracy: Base accuracy percentage (None if always-hit).
        pp: Power Points.
        priority: Priority bracket (0 = normal, +1/−1, etc.).
        effect_description: Human-readable effect text.
        effect_script: Python snippet for sandbox execution.
        is_sound: Whether this is a sound-based move.
        is_punch: Whether this is a punch-based move.
        is_blade: Whether this is a blade/cut-based move.
        additional_flags: Any other special flags as a list.
    """

    id: Optional[int] = None
    name: str = ""
    type: PokemonType = PokemonType.NORMAL
    category: MoveCategory = MoveCategory.PHYSICAL
    contact: MoveContact = MoveContact.CONTACT
    power: Optional[int] = None
    accuracy: Optional[int] = None
    pp: int = 5
    priority: int = 0
    effect_description: str = ""
    effect_script: str = ""
    is_sound: bool = False
    is_punch: bool = False
    is_blade: bool = False
    additional_flags: list[str] = field(default_factory=list)
