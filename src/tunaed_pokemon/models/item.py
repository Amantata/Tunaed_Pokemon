"""Item (소지품) data model.

Items follow the rules in docs/소지품목록.md:
- No duplicate items within a party (except Jewels/Plates of different types).
- Several items are banned (진화의휘석, 약점보험, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tunaed_pokemon.models.enums import PokemonType


@dataclass
class Item:
    """A single held item (소지품).

    Attributes:
        id: Unique identifier.
        name: Item name.
        effect_description: Human-readable effect text.
        effect_script: Python snippet for sandbox execution.
        is_banned: Whether this item is banned from play.
        is_berry: Whether this item is a berry (열매).
        is_jewel: Whether this is a type-jewel (쥬얼).
        is_plate: Whether this is a type-plate (플레이트).
        jewel_plate_type: If jewel/plate, which type it boosts.
        is_consumable: Whether this item is consumed on use.
    """

    id: Optional[int] = None
    name: str = ""
    effect_description: str = ""
    effect_script: str = ""
    is_banned: bool = False
    is_berry: bool = False
    is_jewel: bool = False
    is_plate: bool = False
    jewel_plate_type: Optional[PokemonType] = None
    is_consumable: bool = False
