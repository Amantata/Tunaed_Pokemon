"""Tests for ItemValidator."""

from tunaed_pokemon.models.enums import PokemonType
from tunaed_pokemon.models.item import Item
from tunaed_pokemon.utils.item_validator import (
    BANNED_ITEM_NAMES,
    validate_item_not_banned,
    validate_party_items,
)


class TestItemValidator:
    """Tests for item validation rules."""

    def test_banned_item_detected(self):
        item = Item(name="진화의휘석")
        err = validate_item_not_banned(item)
        assert err is not None
        assert "banned" in err.message

    def test_banned_item_flag(self):
        item = Item(name="custom_banned", is_banned=True)
        err = validate_item_not_banned(item)
        assert err is not None

    def test_normal_item_passes(self):
        item = Item(name="기합의머리띠")
        err = validate_item_not_banned(item)
        assert err is None

    def test_duplicate_items_detected(self):
        items = [
            (0, Item(name="기합의머리띠")),
            (1, Item(name="기합의머리띠")),
        ]
        errors = validate_party_items(items)
        assert any("Duplicate" in e.message for e in errors)

    def test_no_duplicates_when_unique(self):
        items = [
            (0, Item(name="기합의머리띠")),
            (1, Item(name="구슬목걸이")),
        ]
        errors = validate_party_items(items)
        assert len(errors) == 0

    def test_jewels_different_types_allowed(self):
        items = [
            (0, Item(name="불꽃쥬얼", is_jewel=True, jewel_plate_type=PokemonType.FIRE)),
            (1, Item(name="불꽃쥬얼", is_jewel=True, jewel_plate_type=PokemonType.WATER)),
        ]
        errors = validate_party_items(items)
        duplicate_errors = [e for e in errors if "Duplicate" in e.message]
        assert len(duplicate_errors) == 0

    def test_jewels_same_type_rejected(self):
        items = [
            (0, Item(name="불꽃쥬얼", is_jewel=True, jewel_plate_type=PokemonType.FIRE)),
            (1, Item(name="불꽃쥬얼", is_jewel=True, jewel_plate_type=PokemonType.FIRE)),
        ]
        errors = validate_party_items(items)
        duplicate_errors = [e for e in errors if "Duplicate" in e.message]
        assert len(duplicate_errors) == 1

    def test_plates_different_types_allowed(self):
        items = [
            (0, Item(name="플레이트", is_plate=True, jewel_plate_type=PokemonType.FIRE)),
            (1, Item(name="플레이트", is_plate=True, jewel_plate_type=PokemonType.WATER)),
        ]
        errors = validate_party_items(items)
        duplicate_errors = [e for e in errors if "Duplicate" in e.message]
        assert len(duplicate_errors) == 0

    def test_banned_and_duplicate_combined(self):
        items = [
            (0, Item(name="약점보험")),
            (1, Item(name="기합의머리띠")),
            (2, Item(name="기합의머리띠")),
        ]
        errors = validate_party_items(items)
        assert len(errors) >= 2  # At least one ban + one duplicate

    def test_empty_item_names_skipped(self):
        items = [
            (0, Item(name="")),
            (1, Item(name="")),
        ]
        errors = validate_party_items(items)
        assert len(errors) == 0

    def test_known_banned_items(self):
        """Verify all known banned items are in the list."""
        assert "진화의휘석" in BANNED_ITEM_NAMES
        assert "약점보험" in BANNED_ITEM_NAMES
        assert "돌격조끼" in BANNED_ITEM_NAMES
        assert "파괴의유전자" in BANNED_ITEM_NAMES
