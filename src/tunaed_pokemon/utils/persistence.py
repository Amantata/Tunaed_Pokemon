"""JSON-based persistence layer for all application data."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ..models.pokemon import Pokemon, MoveData, AbilityData, PotentialData
from ..models.trainer import Trainer
from ..models.party import Party


def get_data_dir() -> Path:
    """Return the user-level data directory for TunaedPokemon."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    data_dir = base / "TunaedPokemon"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _subdir(name: str) -> Path:
    d = get_data_dir() / name
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Pokémon ──────────────────────────────────────────────────────────────────

def load_all_pokemon() -> dict[str, Pokemon]:
    result: dict[str, Pokemon] = {}
    for f in _subdir("pokemon").glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            p = Pokemon.from_dict(data)
            result[p.id] = p
        except Exception:
            pass
    return result


def save_pokemon(p: Pokemon) -> None:
    f = _subdir("pokemon") / f"{p.id}.json"
    f.write_text(json.dumps(p.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def delete_pokemon(pokemon_id: str) -> None:
    (_subdir("pokemon") / f"{pokemon_id}.json").unlink(missing_ok=True)


# ── Trainers ─────────────────────────────────────────────────────────────────

def load_all_trainers() -> dict[str, Trainer]:
    result: dict[str, Trainer] = {}
    for f in _subdir("trainers").glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            t = Trainer.from_dict(data)
            result[t.id] = t
        except Exception:
            pass
    return result


def save_trainer(t: Trainer) -> None:
    f = _subdir("trainers") / f"{t.id}.json"
    f.write_text(json.dumps(t.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def delete_trainer(trainer_id: str) -> None:
    (_subdir("trainers") / f"{trainer_id}.json").unlink(missing_ok=True)


# ── Parties ──────────────────────────────────────────────────────────────────

def load_all_parties() -> dict[str, Party]:
    result: dict[str, Party] = {}
    for f in _subdir("parties").glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            p = Party.from_dict(data)
            result[p.id] = p
        except Exception:
            pass
    return result


def save_party(p: Party) -> None:
    f = _subdir("parties") / f"{p.id}.json"
    f.write_text(json.dumps(p.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def delete_party(party_id: str) -> None:
    (_subdir("parties") / f"{party_id}.json").unlink(missing_ok=True)


# ── Master Lists ─────────────────────────────────────────────────────────────

def load_moves() -> dict[str, MoveData]:
    f = get_data_dir() / "moves.json"
    if not f.exists():
        return {}
    try:
        return {m["id"]: MoveData.from_dict(m) for m in json.loads(f.read_text(encoding="utf-8"))}
    except Exception:
        return {}


def save_moves(moves: dict[str, MoveData]) -> None:
    f = get_data_dir() / "moves.json"
    f.write_text(json.dumps([m.to_dict() for m in moves.values()], ensure_ascii=False, indent=2), encoding="utf-8")


def load_abilities() -> dict[str, AbilityData]:
    f = get_data_dir() / "abilities.json"
    if not f.exists():
        return {}
    try:
        return {a["id"]: AbilityData.from_dict(a) for a in json.loads(f.read_text(encoding="utf-8"))}
    except Exception:
        return {}


def save_abilities(abilities: dict[str, AbilityData]) -> None:
    f = get_data_dir() / "abilities.json"
    f.write_text(json.dumps([a.to_dict() for a in abilities.values()], ensure_ascii=False, indent=2), encoding="utf-8")


def load_potentials() -> dict[str, PotentialData]:
    f = get_data_dir() / "potentials.json"
    if not f.exists():
        return {}
    try:
        return {p["id"]: PotentialData.from_dict(p) for p in json.loads(f.read_text(encoding="utf-8"))}
    except Exception:
        return {}


def save_potentials(potentials: dict[str, PotentialData]) -> None:
    f = get_data_dir() / "potentials.json"
    f.write_text(json.dumps([p.to_dict() for p in potentials.values()], ensure_ascii=False, indent=2), encoding="utf-8")


# ── Battle State ─────────────────────────────────────────────────────────────

def save_battle_state(state_dict: dict[str, Any], filename: str = "battle_save.json") -> None:
    f = _subdir("battles") / filename
    f.write_text(json.dumps(state_dict, ensure_ascii=False, indent=2), encoding="utf-8")


def load_battle_state(filename: str = "battle_save.json") -> dict[str, Any] | None:
    f = _subdir("battles") / filename
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


# ── Import / Export (EX-01, EX-02) ──────────────────────────────────────────

def export_parties_to_files(parties: list[Party], out_dir: str) -> list[str]:
    """Export multiple Party objects to JSON files in out_dir (EX-01)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for p in parties:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in p.name)
        f = out / f"{safe_name}_{p.id[:8]}.json"
        f.write_text(json.dumps(p.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(f))
    return written


def import_parties_from_files(file_paths: list[str]) -> list[Party]:
    """Import multiple Party JSON files (EX-01). Returns loaded Party objects."""
    result: list[Party] = []
    for path in file_paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            result.append(Party.from_dict(data))
        except Exception:
            pass
    return result


def export_master_list(items: list[dict[str, Any]], file_path: str) -> None:
    """Export a master list (moves/abilities/potentials) to a JSON file (EX-02)."""
    Path(file_path).write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def import_master_list(file_path: str) -> list[dict[str, Any]]:
    """Import a master list from a JSON file (EX-02)."""
    try:
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    except Exception:
        return []
