"""Tests for the EventBus and BattleEvent system."""

from tunaed_pokemon.engine.events import (
    BattleEvent,
    BattleEventType,
    EventBus,
)


class TestBattleEvent:
    """Tests for BattleEvent data class."""

    def test_create_event(self):
        event = BattleEvent(
            event_type=BattleEventType.MOVE_USED,
            turn=1,
            source_side=0,
            source_index=0,
            data={"move_name": "화염방사"},
        )
        assert event.event_type == BattleEventType.MOVE_USED
        assert event.turn == 1
        assert event.data["move_name"] == "화염방사"

    def test_serialize_deserialize(self):
        event = BattleEvent(
            event_type=BattleEventType.DAMAGE_DEALT,
            turn=3,
            source_side=0,
            source_index=0,
            target_side=1,
            target_index=0,
            data={"damage": 42, "effectiveness": 2.0},
        )
        d = event.to_dict()
        restored = BattleEvent.from_dict(d)
        assert restored.event_type == event.event_type
        assert restored.turn == event.turn
        assert restored.source_side == event.source_side
        assert restored.target_side == event.target_side
        assert restored.data["damage"] == 42

    def test_default_values(self):
        event = BattleEvent(event_type=BattleEventType.TURN_START)
        assert event.turn == 0
        assert event.source_side is None
        assert event.data == {}


class TestEventBus:
    """Tests for EventBus."""

    def test_subscribe_and_emit(self):
        bus = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))
        event = BattleEvent(event_type=BattleEventType.TURN_START, turn=1)
        bus.emit(event)
        assert len(received) == 1
        assert received[0].turn == 1

    def test_subscribe_specific_type(self):
        bus = EventBus()
        move_events = []
        damage_events = []
        bus.subscribe(
            lambda e: move_events.append(e),
            event_type=BattleEventType.MOVE_USED,
        )
        bus.subscribe(
            lambda e: damage_events.append(e),
            event_type=BattleEventType.DAMAGE_DEALT,
        )

        bus.emit(BattleEvent(event_type=BattleEventType.MOVE_USED))
        bus.emit(BattleEvent(event_type=BattleEventType.DAMAGE_DEALT))
        bus.emit(BattleEvent(event_type=BattleEventType.MOVE_USED))

        assert len(move_events) == 2
        assert len(damage_events) == 1

    def test_event_log(self):
        bus = EventBus()
        bus.emit(BattleEvent(event_type=BattleEventType.TURN_START, turn=1))
        bus.emit(BattleEvent(event_type=BattleEventType.MOVE_USED, turn=1))
        bus.emit(BattleEvent(event_type=BattleEventType.TURN_END, turn=1))
        assert len(bus.event_log) == 3
        assert bus.event_log[0].event_type == BattleEventType.TURN_START

    def test_clear_log(self):
        bus = EventBus()
        bus.emit(BattleEvent(event_type=BattleEventType.TURN_START))
        assert len(bus.event_log) == 1
        bus.clear_log()
        assert len(bus.event_log) == 0

    def test_unsubscribe(self):
        bus = EventBus()
        received = []
        handler = lambda e: received.append(e)
        bus.subscribe(handler)
        bus.emit(BattleEvent(event_type=BattleEventType.TURN_START))
        assert len(received) == 1
        bus.unsubscribe(handler)
        bus.emit(BattleEvent(event_type=BattleEventType.TURN_START))
        assert len(received) == 1  # No new events after unsubscribe

    def test_global_and_specific_handlers(self):
        bus = EventBus()
        global_events = []
        specific_events = []
        bus.subscribe(lambda e: global_events.append(e))
        bus.subscribe(
            lambda e: specific_events.append(e),
            event_type=BattleEventType.MOVE_USED,
        )

        bus.emit(BattleEvent(event_type=BattleEventType.MOVE_USED))
        bus.emit(BattleEvent(event_type=BattleEventType.TURN_END))

        assert len(global_events) == 2  # Gets all events
        assert len(specific_events) == 1  # Only MOVE_USED

    def test_stat_modification_events_separate(self):
        """Verify ST-02: rank change and reinforcement are separate event types."""
        assert BattleEventType.STAT_RANK_CHANGED != BattleEventType.STAT_REINFORCED

        bus = EventBus()
        rank_events = []
        reinforce_events = []
        bus.subscribe(
            lambda e: rank_events.append(e),
            event_type=BattleEventType.STAT_RANK_CHANGED,
        )
        bus.subscribe(
            lambda e: reinforce_events.append(e),
            event_type=BattleEventType.STAT_REINFORCED,
        )

        bus.emit(BattleEvent(
            event_type=BattleEventType.STAT_RANK_CHANGED,
            data={"stat": "공격", "stages": 1},
        ))
        bus.emit(BattleEvent(
            event_type=BattleEventType.STAT_REINFORCED,
            data={"stat": "공격", "multiplier": 2.0},
        ))

        assert len(rank_events) == 1
        assert len(reinforce_events) == 1
