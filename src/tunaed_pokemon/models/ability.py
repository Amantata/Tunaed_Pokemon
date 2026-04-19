"""Ability (특성) data model.

Abilities are selected from a master list that is editable via in-app editor (SK-03).
Abilities can change mid-battle via moves, potentials, or other abilities (SK-04).
Abilities and potentials are independent (PT-06).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Ability:
    """A single ability (특성) in the master list.

    Attributes:
        id: Unique identifier.
        name: Ability name.
        effect_description: Human-readable effect text.
        effect_script: Python snippet for sandbox execution.
    """

    id: Optional[int] = None
    name: str = ""
    effect_description: str = ""
    effect_script: str = ""
