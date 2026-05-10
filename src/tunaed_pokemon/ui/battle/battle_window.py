"""Battle window — the primary gameplay screen (F-01, B-01–B-04).

This window has NO navigation to the party/encyclopedia editor.
The battle and the editor are completely separate application paths.
"""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from tunaed_pokemon.engine.battle_state import BattleStateSnapshot, TurnHistory
from tunaed_pokemon.engine.events import EventBus, BattleEvent, BattleEventType
from tunaed_pokemon.engine.action_order import ActionEntry
from tunaed_pokemon.engine.turn_pipeline import TurnPipeline
from tunaed_pokemon.models.enums import BattleFormat
from tunaed_pokemon.utils.persistence import (
    load_battle_state,
    save_battle_state,
    load_moves,
)
from tunaed_pokemon.ui.battle.widgets import (
    BattleLogPanel,
    CommandPanel,
    FieldStateBar,
    PartyOverviewPanel,
    PokemonPanel,
)
from tunaed_pokemon.ui.icon_manager import Icons, MEDIUM, SMALL


class BattleWindow(QMainWindow):
    """Main battle screen.

    Opened from the launcher via BattleSetupDialog.
    There is NO route from this window to the party/encyclopedia editor.
    """

    def __init__(self, config: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("전투 화면")
        self.setMinimumSize(1024, 700)

        self._state: BattleStateSnapshot = config["snapshot"]
        self._history = TurnHistory()
        self._history.push(self._state)
        self._bus = EventBus()
        self._pipeline = TurnPipeline(self._bus)
        self._moves = load_moves()
        self._result_announced = False

        self._build_ui()
        self._refresh_all()

        # Subscribe to events for the log
        self._bus.subscribe(BattleEventType.MESSAGE, self._on_message)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Toolbar ──
        tb = QToolBar("배틀 도구")
        tb.setMovable(False)
        self.addToolBar(tb)

        def _tb_btn(text: str, icon, tip: str, slot) -> QPushButton:
            btn = QPushButton(text)
            btn.setObjectName("toolbar_btn")
            btn.setToolTip(tip)
            btn.setIcon(icon)
            btn.setIconSize(MEDIUM)
            btn.clicked.connect(slot)
            return btn

        self._save_btn  = _tb_btn("저장",    Icons.SAVE,        "현재 배틀 상태 저장 (B-01)",       self._save_state)
        self._load_btn  = _tb_btn("불러오기", Icons.LOAD,        "저장된 배틀 상태 불러오기 (B-01)",  self._load_state)
        self._undo_btn  = _tb_btn("되돌리기", Icons.UNDO,        "이전 턴으로 되돌리기 (B-02)",       self._undo)
        self._redo_btn  = _tb_btn("다시실행", Icons.REDO,        "다음 턴으로 이동 (B-02)",           self._redo)
        self._edit_btn  = _tb_btn("배틀 편집", Icons.DIRECT_EDIT, "배틀 상태 직접 편집 (B-04)",       self._open_battle_editor)

        for btn in [self._save_btn, self._load_btn, self._undo_btn, self._redo_btn]:
            tb.addWidget(btn)
        tb.addSeparator()
        tb.addWidget(self._edit_btn)

        # ── Central widget ──
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setSpacing(6)
        main_lay.setContentsMargins(8, 8, 8, 8)

        # Field state bar (top)
        self._field_bar = FieldStateBar()
        main_lay.addWidget(self._field_bar)

        # Battle area (3-column splitter)
        battle_split = QSplitter(Qt.Orientation.Horizontal)
        main_lay.addWidget(battle_split, stretch=1)

        # Left — Side 1
        side1_widget = self._make_side_widget("내 편 (플레이어 1)", 1)
        self._side1_panel, self._party1_panel = side1_widget
        battle_split.addWidget(self._side1_panel)

        # Centre — turn info + VS label
        centre = self._make_centre_widget()
        battle_split.addWidget(centre)

        # Right — Side 2
        side2_widget = self._make_side_widget("상대 (플레이어 2)", 2)
        self._side2_panel, self._party2_panel = side2_widget
        battle_split.addWidget(side2_widget[0])

        # Log + command panel (bottom splitter)
        bottom_split = QSplitter(Qt.Orientation.Horizontal)
        main_lay.addWidget(bottom_split)

        self._log_panel = BattleLogPanel()
        bottom_split.addWidget(self._log_panel)

        self._cmd_panel = CommandPanel()
        self._cmd_panel.move_selected.connect(self._on_move_selected)
        self._cmd_panel.switch_requested.connect(self._on_switch_requested)
        bottom_split.addWidget(self._cmd_panel)

        bottom_split.setSizes([500, 400])
        battle_split.setSizes([280, 200, 280])

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._turn_lbl = QLabel("턴 0")
        self._status_bar.addPermanentWidget(self._turn_lbl)

    def _make_side_widget(self, title: str, side_num: int) -> tuple[QWidget, PartyOverviewPanel]:
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(6)

        hdr = QLabel(title)
        hdr.setObjectName("section_title")
        lay.addWidget(hdr)

        panel = PokemonPanel("활성 포켓몬")
        lay.addWidget(panel)

        party = PartyOverviewPanel()
        lay.addWidget(party)
        lay.addStretch()

        if side_num == 1:
            self._active1_panel = panel
        else:
            self._active2_panel = panel

        return widget, party

    def _make_centre_widget(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(8)

        vs_lbl = QLabel("VS")
        vs_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vs_lbl.setStyleSheet("font-size: 32px; font-weight: bold; color: #34E5FF;")
        lay.addWidget(vs_lbl)

        self._fmt_lbl = QLabel("")
        self._fmt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fmt_lbl.setStyleSheet("color: #A0A0B0; font-size: 12px;")
        lay.addWidget(self._fmt_lbl)

        self._next_turn_btn = QPushButton("다음 턴")
        self._next_turn_btn.setObjectName("primary")
        self._next_turn_btn.setIcon(Icons.NEXT_TURN)
        self._next_turn_btn.setIconSize(MEDIUM)
        self._next_turn_btn.setStyleSheet(
            "font-size: 14px; padding: 10px 20px; min-width: 120px;"
        )
        self._next_turn_btn.clicked.connect(self._advance_turn)
        lay.addWidget(self._next_turn_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return w

    # ── Refresh helpers ───────────────────────────────────────────────────────

    def _refresh_all(self) -> None:
        s = self._state

        # Active Pokémon panels
        active1 = s.side1.active_pokemon
        active2 = s.side2.active_pokemon
        self._active1_panel.refresh(active1[0] if active1 else None)
        self._active2_panel.refresh(active2[0] if active2 else None)

        # Party overviews
        self._party1_panel.refresh(s.side1)
        self._party2_panel.refresh(s.side2)

        # Field state bar
        self._field_bar.refresh(s.field_state)

        # Command panel (moves of the first active Pokémon on side 1)
        if active1:
            self._cmd_panel.refresh(active1[0].move_ids, self._moves)
            self._cmd_panel.set_enabled(not active1[0].is_fainted)
        else:
            self._cmd_panel.refresh([], self._moves)
            self._cmd_panel.set_enabled(False)

        # Format label
        self._fmt_lbl.setText(f"[{s.battle_format}]")

        # Turn counter
        self._turn_lbl.setText(f"턴 {s.turn_number}")

        self._undo_btn.setEnabled(self._history.can_undo())
        self._redo_btn.setEnabled(self._history.can_redo())
        self._next_turn_btn.setEnabled(not s.battle_over)

        # Log
        self._log_panel.set_log(s.log)

        if s.battle_over:
            self._cmd_panel.set_enabled(False)
            self._announce_battle_result()

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_message(self, event: BattleEvent) -> None:
        self._state.add_log(event.message)
        self._log_panel.append(event.message)

    def _on_move_selected(self, move_id: str) -> None:
        if self._state.battle_over:
            return
        mv = self._moves.get(move_id)
        actives1 = self._state.side1.active_pokemon
        if not actives1:
            return
        attacker = actives1[0]
        if attacker.is_fainted:
            return

        if mv is None:
            self._bus.emit_message(f"알 수 없는 기술: {move_id}")
            return

        # Build action for side 1 using the selected move
        action = ActionEntry(side=1, pokemon=attacker, action_type="move", move=mv)

        # Build a simple AI action for side 2 (first available move)
        actives2 = self._state.side2.active_pokemon
        opponent_actions: list[ActionEntry] = []
        if actives2:
            opp = actives2[0]
            if not opp.is_fainted and opp.move_ids:
                opp_mv = self._moves.get(opp.move_ids[0])
                if opp_mv:
                    opponent_actions.append(
                        ActionEntry(side=2, pokemon=opp, action_type="move", move=opp_mv)
                    )

        new_state = self._pipeline.process_turn(
            self._state, [action] + opponent_actions, self._moves
        )
        self._state = new_state
        self._history.push(self._state)
        self._refresh_all()

    def _on_switch_requested(self) -> None:
        if self._state.battle_over:
            return
        self._bus.emit_message("포켓몬 교대 요청 (구현 예정)")
        self._refresh_all()

    # ── Turn processing ───────────────────────────────────────────────────────

    def _advance_turn(self) -> None:
        """Advance to the next turn with no move actions (manual turn increment)."""
        if self._state.battle_over:
            return
        new_state = self._pipeline.process_turn(self._state, [], self._moves)
        self._state = new_state
        self._history.push(self._state)
        self._refresh_all()

    # ── Save / Load (B-01) ────────────────────────────────────────────────────

    def _save_state(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "배틀 상태 저장", "battle_save.json", "JSON (*.json)"
        )
        if path:
            save_battle_state(self._state.to_dict(), path.split("/")[-1])
            self._status_bar.showMessage(f"저장 완료: {path}", 3000)

    def _load_state(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "배틀 상태 불러오기", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            import json as _json
            data = _json.loads(open(path, encoding="utf-8").read())
            self._state = BattleStateSnapshot.from_dict(data)
            self._reset_result_announcement_flag()
            self._history.push(self._state)
            self._refresh_all()
            self._status_bar.showMessage(f"불러오기 완료: {path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"불러오기 실패:\n{e}")

    # ── Undo / Redo (B-02) ────────────────────────────────────────────────────

    def _undo(self) -> None:
        snap = self._history.undo()
        if snap:
            self._state = snap
            self._refresh_all()
            self._status_bar.showMessage("되돌리기", 2000)

    def _redo(self) -> None:
        snap = self._history.redo()
        if snap:
            self._state = snap
            self._refresh_all()
            self._status_bar.showMessage("다시실행", 2000)

    # ── Battle Editor (B-04) ─────────────────────────────────────────────────

    def _open_battle_editor(self) -> None:
        from tunaed_pokemon.ui.battle.battle_editor import BattleEditorDialog
        dlg = BattleEditorDialog(self._state, self)
        if dlg.exec() == BattleEditorDialog.DialogCode.Accepted:
            self._state = dlg.get_state()
            self._reset_result_announcement_flag()
            self._history.push(self._state)
            self._refresh_all()
            self._status_bar.showMessage("배틀 상태가 편집되었습니다.", 3000)

    def _reset_result_announcement_flag(self) -> None:
        self._result_announced = False

    def _battle_result_message(self, state: BattleStateSnapshot) -> str:
        """Build the final battle result text from the snapshot winner_side."""
        if state.winner_side == 1:
            winner_name = state.side1.trainer_name
        elif state.winner_side == 2:
            winner_name = state.side2.trainer_name
        else:
            return "배틀 종료! 무승부"
        return f"배틀 종료! 승자: {winner_name} (플레이어 {state.winner_side})"

    def _announce_battle_result(self) -> None:
        if self._result_announced:
            return
        self._result_announced = True
        message = self._battle_result_message(self._state)
        self._status_bar.showMessage(message, 5000)
