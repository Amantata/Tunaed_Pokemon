"""Potential template data model.

Pre-defined potential templates that can be selected from a list (PT-02).
Individual-specific potentials can also be authored via script (PT-01, PT-04).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tunaed_pokemon.models.enums import PotentialCategory


@dataclass
class PotentialTemplate:
    """A pre-defined potential template in the master list.

    Templates are used when selecting potentials from a list (PT-02).
    Custom potentials can also be written as scripts (PT-01).

    Attributes:
        id: Unique identifier.
        category: Which potential slot this belongs to.
        name: Potential name (e.g. 『에이스』).
        trigger_text: Condition trigger text specification.
        effect_text: Effect trigger text specification.
        effect_script: Python snippet for sandbox execution.
    """

    id: Optional[int] = None
    category: PotentialCategory = PotentialCategory.GENERAL
    name: str = ""
    trigger_text: str = ""
    effect_text: str = ""
    effect_script: str = ""
