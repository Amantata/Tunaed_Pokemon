"""Item validator.

Enforces item rules from docs/소지품목록.md and docs/기본 규칙.md:
- No duplicate items within a party (쥬얼/플레이트 allowed if different types).
- Banned items check.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tunaed_pokemon.models.item import Item


# Items that are always banned from play.
BANNED_ITEM_NAMES: frozenset[str] = frozenset({
    "진화의휘석",
    "약점보험",
    "돌격조끼",
    "파괴의유전자",
})


@dataclass
class ItemValidationError:
    """Describes an item validation failure."""

    message: str
    pokemon_index: Optional[int] = None
    item_name: str = ""


def validate_item_not_banned(item: Item) -> Optional[ItemValidationError]:
    """Check if an item is banned from play.

    Returns an error if the item is banned, None if OK.
    """
    if item.is_banned or item.name in BANNED_ITEM_NAMES:
        return ItemValidationError(
            message=f"Item '{item.name}' is banned from play.",
            item_name=item.name,
        )
    return None


def validate_party_items(items: list[tuple[int, Item]]) -> list[ItemValidationError]:
    """Validate all items in a party for duplicates and bans.

    Args:
        items: List of (pokemon_index, item) tuples for each party member.

    Returns:
        List of validation errors (empty if all OK).

    Rules:
    - No duplicate items within a party.
    - Exception: Jewels (쥬얼) and Plates (플레이트) are allowed if they
      are of different types (e.g. fire jewel + water jewel is OK).
    """
    errors: list[ItemValidationError] = []

    # Check bans
    for idx, item in items:
        err = validate_item_not_banned(item)
        if err is not None:
            err.pokemon_index = idx
            errors.append(err)

    # Check duplicates
    seen: dict[str, int] = {}  # item_name -> first pokemon_index
    for idx, item in items:
        if not item.name:
            continue

        # For jewels/plates, include type to allow different types.
        if item.is_jewel or item.is_plate:
            type_suffix = f":{item.jewel_plate_type.value}" if item.jewel_plate_type else ""
            key = f"{item.name}{type_suffix}"
        else:
            key = item.name

        if key in seen:
            errors.append(ItemValidationError(
                message=(
                    f"Duplicate item '{item.name}' on Pokémon #{idx} "
                    f"(first on #{seen[key]})."
                ),
                pokemon_index=idx,
                item_name=item.name,
            ))
        else:
            seen[key] = idx

    return errors
