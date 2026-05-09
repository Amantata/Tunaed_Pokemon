"""Party builder tab."""

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
    QVBoxLayout,
    QWidget,
)

from tunaed_pokemon.models.party import Party
from tunaed_pokemon.utils.persistence import (
    load_all_parties,
    load_all_trainers,
    load_all_pokemon,
    save_party,
    delete_party,
    export_parties_to_files,
    import_parties_from_files,
)
from tunaed_pokemon.ui.icon_manager import Icons, SMALL, apply_icon


class PartyTab(QWidget):
    """Party builder — list + editor with import/export (EX-01)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._parties: dict[str, Party] = load_all_parties()
        self._trainers = load_all_trainers()
        self._pokemon = load_all_pokemon()
        self._current_id: str | None = None
        self._build_ui()
        self._refresh_list()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        split = QSplitter(Qt.Orientation.Horizontal)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(split)

        # ── Left ─────────────────────────────────────────────────────────────
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(4, 4, 4, 4)
        lbl = QLabel("파티 목록")
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

        # Import / Export (EX-01)
        imp_btn = QPushButton("가져오기")
        apply_icon(imp_btn, Icons.IMPORT, SMALL)
        imp_btn.setToolTip("JSON 파일에서 파티 불러오기 (복수 선택 가능)")
        imp_btn.clicked.connect(self._import)
        exp_btn = QPushButton("내보내기")
        apply_icon(exp_btn, Icons.EXPORT, SMALL)
        exp_btn.setToolTip("선택된 파티를 JSON 파일로 내보내기")
        exp_btn.clicked.connect(self._export)
        io_row = QHBoxLayout()
        io_row.addWidget(imp_btn)
        io_row.addWidget(exp_btn)
        ll.addLayout(io_row)

        split.addWidget(left)

        # ── Right ─────────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        right = QWidget()
        scroll.setWidget(right)
        rl = QVBoxLayout(right)
        rl.setSpacing(10)

        # Party info
        info_grp = QGroupBox("파티 정보")
        info_lay = QFormLayout(info_grp)
        self._name_edit = QLineEdit()
        self._trainer_combo = QComboBox()
        self._trainer_combo.addItem("(트레이너 없음)", None)
        for t in self._trainers.values():
            self._trainer_combo.addItem(t.name, t.id)
        self._max_size_spin = QSpinBox()
        self._max_size_spin.setRange(1, 8)
        self._max_size_spin.setValue(6)
        info_lay.addRow("파티 이름:", self._name_edit)
        info_lay.addRow("트레이너:", self._trainer_combo)
        info_lay.addRow("최대 파티원 수:", self._max_size_spin)
        rl.addWidget(info_grp)

        # Member slots
        members_grp = QGroupBox("파티원 (1–8명, P-02)")
        members_lay = QFormLayout(members_grp)
        self._member_combos: list[QComboBox] = []
        for i in range(8):
            combo = QComboBox()
            combo.addItem("(없음)", None)
            for p in self._pokemon.values():
                combo.addItem(p.name, p.id)
            members_lay.addRow(f"파티원 {i+1}:", combo)
            self._member_combos.append(combo)
        rl.addWidget(members_grp)

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
        for p in self._parties.values():
            item = QListWidgetItem(p.name or "(이름 없음)")
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self._list.addItem(item)

    def _populate_form(self, p: Party) -> None:
        self._name_edit.setText(p.name)
        idx = self._trainer_combo.findData(p.trainer_id)
        self._trainer_combo.setCurrentIndex(max(0, idx))
        self._max_size_spin.setValue(p.max_size)
        for i, combo in enumerate(self._member_combos):
            mid = p.pokemon_ids[i] if i < len(p.pokemon_ids) else None
            idx = combo.findData(mid)
            combo.setCurrentIndex(max(0, idx))

    def _form_to_party(self, p: Party) -> None:
        p.name = self._name_edit.text().strip()
        p.trainer_id = self._trainer_combo.currentData()
        p.max_size = self._max_size_spin.value()
        p.pokemon_ids = [
            combo.currentData()
            for combo in self._member_combos
            if combo.currentData()
        ]

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_select(self, item: QListWidgetItem | None, _prev=None) -> None:
        if item is None:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        p = self._parties.get(pid)
        if p:
            self._current_id = pid
            self._populate_form(p)

    def _add(self) -> None:
        p = Party.new("새 파티")
        self._parties[p.id] = p
        save_party(p)
        self._refresh_list()
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.ItemDataRole.UserRole) == p.id:
                self._list.setCurrentRow(i)
                break

    def _delete(self) -> None:
        if not self._current_id:
            return
        p = self._parties.get(self._current_id)
        name = p.name if p else self._current_id
        reply = QMessageBox.question(
            self, "삭제 확인", f"'{name}'을(를) 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_party(self._current_id)
            self._parties.pop(self._current_id, None)
            self._current_id = None
            self._refresh_list()

    def _save(self) -> None:
        if not self._current_id:
            return
        p = self._parties.get(self._current_id)
        if not p:
            return
        self._form_to_party(p)
        save_party(p)
        self._refresh_list()

    def _import(self) -> None:
        """Import multiple party JSON files (EX-01)."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "파티 파일 가져오기", "", "JSON (*.json)"
        )
        if not paths:
            return
        imported = import_parties_from_files(paths)
        for p in imported:
            self._parties[p.id] = p
            save_party(p)
        self._refresh_list()
        QMessageBox.information(self, "가져오기 완료", f"{len(imported)}개 파티를 가져왔습니다.")

    def _export(self) -> None:
        """Export all parties to a directory (EX-01)."""
        if not self._parties:
            QMessageBox.information(self, "내보내기", "내보낼 파티가 없습니다.")
            return
        out_dir = QFileDialog.getExistingDirectory(self, "내보낼 폴더 선택")
        if not out_dir:
            return
        written = export_parties_to_files(list(self._parties.values()), out_dir)
        QMessageBox.information(
            self, "내보내기 완료", f"{len(written)}개 파일로 내보냈습니다.\n{out_dir}"
        )
