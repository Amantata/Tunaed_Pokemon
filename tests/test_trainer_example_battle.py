"""배틀 로그 재생 테스트 — 트레이너 예제 데이터 기반 (Q8).

docs/트레이너 예제.md의 달크 트레이너 파티 (섬도희 레이 등)를 사용하여
실제 배틀 시뮬레이션을 실행하고 엔진 동작을 검증합니다.

테스트 범위:
  - 예제 파티 구성 (파티원 능력치, 기술 등)
  - BattleEventHistory 이벤트 기록 (B-02)
  - TurnHistory 턴 시작 스냅샷 (B-01)
  - 복수 턴 배틀 로그 재생 / 결과 검증
  - pp_remaining 필드 초기화 및 무제한 정책(미차감)
  - BattleStateSnapshot 직렬화/역직렬화 라운드트립
"""

from __future__ import annotations

import pytest

from tunaed_pokemon.engine.action_order import ActionEntry
from tunaed_pokemon.engine.battle_state import (
    BattleEventHistory,
    BattlePokemonState,
    BattleSideState,
    BattleStateSnapshot,
    TurnHistory,
)
from tunaed_pokemon.engine.events import BattleEventType
from tunaed_pokemon.engine.turn_pipeline import TurnPipeline
from tunaed_pokemon.models.pokemon import MoveData


# ── 예제 파티 구성 헬퍼 ───────────────────────────────────────────────────────

def _make_ray() -> BattlePokemonState:
    """섬도희 레이 — AA급 에이스 (docs/트레이너 예제.md).

    타입: 노말/비행
    주요 능력치: HP A+(135), 공격 A+(135), 방어 B-(90), 특공 C(70), 특방 B-(90), 속도 B+(105)
    기술 6개 (물리 위주)
    """
    moves = ["hitblade", "stoneedge", "magicsword", "doublewing", "sworddance", "wingguard"]
    pp_list = [10, 5, 10, 20, 20, 10]
    return BattlePokemonState(
        pokemon_id="ray_01",
        name="섬도희 레이",
        current_hp=270,
        max_hp=270,
        level=50,
        type1="노말",
        type2="비행",
        ability_name="오기",
        move_ids=moves,
        pp_remaining=pp_list,
        battle_stats={
            "hp": 270, "attack": 135, "defense": 90,
            "sp_atk": 70, "sp_def": 90, "speed": 105,
        },
    )


def _make_opponent() -> BattlePokemonState:
    """대전 상대 — 전기 타입 (레이의 약점 검증용)."""
    return BattlePokemonState(
        pokemon_id="opp_01",
        name="상대 포켓몬",
        current_hp=200,
        max_hp=200,
        level=50,
        type1="전기",
        type2=None,
        ability_name="",
        move_ids=["thunder"],
        pp_remaining=[15],
        battle_stats={
            "hp": 200, "attack": 100, "defense": 80,
            "sp_atk": 120, "sp_def": 80, "speed": 90,
        },
    )


def _make_move_data() -> dict[str, MoveData]:
    """기술 데이터 사전."""
    return {
        "hitblade": MoveData(
            id="hitblade", name="히트블레이드", type="불꽃",
            category="물리", power=90, accuracy=100, pp=10, priority=0,
        ),
        "stoneedge": MoveData(
            id="stoneedge", name="스톤에지", type="바위",
            category="물리", power=100, accuracy=80, pp=5, priority=0,
        ),
        "magicsword": MoveData(
            id="magicsword", name="마법의검", type="페어리",
            category="물리", power=90, accuracy=100, pp=10, priority=0,
        ),
        "doublewing": MoveData(
            id="doublewing", name="더블윙", type="비행",
            category="물리", power=40, accuracy=90, pp=20, priority=0,
        ),
        "sworddance": MoveData(
            id="sworddance", name="칼춤", type="노말",
            category="변화", power=None, accuracy=None, pp=20, priority=0,
        ),
        "wingguard": MoveData(
            id="wingguard", name="날개로방어", type="비행",
            category="변화", power=None, accuracy=None, pp=10, priority=3,
        ),
        "thunder": MoveData(
            id="thunder", name="번개", type="전기",
            category="특수", power=110, accuracy=70, pp=10, priority=0,
        ),
    }


def _make_battle() -> tuple[BattleStateSnapshot, dict[str, MoveData]]:
    """1v1 배틀 초기 상태를 생성합니다."""
    ray = _make_ray()
    opp = _make_opponent()
    side1 = BattleSideState(
        trainer_id="dalc", trainer_name="달크",
        party_id="dalc_party",
        pokemon_states=[ray], active_indices=[0],
    )
    side2 = BattleSideState(
        trainer_id="opp", trainer_name="상대 트레이너",
        party_id="opp_party",
        pokemon_states=[opp], active_indices=[0],
    )
    state = BattleStateSnapshot(side1=side1, side2=side2, battle_format="싱글")
    moves = _make_move_data()
    return state, moves


# ── 기본 배틀 구성 테스트 ─────────────────────────────────────────────────────

class TestExamplePartySetup:
    def test_ray_has_correct_hp(self):
        ray = _make_ray()
        assert ray.max_hp == 270
        assert ray.current_hp == 270

    def test_ray_has_6_moves(self):
        ray = _make_ray()
        assert len(ray.move_ids) == 6

    def test_ray_pp_initialized(self):
        ray = _make_ray()
        assert len(ray.pp_remaining) == 6
        assert ray.pp_remaining[0] == 10   # 히트블레이드

    def test_ray_dual_type(self):
        ray = _make_ray()
        assert ray.type1 == "노말"
        assert ray.type2 == "비행"

    def test_battle_state_created(self):
        state, _ = _make_battle()
        assert state.battle_format == "싱글"
        assert state.side1.trainer_name == "달크"
        assert len(state.side1.pokemon_states) == 1
        assert state.side1.pokemon_states[0].name == "섬도희 레이"


# ── B-02: BattleEventHistory 이벤트 기록 테스트 ──────────────────────────────

class TestBattleEventHistory:
    def test_event_recorded_after_move(self):
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        pipe.process_turn(state, [action], moves)

        assert history.can_undo()
        assert len(history.event_log()) > 0

    def test_undo_restores_state_before_move(self):
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        opp_hp_before = state.side2.pokemon_states[0].current_hp
        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        new_state = pipe.process_turn(state, [action], moves)

        # 데미지가 들어갔는지 확인
        assert new_state.side2.pokemon_states[0].current_hp < opp_hp_before

        # Undo — 이동 사용 전 상태로 복원
        restored = history.undo()
        assert restored is not None
        # 복원된 상태는 데미지 전 HP를 갖는다
        assert restored.side2.pokemon_states[0].current_hp == opp_hp_before

    def test_can_redo_after_undo(self):
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        pipe.process_turn(state, [action], moves)

        history.undo()
        assert history.can_redo()

    def test_redo_returns_state(self):
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        pipe.process_turn(state, [action], moves)

        history.undo()
        snap = history.redo()
        assert snap is not None

    def test_event_log_contains_move_event(self):
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        pipe.process_turn(state, [action], moves)

        event_types = [e.event_type for e in history.event_log()]
        assert BattleEventType.MOVE_USED in event_types

    def test_event_log_contains_damage_event(self):
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        pipe.process_turn(state, [action], moves)

        event_types = [e.event_type for e in history.event_log()]
        assert BattleEventType.DAMAGE_DEALT in event_types

    def test_new_action_clears_redo_stack(self):
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        new_state = pipe.process_turn(state, [action], moves)

        history.undo()
        assert history.can_redo()

        # 새 행동으로 redo 스택 초기화
        ray2 = new_state.side1.pokemon_states[0]
        history.record(new_state, history.event_log()[0])
        assert not history.can_redo()

    def test_serialization_round_trip(self):
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        pipe.process_turn(state, [action], moves)

        d = history.to_dict()
        restored = BattleEventHistory.from_dict(d)
        assert len(restored.event_log()) == len(history.event_log())


# ── B-01: TurnHistory 턴 시작 스냅샷 테스트 ─────────────────────────────────

class TestTurnStartSnapshot:
    def test_snapshot_before_turn_preserves_pre_action_hp(self):
        """B-01: 턴 시작 시점 스냅샷은 행동 처리 전 HP를 보존해야 한다."""
        state, moves = _make_battle()
        turn_history = TurnHistory()

        # 턴 시작 스냅샷 (B-01 — 행동 처리 전)
        turn_history.push(state)

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        pipe = TurnPipeline()
        new_state = pipe.process_turn(state, [action], moves)

        # 저장된 스냅샷은 행동 전 HP
        saved = turn_history.current
        assert saved is not None
        opp_hp_before = saved.side2.pokemon_states[0].current_hp
        opp_hp_after  = new_state.side2.pokemon_states[0].current_hp
        assert opp_hp_before == 200            # 저장 시점은 행동 전
        assert opp_hp_after < opp_hp_before    # 행동 후는 데미지 있음

    def test_multiple_turns_preserve_turn_start_states(self):
        """여러 턴에 걸쳐 턴 시작 스냅샷이 독립적으로 저장된다."""
        state, moves = _make_battle()
        turn_history = TurnHistory()
        pipe = TurnPipeline()

        current = state
        snapshots_before = []
        for _ in range(3):
            turn_history.push(current)
            snapshots_before.append(current.side2.pokemon_states[0].current_hp)
            ray = current.side1.pokemon_states[0]
            if not ray.is_fainted:
                action = ActionEntry(side=1, pokemon=ray, action_type="move",
                                     move=moves["doublewing"])
                current = pipe.process_turn(current, [action], moves)
            else:
                break

        # 각 스냅샷의 HP는 비단조 감소 (또는 같거나 감소)
        for i in range(1, len(snapshots_before)):
            assert snapshots_before[i] <= snapshots_before[i - 1]


# ── PP 무제한 정책 테스트 ─────────────────────────────────────────────────────

class TestPPUnlimited:
    def test_pp_does_not_decrease_when_move_used(self):
        state, moves = _make_battle()
        pipe = TurnPipeline()

        ray_before_pp = state.side1.pokemon_states[0].pp_remaining[0]
        assert ray_before_pp == 10  # 히트블레이드 초기 PP

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        new_state = pipe.process_turn(state, [action], moves)

        ray_after = new_state.side1.pokemon_states[0]
        assert ray_after.pp_remaining[0] == 10   # 무제한 정책으로 미차감

    def test_pp_round_trip(self):
        state, _ = _make_battle()
        d = state.to_dict()
        restored = BattleStateSnapshot.from_dict(d)
        ray_orig = state.side1.pokemon_states[0]
        ray_rest = restored.side1.pokemon_states[0]
        assert ray_rest.pp_remaining == ray_orig.pp_remaining


# ── 다턴 배틀 로그 재생 테스트 ───────────────────────────────────────────────

class TestMultiTurnBattleReplay:
    def test_battle_log_grows_per_turn(self):
        """각 턴마다 로그가 누적된다."""
        state, moves = _make_battle()
        pipe = TurnPipeline()

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        state2 = pipe.process_turn(state, [action], moves)

        # 로그가 더 길어야 함
        assert len(state2.log) > len(state.log)

    def test_battle_ends_when_opponent_faints(self):
        """상대가 쓰러지면 배틀이 종료된다."""
        state, moves = _make_battle()
        # 상대 HP를 1로 설정
        state.side2.pokemon_states[0].current_hp = 1
        state.side2.pokemon_states[0].max_hp = 200

        pipe = TurnPipeline()
        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        new_state = pipe.process_turn(state, [action], moves)

        assert new_state.battle_over is True
        assert new_state.winner_side == 1

    def test_snapshot_serialization_after_battle(self):
        """배틀 종료 후 스냅샷 직렬화/역직렬화 라운드트립."""
        state, moves = _make_battle()
        state.side2.pokemon_states[0].current_hp = 1

        pipe = TurnPipeline()
        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        final_state = pipe.process_turn(state, [action], moves)

        d = final_state.to_dict()
        restored = BattleStateSnapshot.from_dict(d)

        assert restored.battle_over is True
        assert restored.winner_side == 1
        assert restored.side1.trainer_name == "달크"

    def test_five_turn_simulation_no_error(self):
        """5턴 시뮬레이션이 에러 없이 완료된다."""
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        current = state
        for _ in range(5):
            if current.battle_over:
                break
            ray = current.side1.pokemon_states[0]
            if ray.is_fainted:
                break
            action = ActionEntry(side=1, pokemon=ray, action_type="move",
                                 move=moves["hitblade"])
            current = pipe.process_turn(current, [action], moves)

        # 최소 1개 이상의 이벤트가 기록됐는지
        assert len(history.event_log()) > 0
        # 턴이 1 이상 진행됐는지
        assert current.turn_number >= 1

    def test_event_history_undo_all(self):
        """여러 이벤트를 모두 undo할 수 있다."""
        state, moves = _make_battle()
        history = BattleEventHistory()
        pipe = TurnPipeline(event_history=history)

        ray = state.side1.pokemon_states[0]
        action = ActionEntry(side=1, pokemon=ray, action_type="move",
                             move=moves["hitblade"])
        pipe.process_turn(state, [action], moves)

        count = len(history.event_log())
        assert count > 0

        undone = 0
        while history.can_undo():
            snap = history.undo()
            assert snap is not None
            undone += 1

        assert undone == count
