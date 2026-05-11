"""Demo seed data from docs — creates 4 ready-made parties for quick-start.

Target parties:
- docs/트레이너 예제.md : 예제1, 예제2 (2개 파티)
- docs/트레이너 샘플 2.md : 1개 파티
- docs/트레이너 샘플 3.md : 1개 파티

Safe to call multiple times: existing trainer/party/pokémon entries are reused.
"""

from __future__ import annotations

import uuid

from tunaed_pokemon.models.pokemon import IVs, MoveData, Pokemon
from tunaed_pokemon.models.party import Party
from tunaed_pokemon.models.trainer import Trainer
from tunaed_pokemon.utils.persistence import (
    load_all_parties,
    load_all_pokemon,
    load_all_trainers,
    load_moves,
    save_trainer,
    save_moves,
    save_party,
    save_pokemon,
)

# ── Demo move templates ───────────────────────────────────────────────────────

_DEMO_MOVES: list[dict] = [
    {"id": "demo_tackle",  "name": "몸통박기",  "type": "노말", "category": "물리",  "power": 40,  "accuracy": 100, "priority": 0},
    {"id": "demo_pound",   "name": "할퀴기",    "type": "노말", "category": "물리",  "power": 35,  "accuracy": 95,  "priority": 0},
    {"id": "demo_ember",   "name": "불꽃세례",  "type": "불꽃", "category": "특수",  "power": 40,  "accuracy": 100, "priority": 0},
    {"id": "demo_water",   "name": "물대포",    "type": "물",   "category": "특수",  "power": 40,  "accuracy": 100, "priority": 0},
    {"id": "demo_thunder", "name": "번개",       "type": "전기", "category": "특수",  "power": 110, "accuracy": 70,  "priority": 0},
    {"id": "demo_slash",   "name": "베기",       "type": "노말", "category": "물리",  "power": 70,  "accuracy": 100, "priority": 0},
    {"id": "demo_quick",   "name": "전광석화",  "type": "노말", "category": "물리",  "power": 40,  "accuracy": 100, "priority": 1},
    {"id": "demo_surf",    "name": "파도타기",  "type": "물",   "category": "특수",  "power": 90,  "accuracy": 100, "priority": 0},
]

# ── Demo Pokémon templates (name, type1, type2, base_stats, move_set) ────────

_PARTY_SPECS: list[dict] = [
    {
        "key": "trainer_example_1",
        "party_name": "문서 데모 - 트레이너 예제 1 (달크)",
        "trainer_name": "달크",
        "members": [
            {"name": "섬도희 레이", "type1": "노말", "type2": "비행"},
            {"name": "비라 릴리에", "type1": "불꽃", "type2": "드래곤"},
            {"name": "하나즈키", "type1": "물", "type2": None},
            {"name": "윙 건담", "type1": "강철", "type2": "비행"},
            {"name": "모르포", "type1": "전기", "type2": "페어리"},
            {"name": "마스카나", "type1": "풀", "type2": "악"},
            {"name": "유령 기수", "type1": "땅", "type2": "고스트"},
            {"name": "진마 '사냥꾼' 청현", "type1": "땅", "type2": "얼음"},
        ],
    },
    {
        "key": "trainer_example_2",
        "party_name": "문서 데모 - 트레이너 예제 2 (썬콜)",
        "trainer_name": "썬콜",
        "members": [
            {"name": "아크메이지(불,독)", "type1": "불꽃", "type2": "독"},
            {"name": "일리야", "type1": "전기", "type2": "얼음"},
            {"name": "프랑켄슈타인(fate)", "type1": "전기", "type2": "악"},
            {"name": "엘퀴네스", "type1": "얼음", "type2": None},
            {"name": "I:P 마스카레나", "type1": "에스퍼", "type2": "페어리"},
            {"name": "언다인", "type1": "물", "type2": "격투"},
            {"name": "나히다", "type1": "풀", "type2": "땅"},
        ],
    },
    {
        "key": "trainer_sample_2",
        "party_name": "문서 데모 - 트레이너 샘플 2 (쿠로가네 알토)",
        "trainer_name": "쿠로가네 알토",
        "members": [
            {"name": "섬도희 레이", "type1": "노말", "type2": "비행"},
            {"name": "콜로서스", "type1": "강철", "type2": None},
            {"name": "모르포", "type1": "전기", "type2": "페어리"},
            {"name": "이치히메", "type1": "노말", "type2": None},
            {"name": "스즈란", "type1": "불꽃", "type2": "독"},
            {"name": "호세", "type1": "고스트", "type2": "격투"},
        ],
    },
    {
        "key": "trainer_sample_3",
        "party_name": "문서 데모 - 트레이너 샘플 3 (쿠레아)",
        "trainer_name": "쿠레아",
        "members": [
            {"name": "키신 사구메", "type1": "얼음", "type2": "에스퍼"},
            {"name": "엘섀도르 미도라시", "type1": "고스트", "type2": "페어리"},
            {"name": "코코아", "type1": "풀", "type2": "독"},
            {"name": "왕 코쵸", "type1": "노말", "type2": "드래곤"},
            {"name": "스케이스", "type1": "바위", "type2": "에스퍼"},
            {"name": "훼구왕", "type1": "불꽃", "type2": None},
        ],
    },
]


def create_demo_parties() -> list[str]:
    """Create (or reuse) 4 doc-based demo parties and return party IDs in order."""
    existing_parties = load_all_parties()
    existing_trainers = load_all_trainers()
    existing_pokemon = load_all_pokemon()
    party_by_name = {p.name: p for p in existing_parties.values()}
    trainer_by_name = {t.name: t for t in existing_trainers.values()}
    pokemon_by_name = {p.name: p for p in existing_pokemon.values()}

    _ensure_demo_moves()
    available_move_ids = set(load_moves().keys())
    created_party_ids: list[str] = []

    for spec in _PARTY_SPECS:
        trainer_name = spec["trainer_name"]
        trainer = trainer_by_name.get(trainer_name)
        if trainer is None:
            trainer = Trainer(id=str(uuid.uuid4()), name=trainer_name)
            save_trainer(trainer)
            trainer_by_name[trainer_name] = trainer

        member_ids: list[str] = []
        for member in spec["members"]:
            tag = f"[데모:{spec['key']}] {member['name']}"
            existing = pokemon_by_name.get(tag)
            if existing is not None:
                member_ids.append(existing.id)
                continue

            p = Pokemon(
                id=str(uuid.uuid4()),
                name=tag,
                type1=member["type1"],
                type2=member.get("type2"),
                level=50,
                base_stats=_default_stats_for_types(member["type1"], member.get("type2")),
                ivs=IVs(hp=15, attack=15, defense=15, sp_atk=15, sp_def=15, speed=15),
                move_ids=_default_moves_for_types(
                    member["type1"], member.get("type2"), available_move_ids
                ),
            )
            save_pokemon(p)
            pokemon_by_name[tag] = p
            member_ids.append(p.id)

        party_name = spec["party_name"]
        party = party_by_name.get(party_name)
        if party is None:
            party = Party(
                id=str(uuid.uuid4()),
                name=party_name,
                trainer_id=trainer.id,
                pokemon_ids=member_ids,
                max_size=max(6, len(member_ids)),
            )
        else:
            party.trainer_id = trainer.id
            party.pokemon_ids = member_ids
            party.max_size = max(6, len(member_ids))
        save_party(party)
        party_by_name[party_name] = party
        created_party_ids.append(party.id)

    return created_party_ids


def _ensure_demo_moves() -> None:
    """Add demo moves to the master list if not already present."""
    moves = load_moves()
    changed = False
    for tmpl in _DEMO_MOVES:
        if tmpl["id"] not in moves:
            moves[tmpl["id"]] = MoveData(
                id=tmpl["id"],
                name=tmpl["name"],
                type=tmpl["type"],
                category=tmpl["category"],
                power=tmpl.get("power"),
                accuracy=tmpl.get("accuracy"),
                priority=tmpl.get("priority", 0),
            )
            changed = True
    if changed:
        save_moves(moves)


def _default_moves_for_types(
    type1: str,
    type2: str | None,
    available_move_ids: set[str],
) -> list[str]:
    """Return a 4-move demo set with simple type bias."""
    moves = ["demo_tackle", "demo_quick", "demo_slash", "demo_pound"]
    preferred = {
        "불꽃": "demo_ember",
        "물": "demo_surf",
        "전기": "demo_thunder",
    }
    for t in (type1, type2):
        if t in preferred:
            moves[0] = preferred[t]
            break
    validated = [m for m in moves if m in available_move_ids]
    if validated:
        return validated
    # Defensive fallback if move DB is unexpectedly missing demo moves
    # Prefer a guaranteed-safe basic move, otherwise fallback to any available move.
    if "demo_tackle" in available_move_ids:
        return ["demo_tackle"]
    if available_move_ids:
        return [sorted(available_move_ids)[0]]
    raise RuntimeError(
        "데모 기술 목록이 비어 있어 데모 파티를 생성할 수 없습니다. "
        "초기화 이후에도 move 데이터베이스가 비어 있습니다. 앱을 재시작하고 데이터 파일을 확인하세요."
    )


def _default_stats_for_types(type1: str, type2: str | None) -> dict[str, int]:
    """Return deterministic baseline stats for demo members.

    Type category bonuses are cumulative for dual types.
    Example: "전기/격투" gets both special(+sp_atk/+speed) and physical(+attack) bonuses.
    """
    hp = 80
    attack = 85
    defense = 85
    sp_atk = 85
    sp_def = 85
    speed = 85

    offensive_special = {"전기", "불꽃", "얼음", "에스퍼"}
    offensive_physical = {"격투", "땅", "강철", "고스트", "드래곤", "악"}
    defensive = {"바위", "독"}

    types = {type1}
    if type2:
        types.add(type2)

    if types & offensive_special:
        sp_atk += 15
        speed += 5
    if types & offensive_physical:
        attack += 15
    if types & defensive:
        defense += 10
        sp_def += 10

    return {
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "sp_atk": sp_atk,
        "sp_def": sp_def,
        "speed": speed,
    }
