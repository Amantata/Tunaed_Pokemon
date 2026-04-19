"""Field state manager.

Tracks weather, terrain, barriers, global effects, and special fields.
Satisfies: FE-01 (barriers), FE-02 (terrain), FE-03 (global field moves),
           FE-04 (persistent field effects), FE-05 (weather), FE-06 (special fields).

Important: 《필드》 (SpecialField, FE-06) and 「필드」 (Terrain, FE-04) are
different concepts and are tracked separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from tunaed_pokemon.models.enums import (
    FieldEffect,
    SpecialField,
    Terrain,
    Weather,
)


@dataclass
class SideFieldState:
    """Field effects on one side of the battle (e.g. player A's side).

    Tracks barriers (FE-01), entry hazards, and side-specific effects.
    Each effect has an optional remaining turn count.
    """

    # Active effects -> remaining turns (None = indefinite until removed).
    effects: dict[FieldEffect, Optional[int]] = field(default_factory=dict)

    def set_effect(self, effect: FieldEffect, turns: Optional[int] = None) -> None:
        """Set a side field effect with optional turn duration."""
        self.effects[effect] = turns

    def remove_effect(self, effect: FieldEffect) -> bool:
        """Remove a side field effect. Returns True if it was present."""
        if effect in self.effects:
            del self.effects[effect]
            return True
        return False

    def has_effect(self, effect: FieldEffect) -> bool:
        """Check if an effect is active on this side."""
        return effect in self.effects

    def tick(self) -> list[FieldEffect]:
        """Decrement turn counters; return list of expired effects."""
        expired: list[FieldEffect] = []
        to_remove: list[FieldEffect] = []
        for effect, turns in self.effects.items():
            if turns is not None:
                remaining = turns - 1
                if remaining <= 0:
                    expired.append(effect)
                    to_remove.append(effect)
                else:
                    self.effects[effect] = remaining
        for effect in to_remove:
            del self.effects[effect]
        return expired

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {e.value: t for e, t in self.effects.items()}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SideFieldState:
        """Deserialize from dict."""
        state = cls()
        for name, turns in d.items():
            state.effects[FieldEffect(name)] = turns
        return state


@dataclass
class GlobalFieldState:
    """Global field effects (FE-03) that affect the entire battlefield.

    E.g. Trick Room, Gravity — these are not side-specific.
    """

    effects: dict[FieldEffect, Optional[int]] = field(default_factory=dict)

    def set_effect(self, effect: FieldEffect, turns: Optional[int] = None) -> None:
        """Set a global field effect."""
        self.effects[effect] = turns

    def remove_effect(self, effect: FieldEffect) -> bool:
        """Remove a global field effect. Returns True if it was present."""
        if effect in self.effects:
            del self.effects[effect]
            return True
        return False

    def has_effect(self, effect: FieldEffect) -> bool:
        """Check if a global effect is active."""
        return effect in self.effects

    def tick(self) -> list[FieldEffect]:
        """Decrement turn counters; return list of expired effects."""
        expired: list[FieldEffect] = []
        to_remove: list[FieldEffect] = []
        for effect, turns in self.effects.items():
            if turns is not None:
                remaining = turns - 1
                if remaining <= 0:
                    expired.append(effect)
                    to_remove.append(effect)
                else:
                    self.effects[effect] = remaining
        for effect in to_remove:
            del self.effects[effect]
        return expired

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {e.value: t for e, t in self.effects.items()}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GlobalFieldState:
        """Deserialize from dict."""
        state = cls()
        for name, turns in d.items():
            state.effects[FieldEffect(name)] = turns
        return state


# Side-specific effects (barriers, entry hazards).
SIDE_EFFECTS: frozenset[FieldEffect] = frozenset({
    FieldEffect.REFLECT,
    FieldEffect.LIGHT_SCREEN,
    FieldEffect.AURORA_VEIL,
    FieldEffect.STEALTH_ROCK,
    FieldEffect.SPIKES,
    FieldEffect.TOXIC_SPIKES,
    FieldEffect.STICKY_WEB,
    FieldEffect.SAFEGUARD,
    FieldEffect.MIST,
    FieldEffect.TAILWIND,
})

# Global effects (rooms, gravity).
GLOBAL_EFFECTS: frozenset[FieldEffect] = frozenset({
    FieldEffect.TRICK_ROOM,
    FieldEffect.GRAVITY,
    FieldEffect.MAGIC_ROOM,
    FieldEffect.WONDER_ROOM,
})


@dataclass
class FieldStateManager:
    """Manages all field environment states for the battle.

    Tracks:
    - Weather (FE-05): one active weather at a time
    - Terrain/「필드」(FE-02/FE-04): one active terrain at a time
    - Side effects (FE-01): per-side barriers, hazards, etc.
    - Global effects (FE-03): rooms, gravity, etc.
    - Special field/《필드》(FE-06): alternate dimension / arena

    Note: 《필드》 and 「필드」 are distinct concepts.
    """

    # FE-05: Weather
    weather: Weather = Weather.NONE
    weather_turns: Optional[int] = None  # None = indefinite (e.g. ability-set)

    # FE-02/FE-04: Terrain (「필드」)
    terrain: Terrain = Terrain.NONE
    terrain_turns: Optional[int] = None

    # FE-01: Side field effects (barriers, hazards)
    side_a: SideFieldState = field(default_factory=SideFieldState)
    side_b: SideFieldState = field(default_factory=SideFieldState)

    # FE-03: Global field effects (rooms, gravity)
    global_effects: GlobalFieldState = field(default_factory=GlobalFieldState)

    # FE-06: Special field (《필드》)
    special_field: SpecialField = SpecialField.NONE
    special_field_turns: Optional[int] = None

    def set_weather(self, weather: Weather, turns: Optional[int] = 5) -> Weather:
        """Set the weather. Returns the previous weather.

        Args:
            weather: New weather to set.
            turns: Number of turns (None for indefinite, e.g. ability-set).

        Returns:
            The weather that was replaced.
        """
        previous = self.weather
        self.weather = weather
        self.weather_turns = turns
        return previous

    def clear_weather(self) -> Weather:
        """Clear the weather. Returns the weather that was cleared."""
        previous = self.weather
        self.weather = Weather.NONE
        self.weather_turns = None
        return previous

    def set_terrain(self, terrain: Terrain, turns: Optional[int] = 5) -> Terrain:
        """Set the terrain (「필드」). Returns the previous terrain."""
        previous = self.terrain
        self.terrain = terrain
        self.terrain_turns = turns
        return previous

    def clear_terrain(self) -> Terrain:
        """Clear the terrain. Returns the terrain that was cleared."""
        previous = self.terrain
        self.terrain = Terrain.NONE
        self.terrain_turns = None
        return previous

    def set_special_field(
        self, special: SpecialField, turns: Optional[int] = None
    ) -> SpecialField:
        """Set the special field (《필드》). Returns the previous one."""
        previous = self.special_field
        self.special_field = special
        self.special_field_turns = turns
        return previous

    def get_side(self, side: int) -> SideFieldState:
        """Get the field state for a side (0=A, 1=B)."""
        if side == 0:
            return self.side_a
        return self.side_b

    def tick(self) -> dict[str, Any]:
        """Process end-of-turn for all field states.

        Decrements turn counters and removes expired effects.

        Returns:
            Dict describing what expired this turn.
        """
        expired: dict[str, Any] = {}

        # Weather tick
        if self.weather != Weather.NONE and self.weather_turns is not None:
            self.weather_turns -= 1
            if self.weather_turns <= 0:
                expired["weather"] = self.weather.value
                self.weather = Weather.NONE
                self.weather_turns = None

        # Terrain tick
        if self.terrain != Terrain.NONE and self.terrain_turns is not None:
            self.terrain_turns -= 1
            if self.terrain_turns <= 0:
                expired["terrain"] = self.terrain.value
                self.terrain = Terrain.NONE
                self.terrain_turns = None

        # Special field tick
        if (
            self.special_field != SpecialField.NONE
            and self.special_field_turns is not None
        ):
            self.special_field_turns -= 1
            if self.special_field_turns <= 0:
                expired["special_field"] = self.special_field.value
                self.special_field = SpecialField.NONE
                self.special_field_turns = None

        # Side effects tick
        expired_a = self.side_a.tick()
        if expired_a:
            expired["side_a"] = [e.value for e in expired_a]

        expired_b = self.side_b.tick()
        if expired_b:
            expired["side_b"] = [e.value for e in expired_b]

        # Global effects tick
        expired_global = self.global_effects.tick()
        if expired_global:
            expired["global"] = [e.value for e in expired_global]

        return expired

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete field state to a dict."""
        return {
            "weather": self.weather.value,
            "weather_turns": self.weather_turns,
            "terrain": self.terrain.value,
            "terrain_turns": self.terrain_turns,
            "special_field": self.special_field.value,
            "special_field_turns": self.special_field_turns,
            "side_a": self.side_a.to_dict(),
            "side_b": self.side_b.to_dict(),
            "global_effects": self.global_effects.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FieldStateManager:
        """Deserialize from a dict."""
        mgr = cls()
        mgr.weather = Weather(d.get("weather", "없음"))
        mgr.weather_turns = d.get("weather_turns")
        mgr.terrain = Terrain(d.get("terrain", "없음"))
        mgr.terrain_turns = d.get("terrain_turns")
        mgr.special_field = SpecialField(d.get("special_field", "없음"))
        mgr.special_field_turns = d.get("special_field_turns")
        mgr.side_a = SideFieldState.from_dict(d.get("side_a", {}))
        mgr.side_b = SideFieldState.from_dict(d.get("side_b", {}))
        mgr.global_effects = GlobalFieldState.from_dict(d.get("global_effects", {}))
        return mgr
