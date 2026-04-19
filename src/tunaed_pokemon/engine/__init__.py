"""Battle engine and effect processing.

Submodules:
- events: BattleEvent, EventBus — event system for GUI/Undo/animation (B-02, B-03).
- field_state: FieldStateManager — weather, terrain, barriers, special fields (FE-01~FE-06).
- status: StatusEngine — status conditions and changes.
- battle_state: BattleStateSnapshot, TurnHistory — save/load and Undo/Redo (B-01, B-02).
"""
