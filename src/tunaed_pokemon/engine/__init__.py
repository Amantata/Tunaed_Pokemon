"""Engine modules: EventBus, FieldStateManager, StatusEngine, BattleStateSnapshot,
TypeChart, DamageCalculator, ActionOrderResolver, TurnPipeline."""

from .events import EventBus, BattleEvent, BattleEventType
from .field_state import FieldStateManager, SideFieldState
from .status import StatusEngine, StatusState
from .battle_state import (
    RankStages,
    Reinforcements,
    BattlePokemonState,
    BattleSideState,
    BattleStateSnapshot,
    TurnHistory,
)
from .type_chart import get_effectiveness, get_combined_effectiveness
from .damage_calc import DamageCalculator, DamageContext, DamageResult
from .action_order import ActionEntry, ActionOrderResolver
from .turn_pipeline import TurnPipeline

__all__ = [
    # events
    "EventBus", "BattleEvent", "BattleEventType",
    # field state
    "FieldStateManager", "SideFieldState",
    # status
    "StatusEngine", "StatusState",
    # battle state
    "RankStages", "Reinforcements",
    "BattlePokemonState", "BattleSideState",
    "BattleStateSnapshot", "TurnHistory",
    # type chart
    "get_effectiveness", "get_combined_effectiveness",
    # damage
    "DamageCalculator", "DamageContext", "DamageResult",
    # action order
    "ActionEntry", "ActionOrderResolver",
    # turn pipeline
    "TurnPipeline",
]
