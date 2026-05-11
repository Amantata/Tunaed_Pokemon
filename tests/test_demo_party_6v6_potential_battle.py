"""데모파티 6v6 배틀 엔진/포텐셜 통합 테스트."""

from __future__ import annotations

import re

from tunaed_pokemon.engine.action_order import ActionEntry
from tunaed_pokemon.engine.battle_state import (
    BattlePokemonState,
    BattleSideState,
    BattleStateSnapshot,
)
from tunaed_pokemon.engine.turn_pipeline import TurnPipeline
from tunaed_pokemon.models.party import Party
from tunaed_pokemon.models.pokemon import MoveData, Pokemon
from tunaed_pokemon.models.trainer import Trainer
from tunaed_pokemon.utils.persistence import (
    load_all_parties,
    load_all_pokemon,
    load_all_trainers,
    load_moves,
)
from tunaed_pokemon.utils.seed_data import create_demo_parties
from tunaed_pokemon.utils.stat_calc import calc_hp, calc_stat

_SLOT_PATTERN = re.compile(r"포텐셜 발동! \[([^\]]+)\]")
_TEST_MIN_HP = 999
_TEMPLATE_SLOT_KINDS = {
    "역할", "분류", "주인", "이명",
    "계제①", "계제②", "계제③", "계제④",
    "속별", "유대", "선제", "회피", "내성", "격",
    "범용", "부수", "특권", "PT①", "PT②", "전용포텐셜",
}


def _build_side_state(party: Party, trainers: dict[str, Trainer], pokemon_db: dict[str, Pokemon]) -> BattleSideState:
    trainer = trainers.get(party.trainer_id or "")
    pokemon_states: list[BattlePokemonState] = []

    for pid in party.pokemon_ids[:6]:
        p = pokemon_db[pid]
        bs = p.base_stats
        iv = p.ivs
        ev = p.evs
        max_hp = calc_hp(bs.get("hp", 50), iv.hp, ev.hp, p.level)
        battle_stats = {
            "hp": max_hp,
            "attack": calc_stat(bs.get("attack", 50), iv.attack, ev.attack, p.level),
            "defense": calc_stat(bs.get("defense", 50), iv.defense, ev.defense, p.level),
            "sp_atk": calc_stat(bs.get("sp_atk", 50), iv.sp_atk, ev.sp_atk, p.level),
            "sp_def": calc_stat(bs.get("sp_def", 50), iv.sp_def, ev.sp_def, p.level),
            "speed": calc_stat(bs.get("speed", 50), iv.speed, ev.speed, p.level),
        }
        pokemon_states.append(
            BattlePokemonState(
                pokemon_id=p.id,
                name=p.name,
                current_hp=max_hp,
                max_hp=max_hp,
                level=p.level,
                type1=p.type1,
                type2=p.type2,
                ability_name=p.ability_name,
                move_ids=list(p.move_ids),
                potentials=list(p.potentials),
                exclusive_potential=p.exclusive_potential,
                battle_stats=battle_stats,
            )
        )

    return BattleSideState(
        trainer_id=party.trainer_id,
        trainer_name=(trainer.name if trainer else party.name),
        party_id=party.id,
        pokemon_states=pokemon_states,
        active_indices=[0],
    )


def _find_move(ps: BattlePokemonState, moves: dict[str, MoveData]) -> MoveData:
    for mid in ps.move_ids:
        move = moves.get(mid)
        if move is not None:
            return move
    raise AssertionError(f"{ps.name}의 사용 가능한 기술이 없습니다.")


def _collect_activation_slots(lines: list[str], fired_slots: set[str], activation_lines: list[str]) -> bool:
    """Collect per-potential activation lines and fired slot kinds from turn logs."""
    found = False
    for line in lines:
        if not line.startswith("포텐셜 발동! [") or "『" not in line:
            continue
        m = _SLOT_PATTERN.search(line)
        if not m:
            continue
        found = True
        fired_slots.add(m.group(1))
        activation_lines.append(line)
    return found


def test_demo_party_6v6_engine_and_potential_activation_requirements():
    demo_party_ids = create_demo_parties()
    assert len(demo_party_ids) >= 2

    parties = load_all_parties()
    trainers = load_all_trainers()
    pokemon_db = load_all_pokemon()
    moves = load_moves()

    side1 = _build_side_state(parties[demo_party_ids[0]], trainers, pokemon_db)
    side2 = _build_side_state(parties[demo_party_ids[1]], trainers, pokemon_db)
    assert len(side1.pokemon_states) == 6
    assert len(side2.pokemon_states) == 6

    state = BattleStateSnapshot(side1=side1, side2=side2, battle_format="싱글")
    pipe = TurnPipeline()

    # 테스트 중 불필요한 조기 기절을 줄여 포텐셜 발동 검증을 안정화한다.
    for ps in state.side1.pokemon_states + state.side2.pokemon_states:
        ps.max_hp = max(ps.max_hp, _TEST_MIN_HP)
        ps.current_hp = ps.max_hp
        ps.battle_stats["hp"] = ps.max_hp

    triggered_attackers: dict[int, set[str]] = {1: set(), 2: set()}
    activation_lines: list[str] = []
    fired_slots: set[str] = set()

    for idx in range(3):
        if idx > 0:
            state = pipe.process_turn(
                state,
                [
                    ActionEntry(side=1, pokemon=state.side1.active_pokemon[0], action_type="switch", switch_target=idx),
                    ActionEntry(side=2, pokemon=state.side2.active_pokemon[0], action_type="switch", switch_target=idx),
                ],
                moves,
            )

        # side 1 attacker
        s1_attacker = state.side1.active_pokemon[0]
        s1_move = _find_move(s1_attacker, moves)
        before = len(state.log)
        state = pipe.process_turn(
            state,
            [ActionEntry(side=1, pokemon=s1_attacker, action_type="move", move=s1_move)],
            moves,
        )
        lines = state.log[before:]
        if _collect_activation_slots(lines, fired_slots, activation_lines):
            triggered_attackers[1].add(s1_attacker.name)

        # side 2 attacker
        s2_attacker = state.side2.active_pokemon[0]
        s2_move = _find_move(s2_attacker, moves)
        before = len(state.log)
        state = pipe.process_turn(
            state,
            [ActionEntry(side=2, pokemon=s2_attacker, action_type="move", move=s2_move)],
            moves,
        )
        lines = state.log[before:]
        if _collect_activation_slots(lines, fired_slots, activation_lines):
            triggered_attackers[2].add(s2_attacker.name)

    # 요구사항 1) 각 파티당 최소 3마리 포텐셜 발동
    assert len(triggered_attackers[1]) >= 3
    assert len(triggered_attackers[2]) >= 3

    # 요구사항 2) 포텐셜 발동 로그 15회 이상
    assert len(activation_lines) >= 15

    # 요구사항 3) 서로 다른 종류(슬롯) 10개 이상 발동
    assert len(fired_slots) >= 10

    # 요구사항 4) 템플릿 목록의 서로 다른 종류 기준으로도 검증
    assert fired_slots.issubset(_TEMPLATE_SLOT_KINDS)
    assert len(fired_slots & _TEMPLATE_SLOT_KINDS) >= 10
