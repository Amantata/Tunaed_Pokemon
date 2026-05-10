"""Pokémon editor tab."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tunaed_pokemon.models.pokemon import (
    Pokemon, IVs, EVs, AssignedPotential, POKEMON_POTENTIAL_SLOTS,
)
from tunaed_pokemon.models.enums import PokemonType
from tunaed_pokemon.utils.persistence import (
    load_all_pokemon, save_pokemon, delete_pokemon, load_moves, load_abilities,
)
from tunaed_pokemon.ui.icon_manager import Icons, SMALL, apply_icon


class PokemonTab(QWidget):
    """Pokémon list + editor."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pokemon: dict[str, Pokemon] = load_all_pokemon()
        self._moves = load_moves()
        self._abilities = load_abilities()
        self._current_id: str | None = None
        self._build_ui()
        self._refresh_list()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        split = QSplitter(Qt.Orientation.Horizontal)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(split)

        # ── Left: list ───────────────────────────────────────────────────────
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(4, 4, 4, 4)
        lbl = QLabel("포켓몬 목록")
        lbl.setObjectName("section_title")
        ll.addWidget(lbl)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_select)
        ll.addWidget(self._list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("추가")
        apply_icon(add_btn, Icons.ADD, SMALL)
        add_btn.clicked.connect(self._add)
        del_btn = QPushButton("삭제")
        apply_icon(del_btn, Icons.DELETE, SMALL)
        del_btn.clicked.connect(self._delete)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        ll.addLayout(btn_row)
        split.addWidget(left)

        # ── Right: form ──────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        right = QWidget()
        scroll.setWidget(right)
        rl = QVBoxLayout(right)
        rl.setSpacing(10)

        # Basic info
        info_grp = QGroupBox("기본 정보")
        info_lay = QFormLayout(info_grp)
        self._name_edit = QLineEdit()
        self._gender_combo = QComboBox()
        for g in ["♂", "♀", "-"]:
            self._gender_combo.addItem(g)
        self._alien_combo = QComboBox()
        self._alien_combo.addItem("아니오", False)
        self._alien_combo.addItem("예 (아인종)", True)
        self._level_spin = QSpinBox()
        self._level_spin.setRange(1, 100)
        self._level_spin.setValue(50)
        self._type1_combo = QComboBox()
        self._type2_combo = QComboBox()
        self._type2_combo.addItem("없음", None)
        for t in PokemonType:
            self._type1_combo.addItem(t.value, t.value)
            self._type2_combo.addItem(t.value, t.value)
        self._ability_combo = QComboBox()
        self._ability_combo.addItem("없음", None)
        for ab in self._abilities.values():
            self._ability_combo.addItem(ab.name, ab.id)
        self._image_edit = QLineEdit()
        self._image_btn = QPushButton("이미지 선택")
        self._image_btn.setIcon(Icons.IMAGE_PICK)
        self._image_btn.setIconSize(SMALL)
        self._image_btn.clicked.connect(self._choose_image)
        img_row = QHBoxLayout()
        img_row.addWidget(self._image_edit)
        img_row.addWidget(self._image_btn)
        info_lay.addRow("이름:", self._name_edit)
        info_lay.addRow("성별:", self._gender_combo)
        info_lay.addRow("아인종:", self._alien_combo)
        info_lay.addRow("레벨:", self._level_spin)
        info_lay.addRow("타입1:", self._type1_combo)
        info_lay.addRow("타입2:", self._type2_combo)
        info_lay.addRow("특성:", self._ability_combo)
        info_lay.addRow("이미지:", img_row)
        rl.addWidget(info_grp)

        # Base stats / IV
        stats_grp = QGroupBox("능력치 (종족치 / 개체치 / 노력치)")
        stats_lay = QFormLayout(stats_grp)
        self._stat_spins: dict[str, tuple[QSpinBox, QSpinBox, QSpinBox]] = {}
        for stat, label in [
            ("hp", "HP"), ("attack", "공격"), ("defense", "방어"),
            ("sp_atk", "특공"), ("sp_def", "특방"), ("speed", "스피드"),
        ]:
            base = QSpinBox(); base.setRange(1, 999); base.setValue(50)
            iv = QSpinBox(); iv.setRange(0, 200)
            ev = QSpinBox(); ev.setRange(0, 252)
            row = QHBoxLayout()
            row.addWidget(QLabel("종:"))
            row.addWidget(base)
            row.addWidget(QLabel("개:"))
            row.addWidget(iv)
            row.addWidget(QLabel("노:"))
            row.addWidget(ev)
            stats_lay.addRow(f"{label}:", row)
            self._stat_spins[stat] = (base, iv, ev)
        rl.addWidget(stats_grp)

        # Moves (up to 8)
        moves_grp = QGroupBox("기술 (4–8개, SK-01)")
        moves_lay = QFormLayout(moves_grp)
        self._move_combos: list[QComboBox] = []
        for i in range(8):
            combo = QComboBox()
            combo.addItem("없음", None)
            for mv in self._moves.values():
                combo.addItem(mv.name, mv.id)
            moves_lay.addRow(f"기술{i+1}:", combo)
            self._move_combos.append(combo)
        rl.addWidget(moves_grp)

        # Potentials (standard slots)
        pot_grp = QGroupBox("포텐셜")
        pot_lay = QFormLayout(pot_grp)
        self._pot_edits: dict[str, QLineEdit] = {}
        for slot in POKEMON_POTENTIAL_SLOTS:
            edit = QLineEdit()
            edit.setPlaceholderText(f"『{slot}』 효과 설명")
            self._pot_edits[slot] = edit
            pot_lay.addRow(f"『{slot}』:", edit)
        rl.addWidget(pot_grp)

        # 전용포텐셜 (SEPARATE field per PT-05)
        excl_grp = QGroupBox("전용포텐셜 (PT-05 — 별도 필드)")
        excl_lay = QFormLayout(excl_grp)
        self._excl_name_edit = QLineEdit()
        self._excl_effect_edit = QTextEdit()
        self._excl_effect_edit.setMaximumHeight(80)
        excl_lay.addRow("이름:", self._excl_name_edit)
        excl_lay.addRow("효과:", self._excl_effect_edit)
        rl.addWidget(excl_grp)

        # Notes
        notes_grp = QGroupBox("메모")
        notes_lay = QVBoxLayout(notes_grp)
        self._notes_edit = QTextEdit()
        self._notes_edit.setMaximumHeight(60)
        notes_lay.addWidget(self._notes_edit)
        rl.addWidget(notes_grp)

        save_btn = QPushButton("저장")
        apply_icon(save_btn, Icons.SAVE, SMALL)
        save_btn.clicked.connect(self._save)
        rl.addWidget(save_btn)
        rl.addStretch()

        split.addWidget(scroll)
        split.setSizes([220, 500])

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_list(self) -> None:
        self._list.clear()
        for p in self._pokemon.values():
            item = QListWidgetItem(p.name or "(이름 없음)")
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self._list.addItem(item)

    def _populate_form(self, p: Pokemon) -> None:
        self._name_edit.setText(p.name)
        idx = self._gender_combo.findText(p.gender)
        if idx >= 0:
            self._gender_combo.setCurrentIndex(idx)
        self._alien_combo.setCurrentIndex(1 if p.is_alien else 0)
        self._level_spin.setValue(p.level)
        idx = self._type1_combo.findData(p.type1)
        if idx >= 0:
            self._type1_combo.setCurrentIndex(idx)
        idx = self._type2_combo.findData(p.type2)
        if idx >= 0:
            self._type2_combo.setCurrentIndex(idx)
        idx = self._ability_combo.findData(p.ability_id)
        if idx >= 0:
            self._ability_combo.setCurrentIndex(idx)
        self._image_edit.setText(p.image_path)
        for stat, (base_s, iv_s, ev_s) in self._stat_spins.items():
            base_s.setValue(p.base_stats.get(stat, 50))
            iv_s.setValue(getattr(p.ivs, stat, 0))
            ev_s.setValue(getattr(p.evs, stat, 0))
        pot_map = {pt.slot: pt.effect for pt in p.potentials}
        for slot, edit in self._pot_edits.items():
            edit.setText(pot_map.get(slot, ""))
        for i, combo in enumerate(self._move_combos):
            mid = p.move_ids[i] if i < len(p.move_ids) else None
            idx = combo.findData(mid)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        if p.exclusive_potential:
            self._excl_name_edit.setText(p.exclusive_potential.name)
            self._excl_effect_edit.setPlainText(p.exclusive_potential.effect)
        else:
            self._excl_name_edit.clear()
            self._excl_effect_edit.clear()
        self._notes_edit.setPlainText(p.notes)

    def _form_to_pokemon(self, p: Pokemon) -> None:
        p.name = self._name_edit.text().strip()
        p.gender = self._gender_combo.currentText()
        p.is_alien = bool(self._alien_combo.currentData())
        p.level = self._level_spin.value()
        p.type1 = self._type1_combo.currentData()
        p.type2 = self._type2_combo.currentData()
        p.ability_id = self._ability_combo.currentData()
        ab = self._abilities.get(p.ability_id) if p.ability_id else None
        p.ability_name = ab.name if ab else ""
        p.image_path = self._image_edit.text().strip()
        for stat, (base_s, iv_s, ev_s) in self._stat_spins.items():
            p.base_stats[stat] = base_s.value()
            setattr(p.ivs, stat, iv_s.value())
            setattr(p.evs, stat, ev_s.value())
        p.move_ids = [
            combo.currentData() for combo in self._move_combos
            if combo.currentData()
        ]
        p.potentials = [
            AssignedPotential(slot=slot, effect=edit.text().strip())
            for slot, edit in self._pot_edits.items()
            if edit.text().strip()
        ]
        name_e = self._excl_name_edit.text().strip()
        effect_e = self._excl_effect_edit.toPlainText().strip()
        p.exclusive_potential = (
            AssignedPotential(slot="전용포텐셜", name=name_e, effect=effect_e)
            if name_e or effect_e else None
        )
        p.notes = self._notes_edit.toPlainText().strip()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_select(self, item: QListWidgetItem | None, _prev=None) -> None:
        if item is None:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        p = self._pokemon.get(pid)
        if p:
            self._current_id = pid
            self._populate_form(p)

    def _add(self) -> None:
        p = Pokemon.new("새 포켓몬")
        self._pokemon[p.id] = p
        save_pokemon(p)
        self._refresh_list()
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.ItemDataRole.UserRole) == p.id:
                self._list.setCurrentRow(i)
                break

    def _delete(self) -> None:
        if not self._current_id:
            return
        p = self._pokemon.get(self._current_id)
        name = p.name if p else self._current_id
        reply = QMessageBox.question(
            self, "삭제 확인", f"'{name}'을(를) 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_pokemon(self._current_id)
            self._pokemon.pop(self._current_id, None)
            self._current_id = None
            self._refresh_list()

    def _save(self) -> None:
        if not self._current_id:
            return
        p = self._pokemon.get(self._current_id)
        if not p:
            return
        self._form_to_pokemon(p)
        save_pokemon(p)
        self._refresh_list()

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "이미지 선택", "", "이미지 (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self._image_edit.setText(path)
