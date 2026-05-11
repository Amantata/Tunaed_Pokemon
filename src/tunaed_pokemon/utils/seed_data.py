"""Demo seed data — creates two ready-made 6v6 parties for quick-start battles.

Call ``create_demo_parties()`` once to populate the data directory with two
named parties (레드 팀 / 블루 팀) each containing 6 Pokémon and a shared set of
demo moves.  Safe to call multiple times: existing entries are preserved.
"""

from __future__ import annotations

import uuid

from tunaed_pokemon.models.pokemon import IVs, MoveData, Pokemon
from tunaed_pokemon.models.party import Party
from tunaed_pokemon.utils.persistence import (
    load_all_parties,
    load_all_pokemon,
    load_moves,
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

_DEMO_POKEMON_TEMPLATES: list[dict] = [
    # Red team
    {
        "name": "파이리",   "type1": "불꽃", "type2": None,
        "stats": {"hp": 39, "attack": 52, "defense": 43, "sp_atk": 60, "sp_def": 50, "speed": 65},
        "moves": ["demo_ember", "demo_slash", "demo_tackle", "demo_quick"],
        "team": "red",
    },
    {
        "name": "꼬부기",   "type1": "물",   "type2": None,
        "stats": {"hp": 44, "attack": 48, "defense": 65, "sp_atk": 50, "sp_def": 64, "speed": 43},
        "moves": ["demo_water", "demo_tackle", "demo_pound", "demo_surf"],
        "team": "red",
    },
    {
        "name": "이상해씨", "type1": "풀",   "type2": "독",
        "stats": {"hp": 45, "attack": 49, "defense": 49, "sp_atk": 65, "sp_def": 65, "speed": 45},
        "moves": ["demo_tackle", "demo_pound", "demo_slash", "demo_quick"],
        "team": "red",
    },
    {
        "name": "피카츄",   "type1": "전기", "type2": None,
        "stats": {"hp": 35, "attack": 55, "defense": 40, "sp_atk": 50, "sp_def": 50, "speed": 90},
        "moves": ["demo_thunder", "demo_quick", "demo_tackle", "demo_pound"],
        "team": "red",
    },
    {
        "name": "잠만보",   "type1": "노말", "type2": None,
        "stats": {"hp": 95, "attack": 80, "defense": 110, "sp_atk": 70, "sp_def": 95, "speed": 30},
        "moves": ["demo_tackle", "demo_slash", "demo_pound", "demo_surf"],
        "team": "red",
    },
    {
        "name": "갸라도스",  "type1": "물",  "type2": "비행",
        "stats": {"hp": 95, "attack": 125, "defense": 79, "sp_atk": 60, "sp_def": 100, "speed": 81},
        "moves": ["demo_surf", "demo_slash", "demo_tackle", "demo_pound"],
        "team": "red",
    },
    # Blue team
    {
        "name": "리자몽",   "type1": "불꽃", "type2": "비행",
        "stats": {"hp": 78, "attack": 84, "defense": 78, "sp_atk": 109, "sp_def": 85, "speed": 100},
        "moves": ["demo_ember", "demo_slash", "demo_quick", "demo_tackle"],
        "team": "blue",
    },
    {
        "name": "거북왕",   "type1": "물",   "type2": None,
        "stats": {"hp": 79, "attack": 83, "defense": 100, "sp_atk": 85, "sp_def": 105, "speed": 78},
        "moves": ["demo_surf", "demo_water", "demo_slash", "demo_tackle"],
        "team": "blue",
    },
    {
        "name": "이상해꽃", "type1": "풀",   "type2": "독",
        "stats": {"hp": 80, "attack": 82, "defense": 83, "sp_atk": 100, "sp_def": 100, "speed": 80},
        "moves": ["demo_slash", "demo_tackle", "demo_pound", "demo_quick"],
        "team": "blue",
    },
    {
        "name": "쥬피썬더", "type1": "전기", "type2": None,
        "stats": {"hp": 65, "attack": 65, "defense": 60, "sp_atk": 110, "sp_def": 95, "speed": 130},
        "moves": ["demo_thunder", "demo_quick", "demo_pound", "demo_tackle"],
        "team": "blue",
    },
    {
        "name": "내루미",   "type1": "노말", "type2": None,
        "stats": {"hp": 115, "attack": 45, "defense": 20, "sp_atk": 45, "sp_def": 25, "speed": 20},
        "moves": ["demo_tackle", "demo_slash", "demo_pound", "demo_surf"],
        "team": "blue",
    },
    {
        "name": "드래곤",   "type1": "드래곤", "type2": None,
        "stats": {"hp": 91, "attack": 134, "defense": 95, "sp_atk": 100, "sp_def": 100, "speed": 80},
        "moves": ["demo_slash", "demo_tackle", "demo_quick", "demo_pound"],
        "team": "blue",
    },
]


def create_demo_parties() -> tuple[str, str]:
    """Create (or reuse) two 6-member demo parties.

    Returns ``(red_party_id, blue_party_id)``.  If demo parties already exist
    (detected by name) they are returned without modification.
    """
    existing_parties = load_all_parties()
    red_party: Party | None = None
    blue_party: Party | None = None
    for p in existing_parties.values():
        if p.name == "레드 팀":
            red_party = p
        elif p.name == "블루 팀":
            blue_party = p
        if red_party and blue_party:
            break
    if red_party and blue_party:
        return red_party.id, blue_party.id

    # Ensure demo moves exist
    _ensure_demo_moves()

    # Build a name→Pokemon lookup to avoid repeated full-dict scans
    existing_pokemon = load_all_pokemon()
    pokemon_by_name = {p.name: p for p in existing_pokemon.values()}

    red_ids: list[str] = []
    blue_ids: list[str] = []

    for tmpl in _DEMO_POKEMON_TEMPLATES:
        tag = f"[데모:{tmpl['team']}] {tmpl['name']}"
        existing = pokemon_by_name.get(tag)
        if existing:
            pid = existing.id
        else:
            p = Pokemon(
                id=str(uuid.uuid4()),
                name=tag,
                type1=tmpl["type1"],
                type2=tmpl.get("type2"),
                level=50,
                base_stats=tmpl["stats"],
                ivs=IVs(hp=15, attack=15, defense=15, sp_atk=15, sp_def=15, speed=15),
                move_ids=list(tmpl["moves"]),
            )
            save_pokemon(p)
            pid = p.id

        if tmpl["team"] == "red":
            red_ids.append(pid)
        else:
            blue_ids.append(pid)

    red = red_party or Party(id=str(uuid.uuid4()), name="레드 팀",
                             pokemon_ids=red_ids, max_size=6)
    blue = blue_party or Party(id=str(uuid.uuid4()), name="블루 팀",
                               pokemon_ids=blue_ids, max_size=6)

    if not red_party:
        red.pokemon_ids = red_ids
        save_party(red)
    if not blue_party:
        blue.pokemon_ids = blue_ids
        save_party(blue)

    return red.id, blue.id


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
