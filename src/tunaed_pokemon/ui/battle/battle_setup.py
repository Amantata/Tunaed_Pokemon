"""Battle setup dialog — shown before the battle window opens.

The user picks two parties (or enters trainer names without saved party data)
and chooses a battle format.  This dialog sits between the launcher and the
battle window; the editor is NOT accessible from here.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from tunaed_pokemon.utils.persistence import load_all_parties, load_all_trainers, load_all_pokemon
from tunaed_pokemon.models.party import Party
from tunaed_pokemon.models.enums import BattleFormat
from tunaed_pokemon.engine.battle_state import (
    BattleStateSnapshot,
    BattleSideState,
    BattlePokemonState,
)
from tunaed_pokemon.utils.stat_calc import calc_hp, calc_stat


def _build_side_state(party: Party | None, trainers: dict, pokemon: dict,
                      trainer_name: str, side_label: str) -> BattleSideState:
    """Build a BattleSideState from a Party (or a blank placeholder)."""
    if party is None:
        return BattleSideState(trainer_id=None, trainer_name=trainer_name or side_label, party_id=None)

    t = trainers.get(party.trainer_id or "") if party.trainer_id else None
    t_name = trainer_name or (t.name if t else side_label)

    pokemon_states: list[BattlePokemonState] = []
    for pid in party.pokemon_ids:
        p = pokemon.get(pid)
        if p is None:
            continue
        bs = p.base_stats
        iv = p.ivs
        ev = p.evs
        max_hp = calc_hp(bs.get("hp", 50), iv.hp, ev.hp, p.level)
        # Compute all battle stats and store them for use by DamageCalculator
        battle_stats = {
            "hp":      max_hp,
            "attack":  calc_stat(bs.get("attack",  50), iv.attack,  ev.attack,  p.level),
            "defense": calc_stat(bs.get("defense", 50), iv.defense, ev.defense, p.level),
            "sp_atk":  calc_stat(bs.get("sp_atk",  50), iv.sp_atk,  ev.sp_atk,  p.level),
            "sp_def":  calc_stat(bs.get("sp_def",  50), iv.sp_def,  ev.sp_def,  p.level),
            "speed":   calc_stat(bs.get("speed",   50), iv.speed,   ev.speed,   p.level),
        }
        pokemon_states.append(BattlePokemonState(
            pokemon_id=p.id,
            name=p.name,
            current_hp=max_hp,
            max_hp=max_hp,
            level=p.level,
            type1=p.type1,
            type2=p.type2,
            ability_name=p.ability_name,
            move_ids=list(p.move_ids),
            potentials=[pt for pt in p.potentials],
            exclusive_potential=p.exclusive_potential,
            battle_stats=battle_stats,
        ))

    return BattleSideState(
        trainer_id=party.trainer_id,
        trainer_name=t_name,
        party_id=party.id,
        pokemon_states=pokemon_states,
        active_indices=[0] if pokemon_states else [],
    )


class BattleSetupDialog(QDialog):
    """Dialog for configuring a battle before opening the BattleWindow."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("전투 설정")
        self.setMinimumWidth(440)
        self._parties = load_all_parties()
        self._trainers = load_all_trainers()
        self._pokemon = load_all_pokemon()
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Format selection
        fmt_grp = QGroupBox("배틀 형식")
        fmt_lay = QFormLayout(fmt_grp)
        self._fmt_combo = QComboBox()
        for fmt in BattleFormat:
            self._fmt_combo.addItem(fmt.value, fmt)
        fmt_lay.addRow("형식:", self._fmt_combo)
        layout.addWidget(fmt_grp)

        # Side 1
        self._side1_grp = self._make_side_group("플레이어 1 (내 편)")
        layout.addWidget(self._side1_grp["group"])

        # Side 2
        self._side2_grp = self._make_side_group("플레이어 2 (상대편)")
        layout.addWidget(self._side2_grp["group"])

        # Buttons
        demo_btn = QPushButton("데모 파티 생성 (문서 기반 4파티)")
        demo_btn.setToolTip("트레이너 예제/샘플2/샘플3 기반 데모 파티 4개를 생성합니다.")
        demo_btn.clicked.connect(self._create_demo_parties)
        layout.addWidget(demo_btn)

        # Start / Cancel
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("전투 시작")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _make_side_group(self, label: str) -> dict[str, Any]:
        grp = QGroupBox(label)
        lay = QFormLayout(grp)

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("트레이너 이름 (선택)")
        lay.addRow("트레이너:", name_edit)

        party_combo = QComboBox()
        party_combo.addItem("(파티 없음)", None)
        for p in self._parties.values():
            party_combo.addItem(p.name, p.id)
        lay.addRow("파티:", party_combo)

        return {"group": grp, "name": name_edit, "party": party_combo}

    def _create_demo_parties(self) -> None:
        """Generate demo parties and refresh the party combo boxes."""
        from tunaed_pokemon.utils.seed_data import create_demo_parties
        demo_party_ids = create_demo_parties()
        # Reload party list and refresh combos
        self._parties = load_all_parties()
        self._trainers = load_all_trainers()
        self._pokemon = load_all_pokemon()
        self._refresh_party_combos()
        # Auto-select the first 2 created demo parties
        preferred = list(demo_party_ids[:2])
        while len(preferred) < 2:
            preferred.append(None)
        for grp, demo_id in [(self._side1_grp, preferred[0]), (self._side2_grp, preferred[1])]:
            combo: QComboBox = grp["party"]
            idx = combo.findData(demo_id)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def _refresh_party_combos(self) -> None:
        """Repopulate both party combo boxes from self._parties."""
        for grp in (self._side1_grp, self._side2_grp):
            combo: QComboBox = grp["party"]
            current = combo.currentData()
            combo.clear()
            combo.addItem("(파티 없음)", None)
            for p in self._parties.values():
                combo.addItem(p.name, p.id)
            idx = combo.findData(current)
            combo.setCurrentIndex(max(0, idx))


    # ── Result ────────────────────────────────────────────────────────────────

    def get_config(self) -> dict[str, Any]:
        """Build and return the initial BattleStateSnapshot config dict."""
        fmt: BattleFormat = self._fmt_combo.currentData()

        def resolve(grp: dict[str, Any], fallback: str) -> BattleSideState:
            pid = grp["party"].currentData()
            party = self._parties.get(pid) if pid else None
            return _build_side_state(party, self._trainers, self._pokemon,
                                     grp["name"].text().strip(), fallback)

        s1 = resolve(self._side1_grp, "플레이어 1")
        s2 = resolve(self._side2_grp, "플레이어 2")

        snapshot = BattleStateSnapshot(
            turn_number=0,
            battle_format=fmt.value,
            side1=s1,
            side2=s2,
        )
        return {"snapshot": snapshot, "format": fmt}
