"""Reusable widgets for the battle screen.

Widgets exported:
  • PokemonPanel   — shows one Pokémon's HP, status, level, rank stages
  • FieldStateBar  — shows weather, terrain, global effects, special field
  • CommandPanel   — move buttons + switch/flee actions
  • BattleLogPanel — scrolling text log of battle events

All visual indicators use custom SVG icons (no emoji).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tunaed_pokemon.engine.battle_state import BattlePokemonState, BattleSideState
from tunaed_pokemon.engine.field_state import FieldStateManager
from tunaed_pokemon.models.enums import Weather, Terrain, SpecialField
from tunaed_pokemon.utils.persistence import load_moves
from tunaed_pokemon.ui.icon_manager import Icons, SMALL


# ── HP Bar colour helper ──────────────────────────────────────────────────────

def _hp_colour(fraction: float) -> str:
    if fraction > 0.5:
        return "#4CAF50"   # green
    if fraction > 0.25:
        return "#FF9800"   # orange
    return "#F44336"       # red


# ── PokemonPanel ─────────────────────────────────────────────────────────────

class PokemonPanel(QFrame):
    """Displays one Pokémon's name, level, HP bar, type(s), ability, and status."""

    def __init__(self, title: str = "포켓몬", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setMinimumWidth(200)
        self._build_ui(title)

    def _build_ui(self, title: str) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        # Header (side label)
        hdr = QLabel(title)
        hdr.setObjectName("section_title")
        lay.addWidget(hdr)

        # Pokémon name + level
        row = QHBoxLayout()
        self._name_lbl = QLabel("—")
        self._name_lbl.setObjectName("pokemon_name")
        row.addWidget(self._name_lbl)
        row.addStretch()
        self._level_lbl = QLabel("Lv.—")
        self._level_lbl.setStyleSheet("color: #A0A0B0; font-size: 11px;")
        row.addWidget(self._level_lbl)
        lay.addLayout(row)

        # Type tags
        self._type_lbl = QLabel("")
        self._type_lbl.setStyleSheet("font-size: 11px; color: #A0A0B0;")
        lay.addWidget(self._type_lbl)

        # HP bar
        hp_row = QHBoxLayout()
        self._hp_lbl = QLabel("HP: —/—")
        self._hp_lbl.setObjectName("hp_label")
        hp_row.addWidget(self._hp_lbl)
        lay.addLayout(hp_row)

        self._hp_bar = QProgressBar()
        self._hp_bar.setRange(0, 100)
        self._hp_bar.setValue(100)
        self._hp_bar.setTextVisible(False)
        self._hp_bar.setMaximumHeight(14)
        lay.addWidget(self._hp_bar)

        # Ability + Status
        ability_row = QHBoxLayout()
        self._ability_lbl = QLabel("")
        self._ability_lbl.setStyleSheet("font-size: 10px; color: #A0A0B0;")
        ability_row.addWidget(self._ability_lbl)
        ability_row.addStretch()
        self._status_lbl = QLabel("")
        self._status_lbl.setObjectName("status_badge")
        self._status_lbl.hide()
        ability_row.addWidget(self._status_lbl)
        lay.addLayout(ability_row)

        # Rank stages (compact)
        self._rank_lbl = QLabel("")
        self._rank_lbl.setStyleSheet("font-size: 10px; color: #A0A0B0;")
        self._rank_lbl.setWordWrap(True)
        lay.addWidget(self._rank_lbl)

        lay.addStretch()

    # ── Refresh ──────────────────────────────────────────────────────────────

    def refresh(self, ps: BattlePokemonState | None) -> None:
        if ps is None:
            self._name_lbl.setText("—")
            self._level_lbl.setText("Lv.—")
            self._type_lbl.setText("")
            self._hp_lbl.setText("HP: —/—")
            self._hp_bar.setValue(0)
            self._ability_lbl.setText("")
            self._status_lbl.hide()
            self._rank_lbl.setText("")
            return

        if ps.is_fainted:
            # Show fainted icon in the label instead of emoji
            self._name_lbl.setText(ps.name)
            self._name_lbl.setStyleSheet("color: #555; font-size: 14px; font-weight: bold; text-decoration: line-through;")
        else:
            self._name_lbl.setText(ps.name)
            self._name_lbl.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: bold;")
        self._level_lbl.setText(f"Lv.{ps.level}")

        types = ps.type1
        if ps.type2:
            types += f"/{ps.type2}"
        self._type_lbl.setText(types)

        self._hp_lbl.setText(f"HP: {ps.current_hp}/{ps.max_hp}")
        pct = int(ps.hp_fraction * 100)
        self._hp_bar.setValue(pct)
        colour = _hp_colour(ps.hp_fraction)
        self._hp_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: {colour}; border-radius: 3px; }}"
        )

        self._ability_lbl.setText(ps.ability_name or "")

        status_text = ps.status.major_status or ("혼란" if ps.status.is_confused else "")
        if status_text:
            self._status_lbl.setText(status_text)
            self._status_lbl.show()
        else:
            self._status_lbl.hide()

        # Non-zero rank stages
        rs = ps.rank_stages
        parts = []
        for stat, val in [
            ("공격", rs.attack), ("방어", rs.defense),
            ("특공", rs.sp_atk), ("특방", rs.sp_def),
            ("속도", rs.speed), ("명중", rs.accuracy), ("회피", rs.evasion),
        ]:
            if val != 0:
                sign = "+" if val > 0 else ""
                parts.append(f"{stat}{sign}{val}")
        self._rank_lbl.setText("  ".join(parts) if parts else "")


# ── PartyOverviewPanel ────────────────────────────────────────────────────────

class PartyOverviewPanel(QWidget):
    """Shows the 6 party slots as small HP indicators."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bars: list[QProgressBar] = []
        self._names: list[QLabel] = []
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(3)
        for _ in range(8):   # up to 8 members (P-02)
            row = QHBoxLayout()
            nm = QLabel("—")
            nm.setFixedWidth(80)
            nm.setStyleSheet("font-size: 10px; color: #A0A0B0;")
            nm.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setMaximumHeight(8)
            row.addWidget(nm)
            row.addWidget(bar)
            lay.addLayout(row)
            self._bars.append(bar)
            self._names.append(nm)

    def refresh(self, side: BattleSideState) -> None:
        for i, (nm, bar) in enumerate(zip(self._names, self._bars)):
            if i < len(side.pokemon_states):
                ps = side.pokemon_states[i]
                nm.setText(ps.name[:8])
                pct = int(ps.hp_fraction * 100)
                bar.setValue(pct)
                colour = _hp_colour(ps.hp_fraction)
                bar.setStyleSheet(f"QProgressBar::chunk {{ background: {colour}; border-radius: 2px; }}")
                nm.setStyleSheet(
                    "font-size: 10px; color: #555;" if ps.is_fainted else "font-size: 10px; color: #A0A0B0;"
                )
            else:
                nm.setText("—")
                bar.setValue(0)


# ── FieldStateBar ─────────────────────────────────────────────────────────────

class FieldStateBar(QWidget):
    """Compact bar showing all active field conditions (FE-01 through FE-06)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(6)
        self._layout.addStretch()

    def _clear(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _make_tag(self, text: str, icon, obj_name: str) -> QWidget:
        """Build a compact tag widget: small SVG icon + text label."""
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(4, 2, 6, 2)
        row.setSpacing(4)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon.pixmap(SMALL))
        row.addWidget(icon_lbl)
        txt_lbl = QLabel(text)
        txt_lbl.setObjectName(obj_name)
        row.addWidget(txt_lbl)
        w.setObjectName(obj_name + "_wrap")
        return w

    def refresh(self, fs: FieldStateManager) -> None:
        self._clear()
        tags: list[tuple[str, object, str]] = []   # (text, icon, object_name)

        if fs.weather != Weather.NONE.value:
            turns = f"({fs.weather_turns}T)" if fs.weather_turns > 0 else ""
            tags.append((f"{fs.weather}{turns}", Icons.WEATHER, "weather_tag"))

        if fs.terrain != Terrain.NONE.value:
            turns = f"({fs.terrain_turns}T)" if fs.terrain_turns > 0 else ""
            tags.append((f"{fs.terrain}{turns}", Icons.TERRAIN, "field_tag"))

        for name, turns in fs.global_effects.items():
            tags.append((f"{name}({turns}T)", Icons.GLOBAL_EFFECT, "field_tag"))

        for name, turns in fs.side1.barriers.items():
            tags.append((f"[1] {name}({turns}T)", Icons.BARRIER, "field_tag"))
        for name, turns in fs.side2.barriers.items():
            tags.append((f"[2] {name}({turns}T)", Icons.BARRIER, "field_tag"))

        if fs.special_field != SpecialField.NONE.value:
            tags.append((fs.special_field, Icons.SPECIAL_FIELD, "field_tag"))

        if not tags:
            no_tag = QLabel("필드: 이상 없음")
            no_tag.setObjectName("field_tag")
            self._layout.addWidget(no_tag)
        else:
            for text, icon, obj_name in tags:
                self._layout.addWidget(self._make_tag(text, icon, obj_name))
        self._layout.addStretch()


# ── CommandPanel ─────────────────────────────────────────────────────────────

class CommandPanel(QWidget):
    """Move buttons + Switch / Flee buttons.

    Emits:
        move_selected(str move_id)
        switch_requested()
    """

    move_selected = Signal(str)
    switch_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._move_data: dict = {}
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # Move grid (up to 8 moves in 2 rows × 4 cols)
        self._move_grid = QGridLayout()
        self._move_grid.setSpacing(6)
        self._move_btns: list[QPushButton] = []
        for i in range(8):
            btn = QPushButton(f"기술 {i+1}")
            btn.setObjectName("move_btn")
            btn.setEnabled(False)
            btn.clicked.connect(lambda _, idx=i: self._on_move_clicked(idx))
            self._move_grid.addWidget(btn, i // 4, i % 4)
            self._move_btns.append(btn)
        outer.addLayout(self._move_grid)

        # Switch / Flee row
        action_row = QHBoxLayout()
        self._switch_btn = QPushButton("포켓몬 교대")
        self._switch_btn.setObjectName("toolbar_btn")
        self._switch_btn.setIcon(Icons.SWITCH)
        self._switch_btn.setIconSize(SMALL)
        self._switch_btn.clicked.connect(self.switch_requested)
        action_row.addWidget(self._switch_btn)
        action_row.addStretch()
        outer.addLayout(action_row)

    # ── Refresh ──────────────────────────────────────────────────────────────

    def refresh(self, move_ids: list[str], move_data: dict) -> None:
        """Populate move buttons from a list of move IDs."""
        self._move_data = move_data
        for i, btn in enumerate(self._move_btns):
            if i < len(move_ids):
                mid = move_ids[i]
                mv = move_data.get(mid)
                if mv:
                    power_str = f" ({mv.power})" if mv.power else ""
                    btn.setText(f"{mv.name}\n{mv.type}{power_str}")
                    btn.setProperty("move_id", mid)
                else:
                    btn.setText(f"기술 {i+1}")
                    btn.setProperty("move_id", mid)
                btn.setEnabled(True)
            else:
                btn.setText(f"기술 {i+1}")
                btn.setEnabled(False)
                btn.setProperty("move_id", None)

    def set_enabled(self, enabled: bool) -> None:
        for btn in self._move_btns:
            btn.setEnabled(enabled and bool(btn.property("move_id")))
        self._switch_btn.setEnabled(enabled)

    def _on_move_clicked(self, idx: int) -> None:
        mid = self._move_btns[idx].property("move_id")
        if mid:
            self.move_selected.emit(mid)


# ── BattleLogPanel ────────────────────────────────────────────────────────────

class BattleLogPanel(QWidget):
    """Dual-tab battle log panel (Q5).

    Tab 0 — 텍스트 로그 (기본): Chat-style scrolling text log.
    Tab 1 — 이벤트 타임라인: Card-style event list from BattleEventHistory.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._tabs = QTabWidget()
        lay.addWidget(self._tabs)

        # ── Tab 0: 텍스트 로그 (primary) ────────────────────────────────────
        log_widget = QWidget()
        log_lay = QVBoxLayout(log_widget)
        log_lay.setContentsMargins(4, 4, 4, 4)
        log_lay.setSpacing(4)
        self._log = QTextEdit()
        self._log.setObjectName("battle_log")
        self._log.setReadOnly(True)
        log_lay.addWidget(self._log)
        self._tabs.addTab(log_widget, "텍스트 로그")

        # ── Tab 1: 이벤트 타임라인 (secondary) ──────────────────────────────
        timeline_widget = QWidget()
        timeline_lay = QVBoxLayout(timeline_widget)
        timeline_lay.setContentsMargins(4, 4, 4, 4)
        timeline_lay.setSpacing(4)
        self._timeline = QTextEdit()
        self._timeline.setObjectName("battle_log")
        self._timeline.setReadOnly(True)
        timeline_lay.addWidget(self._timeline)
        self._tabs.addTab(timeline_widget, "이벤트 타임라인")

        # Always open on the text log tab
        self._tabs.setCurrentIndex(0)

    # ── Public API ────────────────────────────────────────────────────────────

    def append(self, text: str) -> None:
        """Append a text line to the text log tab."""
        self._log.append(text)
        self._log.ensureCursorVisible()

    def set_log(self, entries: list[str]) -> None:
        """Replace the entire text log."""
        self._log.clear()
        for entry in entries:
            self._log.append(entry)
        self._log.ensureCursorVisible()

    def clear(self) -> None:
        self._log.clear()
        self._timeline.clear()

    def set_event_log(self, events: list) -> None:
        """Populate the event timeline tab from a list of BattleEvent objects."""
        from tunaed_pokemon.engine.events import BattleEventType
        self._timeline.clear()
        for i, evt in enumerate(events):
            icon_map = {
                BattleEventType.MOVE_USED:      "[기술]",
                BattleEventType.DAMAGE_DEALT:   "[데미지]",
                BattleEventType.STATUS_APPLIED: "[상태이상]",
                BattleEventType.STATUS_REMOVED: "[상태회복]",
                BattleEventType.POKEMON_FAINTED:"[쓰러짐]",
                BattleEventType.POKEMON_SWITCHED:"[교대]",
                BattleEventType.TURN_START:     "[턴 시작]",
                BattleEventType.TURN_END:       "[턴 종료]",
                BattleEventType.FIELD_CHANGED:  "[필드 변화]",
                BattleEventType.RANK_CHANGED:   "[랭크 변화]",
                BattleEventType.HP_CHANGED:     "[HP 변화]",
                BattleEventType.BATTLE_END:     "[배틀 종료]",
                BattleEventType.MESSAGE:        "[메시지]",
            }
            tag = icon_map.get(evt.event_type, "[?]")
            side_str = f" [P{evt.side}]" if evt.side else ""
            line = f"#{i+1:03d} {tag}{side_str} {evt.message}"
            self._timeline.append(line)
        self._timeline.ensureCursorVisible()


