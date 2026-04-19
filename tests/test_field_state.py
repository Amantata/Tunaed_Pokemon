"""Tests for the FieldStateManager."""

from tunaed_pokemon.engine.field_state import (
    FieldStateManager,
    GlobalFieldState,
    SideFieldState,
    SIDE_EFFECTS,
    GLOBAL_EFFECTS,
)
from tunaed_pokemon.models.enums import (
    FieldEffect,
    SpecialField,
    Terrain,
    Weather,
)


class TestSideFieldState:
    """Tests for side-specific field effects (FE-01)."""

    def test_set_and_check_effect(self):
        side = SideFieldState()
        side.set_effect(FieldEffect.REFLECT, turns=5)
        assert side.has_effect(FieldEffect.REFLECT)
        assert not side.has_effect(FieldEffect.LIGHT_SCREEN)

    def test_remove_effect(self):
        side = SideFieldState()
        side.set_effect(FieldEffect.REFLECT, turns=5)
        assert side.remove_effect(FieldEffect.REFLECT)
        assert not side.has_effect(FieldEffect.REFLECT)
        assert not side.remove_effect(FieldEffect.REFLECT)

    def test_tick_decrements_and_expires(self):
        side = SideFieldState()
        side.set_effect(FieldEffect.REFLECT, turns=2)
        side.set_effect(FieldEffect.LIGHT_SCREEN, turns=1)

        expired = side.tick()
        assert FieldEffect.LIGHT_SCREEN in expired
        assert FieldEffect.REFLECT not in expired
        assert side.has_effect(FieldEffect.REFLECT)
        assert not side.has_effect(FieldEffect.LIGHT_SCREEN)

    def test_tick_indefinite_effect_persists(self):
        side = SideFieldState()
        side.set_effect(FieldEffect.STEALTH_ROCK, turns=None)
        expired = side.tick()
        assert len(expired) == 0
        assert side.has_effect(FieldEffect.STEALTH_ROCK)

    def test_serialize_deserialize(self):
        side = SideFieldState()
        side.set_effect(FieldEffect.REFLECT, turns=3)
        side.set_effect(FieldEffect.STEALTH_ROCK, turns=None)
        d = side.to_dict()
        restored = SideFieldState.from_dict(d)
        assert restored.has_effect(FieldEffect.REFLECT)
        assert restored.has_effect(FieldEffect.STEALTH_ROCK)


class TestGlobalFieldState:
    """Tests for global field effects (FE-03)."""

    def test_trick_room(self):
        gfs = GlobalFieldState()
        gfs.set_effect(FieldEffect.TRICK_ROOM, turns=5)
        assert gfs.has_effect(FieldEffect.TRICK_ROOM)

    def test_gravity(self):
        gfs = GlobalFieldState()
        gfs.set_effect(FieldEffect.GRAVITY, turns=5)
        assert gfs.has_effect(FieldEffect.GRAVITY)
        gfs.remove_effect(FieldEffect.GRAVITY)
        assert not gfs.has_effect(FieldEffect.GRAVITY)


class TestFieldStateManager:
    """Tests for the full FieldStateManager."""

    def test_weather(self):
        mgr = FieldStateManager()
        assert mgr.weather == Weather.NONE

        old = mgr.set_weather(Weather.SUN, turns=5)
        assert old == Weather.NONE
        assert mgr.weather == Weather.SUN

        old = mgr.set_weather(Weather.RAIN, turns=5)
        assert old == Weather.SUN
        assert mgr.weather == Weather.RAIN

    def test_clear_weather(self):
        mgr = FieldStateManager()
        mgr.set_weather(Weather.SANDSTORM)
        cleared = mgr.clear_weather()
        assert cleared == Weather.SANDSTORM
        assert mgr.weather == Weather.NONE

    def test_terrain_distinct_from_special_field(self):
        """FE-04 (「필드」) and FE-06 (《필드》) are tracked separately."""
        mgr = FieldStateManager()

        mgr.set_terrain(Terrain.ELECTRIC, turns=5)
        mgr.set_special_field(SpecialField.NONE)

        assert mgr.terrain == Terrain.ELECTRIC
        assert mgr.special_field == SpecialField.NONE

        # Changing terrain doesn't affect special field.
        mgr.clear_terrain()
        assert mgr.terrain == Terrain.NONE

    def test_terrain(self):
        mgr = FieldStateManager()
        old = mgr.set_terrain(Terrain.GRASSY, turns=5)
        assert old == Terrain.NONE
        assert mgr.terrain == Terrain.GRASSY
        cleared = mgr.clear_terrain()
        assert cleared == Terrain.GRASSY
        assert mgr.terrain == Terrain.NONE

    def test_side_effects(self):
        mgr = FieldStateManager()
        mgr.side_a.set_effect(FieldEffect.REFLECT, turns=5)
        mgr.side_b.set_effect(FieldEffect.STEALTH_ROCK)

        assert mgr.get_side(0).has_effect(FieldEffect.REFLECT)
        assert mgr.get_side(1).has_effect(FieldEffect.STEALTH_ROCK)

    def test_global_effects(self):
        mgr = FieldStateManager()
        mgr.global_effects.set_effect(FieldEffect.TRICK_ROOM, turns=5)
        assert mgr.global_effects.has_effect(FieldEffect.TRICK_ROOM)

    def test_tick_weather_expires(self):
        mgr = FieldStateManager()
        mgr.set_weather(Weather.HAIL, turns=1)
        expired = mgr.tick()
        assert "weather" in expired
        assert mgr.weather == Weather.NONE

    def test_tick_terrain_expires(self):
        mgr = FieldStateManager()
        mgr.set_terrain(Terrain.PSYCHIC, turns=1)
        expired = mgr.tick()
        assert "terrain" in expired
        assert mgr.terrain == Terrain.NONE

    def test_tick_indefinite_weather_persists(self):
        mgr = FieldStateManager()
        mgr.set_weather(Weather.SUN, turns=None)
        expired = mgr.tick()
        assert "weather" not in expired
        assert mgr.weather == Weather.SUN

    def test_serialize_deserialize(self):
        mgr = FieldStateManager()
        mgr.set_weather(Weather.RAIN, turns=3)
        mgr.set_terrain(Terrain.ELECTRIC, turns=5)
        mgr.side_a.set_effect(FieldEffect.REFLECT, turns=2)
        mgr.global_effects.set_effect(FieldEffect.TRICK_ROOM, turns=4)

        d = mgr.to_dict()
        restored = FieldStateManager.from_dict(d)

        assert restored.weather == Weather.RAIN
        assert restored.weather_turns == 3
        assert restored.terrain == Terrain.ELECTRIC
        assert restored.side_a.has_effect(FieldEffect.REFLECT)
        assert restored.global_effects.has_effect(FieldEffect.TRICK_ROOM)

    def test_effect_categories(self):
        """Verify side vs global effect categorization."""
        assert FieldEffect.REFLECT in SIDE_EFFECTS
        assert FieldEffect.TRICK_ROOM in GLOBAL_EFFECTS
        assert FieldEffect.GRAVITY in GLOBAL_EFFECTS
        assert FieldEffect.STEALTH_ROCK in SIDE_EFFECTS
