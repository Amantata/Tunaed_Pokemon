"""Field environment state manager (FE-01 through FE-06)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models.enums import Weather, Terrain, SpecialField


@dataclass
class SideFieldState:
    """Per-side field state: barriers (FE-01) and hazards."""
    barriers: dict[str, int] = field(default_factory=dict)   # name → turns remaining
    hazards: dict[str, int] = field(default_factory=dict)    # name → layer count

    def to_dict(self) -> dict[str, Any]:
        return {"barriers": dict(self.barriers), "hazards": dict(self.hazards)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SideFieldState":
        obj = cls()
        obj.barriers = dict(d.get("barriers", {}))
        obj.hazards = dict(d.get("hazards", {}))
        return obj

    def set_barrier(self, name: str, turns: int) -> None:
        self.barriers[name] = turns

    def tick_barriers(self) -> list[str]:
        """Decrement barrier turns. Returns list of expired barrier names."""
        expired = [k for k, v in self.barriers.items() if v <= 1]
        for k in expired:
            del self.barriers[k]
        for k in list(self.barriers):
            self.barriers[k] -= 1
        return expired

    def add_hazard(self, name: str, max_layers: int = 3) -> bool:
        """Add one hazard layer. Returns True if added."""
        current = self.hazards.get(name, 0)
        if current < max_layers:
            self.hazards[name] = current + 1
            return True
        return False

    def clear_hazards(self) -> None:
        self.hazards.clear()


@dataclass
class FieldStateManager:
    """Manages all field environment states.

    Tracks:
    - FE-01: Barriers per side (Reflect/Light Screen/Aurora Veil)
    - FE-02/FE-04: Terrain / 「필드」 effects (Electric, Grassy, Misty, Psychic)
    - FE-03: Global effects (Trick Room, Tailwind, Gravity, etc.)
    - FE-05: Weather
    - FE-06: 《필드》 Special arena/dimension (distinct from Terrain/「필드」)
    """
    # FE-05 Weather
    weather: str = Weather.NONE.value
    weather_turns: int = 0

    # FE-02/FE-04 「필드」 Terrain/field effect
    terrain: str = Terrain.NONE.value
    terrain_turns: int = 0

    # FE-03 Global effects (Trick Room, Tailwind, Gravity, etc.)
    global_effects: dict[str, int] = field(default_factory=dict)  # name → turns

    # FE-01 Per-side barriers and hazards
    side1: SideFieldState = field(default_factory=SideFieldState)
    side2: SideFieldState = field(default_factory=SideFieldState)

    # FE-06 《필드》 special arena (entirely separate from Terrain)
    special_field: str = SpecialField.NONE.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "weather": self.weather,
            "weather_turns": self.weather_turns,
            "terrain": self.terrain,
            "terrain_turns": self.terrain_turns,
            "global_effects": dict(self.global_effects),
            "side1": self.side1.to_dict(),
            "side2": self.side2.to_dict(),
            "special_field": self.special_field,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "FieldStateManager":
        obj = cls()
        obj.weather = d.get("weather", Weather.NONE.value)
        obj.weather_turns = d.get("weather_turns", 0)
        obj.terrain = d.get("terrain", Terrain.NONE.value)
        obj.terrain_turns = d.get("terrain_turns", 0)
        obj.global_effects = dict(d.get("global_effects", {}))
        obj.side1 = SideFieldState.from_dict(d.get("side1", {}))
        obj.side2 = SideFieldState.from_dict(d.get("side2", {}))
        obj.special_field = d.get("special_field", SpecialField.NONE.value)
        return obj

    # ── Setters ──────────────────────────────────────────────────────────────

    def set_weather(self, weather: Weather, turns: int = 5) -> None:
        self.weather = weather.value
        self.weather_turns = turns

    def set_terrain(self, terrain: Terrain, turns: int = 5) -> None:
        """FE-02/FE-04: set a 「필드」 terrain/field effect."""
        self.terrain = terrain.value
        self.terrain_turns = turns

    def set_global_effect(self, name: str, turns: int) -> None:
        """FE-03: set a global field effect (Trick Room, Tailwind, etc.)."""
        self.global_effects[name] = turns

    def set_special_field(self, sf: SpecialField) -> None:
        """FE-06: set the 《필드》 special arena."""
        self.special_field = sf.value

    def get_side(self, side: int) -> SideFieldState:
        return self.side1 if side == 1 else self.side2

    # ── Turn tick ────────────────────────────────────────────────────────────

    def tick(self) -> list[str]:
        """Advance one turn; return list of expired effect description strings."""
        expired: list[str] = []

        if self.weather_turns > 0:
            self.weather_turns -= 1
            if self.weather_turns == 0:
                expired.append(f"날씨 종료: {self.weather}")
                self.weather = Weather.NONE.value

        if self.terrain_turns > 0:
            self.terrain_turns -= 1
            if self.terrain_turns == 0:
                expired.append(f"필드 종료: {self.terrain}")
                self.terrain = Terrain.NONE.value

        for name in list(self.global_effects):
            self.global_effects[name] -= 1
            if self.global_effects[name] <= 0:
                expired.append(f"효과 종료: {name}")
                del self.global_effects[name]

        expired.extend(self.side1.tick_barriers())
        expired.extend(self.side2.tick_barriers())
        return expired
