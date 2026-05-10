"""Master list editor tab — CRUD for moves, abilities, and potentials (SK-01, SK-03, PT-02).

Provides import/export of each list as JSON files (EX-02).
All icons use custom SVGs (no emoji).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tunaed_pokemon.models.pokemon import MoveData, AbilityData, PotentialData
from tunaed_pokemon.utils.persistence import (
    load_moves, save_moves,
    load_abilities, save_abilities,
    load_potentials, save_potentials,
    export_master_list, import_master_list,
)
from tunaed_pokemon.ui.icon_manager import Icons, SMALL, apply_icon


class _ItemListPanel(QWidget):
    """Generic list panel with add/delete/import/export — reused for all three master lists."""

    def __init__(self, item_label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._item_label = item_label
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lbl = QLabel(self._item_label)
        lbl.setObjectName("section_title")
        lay.addWidget(lbl)

        self.list_widget = QListWidget()
        lay.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("추가")
        apply_icon(self.add_btn, Icons.ADD, SMALL)
        self.del_btn = QPushButton("삭제")
        apply_icon(self.del_btn, Icons.DELETE, SMALL)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.del_btn)
        lay.addLayout(btn_row)

        io_row = QHBoxLayout()
        self.imp_btn = QPushButton("가져오기")
        apply_icon(self.imp_btn, Icons.IMPORT, SMALL)
        self.imp_btn.setToolTip("JSON 파일에서 가져오기 (EX-02)")
        self.exp_btn = QPushButton("내보내기")
        apply_icon(self.exp_btn, Icons.EXPORT, SMALL)
        self.exp_btn.setToolTip("JSON 파일로 내보내기 (EX-02)")
        io_row.addWidget(self.imp_btn)
        io_row.addWidget(self.exp_btn)
        lay.addLayout(io_row)


# ── Move List Editor ──────────────────────────────────────────────────────────

class MoveListTab(QWidget):
    """기술 목록 CRUD (SK-01) with import/export (EX-02)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._moves = load_moves()
        self._current_id: str | None = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        split = QSplitter(Qt.Orientation.Horizontal)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(split)

        self._list_panel = _ItemListPanel("기술 목록 (SK-01)")
        self._list_panel.list_widget.currentItemChanged.connect(self._on_select)
        self._list_panel.add_btn.clicked.connect(self._add)
        self._list_panel.del_btn.clicked.connect(self._delete)
        self._list_panel.imp_btn.clicked.connect(self._import)
        self._list_panel.exp_btn.clicked.connect(self._export)
        split.addWidget(self._list_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        right = QWidget()
        scroll.setWidget(right)
        rl = QVBoxLayout(right)

        grp = QGroupBox("기술 상세")
        gl = QFormLayout(grp)
        self._name_e = QLineEdit()
        self._type_e = QLineEdit()
        self._cat_e = QLineEdit()
        self._power_e = QSpinBox(); self._power_e.setRange(0, 999); self._power_e.setSpecialValueText("없음")
        self._acc_e = QSpinBox(); self._acc_e.setRange(0, 100); self._acc_e.setSpecialValueText("—"  )
        self._pp_e = QSpinBox(); self._pp_e.setRange(1, 64)
        self._effect_e = QTextEdit(); self._effect_e.setMaximumHeight(60)
        self._script_e = QPlainTextEdit(); self._script_e.setMaximumHeight(80)
        gl.addRow("이름:", self._name_e)
        gl.addRow("타입:", self._type_e)
        gl.addRow("분류:", self._cat_e)
        gl.addRow("위력:", self._power_e)
        gl.addRow("명중:", self._acc_e)
        gl.addRow("PP:", self._pp_e)
        gl.addRow("효과 설명:", self._effect_e)
        gl.addRow("효과 스크립트:", self._script_e)
        rl.addWidget(grp)

        save_btn = QPushButton("저장")
        apply_icon(save_btn, Icons.SAVE, SMALL)
        save_btn.clicked.connect(self._save)
        rl.addWidget(save_btn)
        rl.addStretch()
        split.addWidget(scroll)
        split.setSizes([220, 500])

    def _refresh_list(self) -> None:
        self._list_panel.list_widget.clear()
        for m in self._moves.values():
            item = QListWidgetItem(m.name)
            item.setData(Qt.ItemDataRole.UserRole, m.id)
            self._list_panel.list_widget.addItem(item)

    def _populate(self, m: MoveData) -> None:
        self._name_e.setText(m.name)
        self._type_e.setText(m.type)
        self._cat_e.setText(m.category)
        self._power_e.setValue(m.power or 0)
        self._acc_e.setValue(m.accuracy or 0)
        self._pp_e.setValue(m.pp)
        self._effect_e.setPlainText(m.effect)
        self._script_e.setPlainText(m.effect_script)

    def _form_to(self, m: MoveData) -> None:
        m.name = self._name_e.text().strip()
        m.type = self._type_e.text().strip()
        m.category = self._cat_e.text().strip()
        p = self._power_e.value()
        m.power = p if p > 0 else None
        a = self._acc_e.value()
        m.accuracy = a if a > 0 else None
        m.pp = self._pp_e.value()
        m.effect = self._effect_e.toPlainText().strip()
        m.effect_script = self._script_e.toPlainText().strip()

    def _on_select(self, item, _prev=None) -> None:
        if item is None:
            return
        mid = item.data(Qt.ItemDataRole.UserRole)
        m = self._moves.get(mid)
        if m:
            self._current_id = mid
            self._populate(m)

    def _add(self) -> None:
        m = MoveData.new("새 기술")
        self._moves[m.id] = m
        save_moves(self._moves)
        self._refresh_list()

    def _delete(self) -> None:
        if not self._current_id:
            return
        m = self._moves.get(self._current_id)
        reply = QMessageBox.question(
            self, "삭제 확인", f"'{m.name if m else self._current_id}'을(를) 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._moves.pop(self._current_id, None)
            self._current_id = None
            save_moves(self._moves)
            self._refresh_list()

    def _save(self) -> None:
        if not self._current_id:
            return
        m = self._moves.get(self._current_id)
        if m:
            self._form_to(m)
            save_moves(self._moves)
            self._refresh_list()

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "기술 목록 가져오기", "", "JSON (*.json)")
        if not path:
            return
        items = import_master_list(path)
        for d in items:
            try:
                m = MoveData.from_dict(d)
                self._moves[m.id] = m
            except Exception:
                pass
        save_moves(self._moves)
        self._refresh_list()
        QMessageBox.information(self, "가져오기 완료", f"{len(items)}개 기술을 가져왔습니다.")

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "기술 목록 내보내기", "moves.json", "JSON (*.json)")
        if path:
            export_master_list([m.to_dict() for m in self._moves.values()], path)
            QMessageBox.information(self, "내보내기 완료", f"저장됨: {path}")


# ── Ability List Editor ───────────────────────────────────────────────────────

class AbilityListTab(QWidget):
    """특성 목록 CRUD (SK-03) with import/export (EX-02)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._abilities = load_abilities()
        self._current_id: str | None = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        split = QSplitter(Qt.Orientation.Horizontal)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(split)

        self._list_panel = _ItemListPanel("특성 목록 (SK-03)")
        self._list_panel.list_widget.currentItemChanged.connect(self._on_select)
        self._list_panel.add_btn.clicked.connect(self._add)
        self._list_panel.del_btn.clicked.connect(self._delete)
        self._list_panel.imp_btn.clicked.connect(self._import)
        self._list_panel.exp_btn.clicked.connect(self._export)
        split.addWidget(self._list_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        right = QWidget()
        scroll.setWidget(right)
        rl = QVBoxLayout(right)

        grp = QGroupBox("특성 상세")
        gl = QFormLayout(grp)
        self._name_e = QLineEdit()
        self._effect_e = QTextEdit(); self._effect_e.setMaximumHeight(80)
        self._script_e = QPlainTextEdit(); self._script_e.setMaximumHeight(100)
        gl.addRow("이름:", self._name_e)
        gl.addRow("효과 설명:", self._effect_e)
        gl.addRow("효과 스크립트:", self._script_e)
        rl.addWidget(grp)

        save_btn = QPushButton("저장")
        apply_icon(save_btn, Icons.SAVE, SMALL)
        save_btn.clicked.connect(self._save)
        rl.addWidget(save_btn)
        rl.addStretch()
        split.addWidget(scroll)
        split.setSizes([220, 500])

    def _refresh_list(self) -> None:
        self._list_panel.list_widget.clear()
        for a in self._abilities.values():
            item = QListWidgetItem(a.name)
            item.setData(Qt.ItemDataRole.UserRole, a.id)
            self._list_panel.list_widget.addItem(item)

    def _populate(self, a: AbilityData) -> None:
        self._name_e.setText(a.name)
        self._effect_e.setPlainText(a.effect)
        self._script_e.setPlainText(a.effect_script)

    def _form_to(self, a: AbilityData) -> None:
        a.name = self._name_e.text().strip()
        a.effect = self._effect_e.toPlainText().strip()
        a.effect_script = self._script_e.toPlainText().strip()

    def _on_select(self, item, _prev=None) -> None:
        if item is None:
            return
        aid = item.data(Qt.ItemDataRole.UserRole)
        a = self._abilities.get(aid)
        if a:
            self._current_id = aid
            self._populate(a)

    def _add(self) -> None:
        a = AbilityData.new("새 특성")
        self._abilities[a.id] = a
        save_abilities(self._abilities)
        self._refresh_list()

    def _delete(self) -> None:
        if not self._current_id:
            return
        a = self._abilities.get(self._current_id)
        reply = QMessageBox.question(
            self, "삭제 확인", f"'{a.name if a else self._current_id}'을(를) 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._abilities.pop(self._current_id, None)
            self._current_id = None
            save_abilities(self._abilities)
            self._refresh_list()

    def _save(self) -> None:
        if not self._current_id:
            return
        a = self._abilities.get(self._current_id)
        if a:
            self._form_to(a)
            save_abilities(self._abilities)
            self._refresh_list()

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "특성 목록 가져오기", "", "JSON (*.json)")
        if not path:
            return
        items = import_master_list(path)
        for d in items:
            try:
                a = AbilityData.from_dict(d)
                self._abilities[a.id] = a
            except Exception:
                pass
        save_abilities(self._abilities)
        self._refresh_list()
        QMessageBox.information(self, "가져오기 완료", f"{len(items)}개 특성을 가져왔습니다.")

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "특성 목록 내보내기", "abilities.json", "JSON (*.json)")
        if path:
            export_master_list([a.to_dict() for a in self._abilities.values()], path)
            QMessageBox.information(self, "내보내기 완료", f"저장됨: {path}")


# ── Potential List Editor ─────────────────────────────────────────────────────

class PotentialListTab(QWidget):
    """포텐셜 목록 CRUD (PT-02) with import/export (EX-02)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._potentials = load_potentials()
        self._current_id: str | None = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        split = QSplitter(Qt.Orientation.Horizontal)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(split)

        self._list_panel = _ItemListPanel("포텐셜 목록 (PT-02)")
        self._list_panel.list_widget.currentItemChanged.connect(self._on_select)
        self._list_panel.add_btn.clicked.connect(self._add)
        self._list_panel.del_btn.clicked.connect(self._delete)
        self._list_panel.imp_btn.clicked.connect(self._import)
        self._list_panel.exp_btn.clicked.connect(self._export)
        split.addWidget(self._list_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        right = QWidget()
        scroll.setWidget(right)
        rl = QVBoxLayout(right)

        grp = QGroupBox("포텐셜 상세")
        gl = QFormLayout(grp)
        self._category_e = QLineEdit()
        self._name_e = QLineEdit()
        self._trigger_e = QTextEdit(); self._trigger_e.setMaximumHeight(60)
        self._effect_e = QTextEdit(); self._effect_e.setMaximumHeight(60)
        self._script_e = QPlainTextEdit(); self._script_e.setMaximumHeight(100)
        gl.addRow("분류:", self._category_e)
        gl.addRow("이름:", self._name_e)
        gl.addRow("발동 조건:", self._trigger_e)
        gl.addRow("효과:", self._effect_e)
        gl.addRow("스크립트:", self._script_e)
        rl.addWidget(grp)

        save_btn = QPushButton("저장")
        apply_icon(save_btn, Icons.SAVE, SMALL)
        save_btn.clicked.connect(self._save)
        rl.addWidget(save_btn)
        rl.addStretch()
        split.addWidget(scroll)
        split.setSizes([220, 500])

    def _refresh_list(self) -> None:
        self._list_panel.list_widget.clear()
        for p in self._potentials.values():
            label = f"[{p.category}] {p.name}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self._list_panel.list_widget.addItem(item)

    def _populate(self, p: PotentialData) -> None:
        self._category_e.setText(p.category)
        self._name_e.setText(p.name)
        self._trigger_e.setPlainText(p.trigger)
        self._effect_e.setPlainText(p.effect)
        self._script_e.setPlainText(p.script)

    def _form_to(self, p: PotentialData) -> None:
        p.category = self._category_e.text().strip()
        p.name = self._name_e.text().strip()
        p.trigger = self._trigger_e.toPlainText().strip()
        p.effect = self._effect_e.toPlainText().strip()
        p.script = self._script_e.toPlainText().strip()

    def _on_select(self, item, _prev=None) -> None:
        if item is None:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        p = self._potentials.get(pid)
        if p:
            self._current_id = pid
            self._populate(p)

    def _add(self) -> None:
        p = PotentialData.new("범용", "새 포텐셜")
        self._potentials[p.id] = p
        save_potentials(self._potentials)
        self._refresh_list()

    def _delete(self) -> None:
        if not self._current_id:
            return
        p = self._potentials.get(self._current_id)
        reply = QMessageBox.question(
            self, "삭제 확인", f"'{p.name if p else self._current_id}'을(를) 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._potentials.pop(self._current_id, None)
            self._current_id = None
            save_potentials(self._potentials)
            self._refresh_list()

    def _save(self) -> None:
        if not self._current_id:
            return
        p = self._potentials.get(self._current_id)
        if p:
            self._form_to(p)
            save_potentials(self._potentials)
            self._refresh_list()

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "포텐셜 목록 가져오기", "", "JSON (*.json)")
        if not path:
            return
        items = import_master_list(path)
        for d in items:
            try:
                p = PotentialData.from_dict(d)
                self._potentials[p.id] = p
            except Exception:
                pass
        save_potentials(self._potentials)
        self._refresh_list()
        QMessageBox.information(self, "가져오기 완료", f"{len(items)}개 포텐셜을 가져왔습니다.")

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "포텐셜 목록 내보내기", "potentials.json", "JSON (*.json)")
        if path:
            export_master_list([p.to_dict() for p in self._potentials.values()], path)
            QMessageBox.information(self, "내보내기 완료", f"저장됨: {path}")
