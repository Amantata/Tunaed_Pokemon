"""Trainer editor tab."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
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
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tunaed_pokemon.models.trainer import Trainer, InnatePotential, CommandPotential
from tunaed_pokemon.models.enums import QualityName, QualityRank
from tunaed_pokemon.utils.persistence import (
    load_all_trainers,
    save_trainer,
    delete_trainer,
)


class TrainerTab(QWidget):
    """Trainer list + editor."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._trainers: dict[str, Trainer] = load_all_trainers()
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
        lbl = QLabel("트레이너 목록")
        lbl.setObjectName("section_title")
        ll.addWidget(lbl)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_select)
        ll.addWidget(self._list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ 추가")
        add_btn.clicked.connect(self._add)
        del_btn = QPushButton("🗑 삭제")
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
        self._alias_edit = QLineEdit()
        self._origin_edit = QLineEdit()
        self._career_edit = QTextEdit()
        self._career_edit.setMaximumHeight(60)
        self._image_edit = QLineEdit()
        self._image_btn = QPushButton("이미지 선택")
        self._image_btn.clicked.connect(self._choose_image)
        img_row = QHBoxLayout()
        img_row.addWidget(self._image_edit)
        img_row.addWidget(self._image_btn)
        info_lay.addRow("이름:", self._name_edit)
        info_lay.addRow("별칭:", self._alias_edit)
        info_lay.addRow("출신:", self._origin_edit)
        info_lay.addRow("경력:", self._career_edit)
        info_lay.addRow("이미지:", img_row)
        rl.addWidget(info_grp)

        # Qualities
        qual_grp = QGroupBox("자질 평가")
        qual_lay = QFormLayout(qual_grp)
        self._quality_combos: dict[str, QComboBox] = {}
        for qn in QualityName:
            combo = QComboBox()
            for qr in QualityRank:
                combo.addItem(f"{qr.value} ({qr.points}pt)", qr.value)
            self._quality_combos[qn.value] = combo
            qual_lay.addRow(f"{qn.value}:", combo)
        rl.addWidget(qual_grp)

        # 고유포텐셜
        innate_grp = QGroupBox("고유포텐셜 (PT-05)")
        innate_lay = QVBoxLayout(innate_grp)
        self._innate_edit = QTextEdit()
        self._innate_edit.setPlaceholderText("각 줄에 하나씩 포텐셜 이름을 입력하세요")
        self._innate_edit.setMaximumHeight(80)
        innate_lay.addWidget(self._innate_edit)
        rl.addWidget(innate_grp)

        # Notes
        notes_grp = QGroupBox("메모")
        notes_lay = QVBoxLayout(notes_grp)
        self._notes_edit = QTextEdit()
        self._notes_edit.setMaximumHeight(60)
        notes_lay.addWidget(self._notes_edit)
        rl.addWidget(notes_grp)

        # Save button
        save_btn = QPushButton("💾 저장")
        save_btn.clicked.connect(self._save)
        rl.addWidget(save_btn)
        rl.addStretch()

        split.addWidget(scroll)
        split.setSizes([220, 500])

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_list(self) -> None:
        self._list.clear()
        for t in self._trainers.values():
            item = QListWidgetItem(t.name or "(이름 없음)")
            item.setData(Qt.ItemDataRole.UserRole, t.id)
            self._list.addItem(item)

    def _populate_form(self, t: Trainer) -> None:
        self._name_edit.setText(t.name)
        self._alias_edit.setText(t.alias)
        self._origin_edit.setText(t.origin)
        self._career_edit.setPlainText(t.career)
        self._image_edit.setText(t.image_path)
        for q in t.qualities:
            combo = self._quality_combos.get(q.name)
            if combo:
                idx = combo.findData(q.rank)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
        innate_text = "\n".join(ip.name for ip in t.innate_potentials)
        self._innate_edit.setPlainText(innate_text)
        self._notes_edit.setPlainText(t.notes)

    def _form_to_trainer(self, t: Trainer) -> None:
        t.name = self._name_edit.text().strip()
        t.alias = self._alias_edit.text().strip()
        t.origin = self._origin_edit.text().strip()
        t.career = self._career_edit.toPlainText().strip()
        t.image_path = self._image_edit.text().strip()
        for q in t.qualities:
            combo = self._quality_combos.get(q.name)
            if combo:
                q.rank = combo.currentData()
        innate_names = [n.strip() for n in self._innate_edit.toPlainText().split("\n") if n.strip()]
        t.innate_potentials = [InnatePotential(name=n) for n in innate_names]
        t.notes = self._notes_edit.toPlainText().strip()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_select(self, item: QListWidgetItem | None, _prev=None) -> None:
        if item is None:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        t = self._trainers.get(tid)
        if t:
            self._current_id = tid
            self._populate_form(t)

    def _add(self) -> None:
        t = Trainer.new("새 트레이너")
        self._trainers[t.id] = t
        save_trainer(t)
        self._refresh_list()
        # Select the new item
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.ItemDataRole.UserRole) == t.id:
                self._list.setCurrentRow(i)
                break

    def _delete(self) -> None:
        if not self._current_id:
            return
        t = self._trainers.get(self._current_id)
        name = t.name if t else self._current_id
        reply = QMessageBox.question(
            self, "삭제 확인", f"'{name}'을(를) 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_trainer(self._current_id)
            self._trainers.pop(self._current_id, None)
            self._current_id = None
            self._refresh_list()

    def _save(self) -> None:
        if not self._current_id:
            return
        t = self._trainers.get(self._current_id)
        if not t:
            return
        self._form_to_trainer(t)
        save_trainer(t)
        self._refresh_list()

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "이미지 선택", "", "이미지 (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self._image_edit.setText(path)
