"""Battle window — the primary gameplay screen (F-01, B-01–B-04).

This window has NO navigation to the party/encyclopedia editor.
The battle and the editor are completely separate application paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from tunaed_pokemon.engine.battle_state import (
    BattleEventHistory,
    BattleSideState,
    BattleStateSnapshot,
    TurnHistory,
)
from tunaed_pokemon.engine.events import EventBus, BattleEvent, BattleEventType
from tunaed_pokemon.engine.action_order import ActionEntry
from tunaed_pokemon.engine.turn_pipeline import TurnPipeline
from tunaed_pokemon.utils.persistence import (
    load_moves,
)
from tunaed_pokemon.ui.battle.widgets import (
    BattleLogPanel,
    CommandPanel,
    FieldStateBar,
    PartyOverviewPanel,
    PokemonPanel,
)
from tunaed_pokemon.ui.icon_manager import Icons, MEDIUM


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
        # B-01: TurnHistory records turn-START snapshots only (for save/load).
        self._turn_history = TurnHistory()
        # B-02: BattleEventHistory tracks per-event state for Undo/Redo.
        self._event_history = BattleEventHistory()
        self._bus = EventBus()
        self._pipeline = TurnPipeline(self._bus, self._event_history)
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

        # Screenshot-based layout: 3 columns × 2 rows
        row_split = QSplitter(Qt.Orientation.Vertical)
        main_lay.addWidget(row_split, stretch=1)

        top_split = QSplitter(Qt.Orientation.Horizontal)
        row_split.addWidget(top_split)
        top_split.addWidget(self._make_top_side_widget("내 편 (플레이어 1)", 1))
        top_split.addWidget(self._make_stage_top_widget())
        top_split.addWidget(self._make_top_side_widget("상대 (플레이어 2)", 2))

        bottom_split = QSplitter(Qt.Orientation.Horizontal)
        row_split.addWidget(bottom_split)
        bottom_split.addWidget(self._make_bottom_side_widget(1))
        bottom_split.addWidget(self._make_centre_bottom_widget())
        bottom_split.addWidget(self._make_bottom_side_widget(2))

        row_split.setSizes([240, 420])
        top_split.setSizes([280, 600, 280])
        bottom_split.setSizes([280, 600, 280])

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._turn_lbl = QLabel("턴 0")
        self._status_bar.addPermanentWidget(self._turn_lbl)

    def _make_top_side_widget(self, title: str, side_num: int) -> QWidget:
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        hdr = QLabel(title)
        hdr.setObjectName("section_title")
        lay.addWidget(hdr)

        info_row = QHBoxLayout()
        image = QFrame()
        image.setObjectName("panel")
        image.setFixedSize(110, 110)
        image_lbl = QLabel("이미지", image)
        image_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_lbl.setGeometry(0, 0, 110, 110)
        info_row.addWidget(image)

        panel = PokemonPanel("포켓몬 데이터")
        info_row.addWidget(panel, stretch=1)
        lay.addLayout(info_row)

        for colour in ("#8b0016", "#8b0016", "#FFE66D"):
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet(f"border: 2px solid {colour};")
            lay.addWidget(line)
        lay.addStretch()

        if side_num == 1:
            self._active1_panel = panel
        else:
            self._active2_panel = panel

        return widget

    def _make_stage_top_widget(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        self._field_bar = FieldStateBar()
        lay.addWidget(self._field_bar)

        bg_lbl = QLabel("배경 이미지 (날씨, 필드 등)")
        bg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_lbl.setStyleSheet("font-size: 16px; color: #A0A0B0;")
        lay.addWidget(bg_lbl)

        battle_data_lbl = QLabel("배틀 데이터")
        battle_data_lbl.setStyleSheet("font-size: 18px; color: #E0E0E0;")
        lay.addWidget(battle_data_lbl)
        lay.addStretch()

        self._fmt_lbl = QLabel("")
        self._fmt_lbl.setStyleSheet("color: #A0A0B0; font-size: 12px;")
        lay.addWidget(self._fmt_lbl, alignment=Qt.AlignmentFlag.AlignLeft)

        self._next_turn_btn = QPushButton("다음 턴")
        self._next_turn_btn.setObjectName("primary")
        self._next_turn_btn.setIcon(Icons.NEXT_TURN)
        self._next_turn_btn.setIconSize(MEDIUM)
        self._next_turn_btn.setStyleSheet(
            "font-size: 14px; padding: 10px 20px; min-width: 120px;"
        )
        self._next_turn_btn.clicked.connect(self._advance_turn)
        lay.addWidget(self._next_turn_btn, alignment=Qt.AlignmentFlag.AlignRight)

        return w

    def _make_bottom_side_widget(self, side_num: int) -> QWidget:
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(8)

        party = PartyOverviewPanel()
        lay.addWidget(party)
        if side_num == 1:
            self._party1_panel = party
        else:
            self._party2_panel = party

        cmd = CommandPanel()
        lay.addWidget(cmd)
        if side_num == 1:
            self._cmd_panel = cmd
            self._cmd_panel.move_selected.connect(self._on_move_selected)
            self._cmd_panel.switch_requested.connect(self._on_switch_requested)
        else:
            self._opponent_cmd_panel = cmd
            cmd.set_enabled(False)

        extra = QLineEdit()
        extra.setPlaceholderText("추가입력장")
        extra.setReadOnly(side_num == 2)
        lay.addWidget(extra)
        lay.addStretch()

        return widget

    def _make_centre_bottom_widget(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        fx_lbl = QLabel("연출 등")
        fx_lbl.setObjectName("section_title")
        lay.addWidget(fx_lbl)

        self._log_panel = BattleLogPanel()
        lay.addWidget(self._log_panel, stretch=1)

        log_lbl = QLabel("로그")
        log_lbl.setStyleSheet("color: #A0A0B0;")
        lay.addWidget(log_lbl, alignment=Qt.AlignmentFlag.AlignLeft)

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
        if active2:
            self._opponent_cmd_panel.refresh(active2[0].move_ids, self._moves)
        else:
            self._opponent_cmd_panel.refresh([], self._moves)
        self._opponent_cmd_panel.set_enabled(False)

        # Format label
        self._fmt_lbl.setText(f"[{s.battle_format}]")

        # Turn counter
        self._turn_lbl.setText(f"턴 {s.turn_number}")

        self._undo_btn.setEnabled(self._event_history.can_undo())
        self._redo_btn.setEnabled(self._event_history.can_redo())
        self._next_turn_btn.setEnabled(not s.battle_over)

        # Log — text log from state, event timeline from event history
        self._log_panel.set_log(s.log)
        self._log_panel.set_event_log(self._event_history.event_log())

        if s.battle_over:
            self._cmd_panel.set_enabled(False)
            self._announce_battle_result()

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_message(self, event: BattleEvent) -> None:
        # Messages are already added to s.log by TurnPipeline; just refresh panel
        self._log_panel.append(event.message)

    def _build_ai_action(self, side: int) -> list[ActionEntry]:
        """Build a simple AI action for the given side (uses first available move,
        or switches to the next non-fainted Pokémon if active is fainted)."""
        side_state = self._state.side1 if side == 1 else self._state.side2
        actives = side_state.active_pokemon
        if not actives:
            return []
        active = actives[0]

        # If fainted, perform an auto-switch to the first available Pokémon
        if active.is_fainted:
            next_idx = self._find_next_available(side_state)
            if next_idx is not None:
                return [ActionEntry(side=side, pokemon=active,
                                    action_type="switch", switch_target=next_idx)]
            return []

        # Use first available move
        for mid in active.move_ids:
            mv = self._moves.get(mid)
            if mv:
                return [ActionEntry(side=side, pokemon=active,
                                    action_type="move", move=mv)]
        return []

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

        # B-01: snapshot at turn START (before processing)
        self._turn_history.push(self._state)

        action = ActionEntry(side=1, pokemon=attacker, action_type="move", move=mv)
        new_state = self._pipeline.process_turn(
            self._state, [action] + self._build_ai_action(2), self._moves
        )
        self._state = new_state
        self._handle_post_faint_switch()
        self._refresh_all()

    def _on_switch_requested(self) -> None:
        """Handle voluntary switch: player chooses a party member to send out."""
        if self._state.battle_over:
            return
        idx = self._pick_switch_target(self._state.side1, forced=False)
        if idx is None:
            return

        # B-01: snapshot at turn START
        self._turn_history.push(self._state)

        active1 = self._state.side1.active_pokemon
        attacker = active1[0] if active1 else None

        actions: list[ActionEntry] = []
        if attacker:
            switch_action = ActionEntry(
                side=1,
                pokemon=attacker,
                action_type="switch",
                switch_target=idx,
            )
            actions.append(switch_action)

        # AI also acts this turn
        actions += self._build_ai_action(2)

        new_state = self._pipeline.process_turn(self._state, actions, self._moves)
        self._state = new_state
        self._handle_post_faint_switch()
        self._refresh_all()

    # ── Turn processing ───────────────────────────────────────────────────────

    def _advance_turn(self) -> None:
        """Advance to the next turn with no move actions (manual turn increment)."""
        if self._state.battle_over:
            return
        # B-01: snapshot at turn START
        self._turn_history.push(self._state)
        new_state = self._pipeline.process_turn(self._state, [], self._moves)
        self._state = new_state
        self._handle_post_faint_switch()
        self._refresh_all()

    # ── Switch helpers ────────────────────────────────────────────────────────

    def _pick_switch_target(
        self, side_state: BattleSideState, *, forced: bool
    ) -> int | None:
        """Show a dialog for the player to choose a Pokémon to switch to.

        Returns the index into side_state.pokemon_states, or None if cancelled.
        ``forced=True`` means the dialog cannot be dismissed without selecting.
        """
        candidates: list[tuple[int, str]] = []
        for i, ps in enumerate(side_state.pokemon_states):
            if not ps.is_fainted and i not in side_state.active_indices:
                candidates.append((i, f"{ps.name}  HP {ps.current_hp}/{ps.max_hp}"))
        if not candidates:
            return None

        dlg = _SwitchSelectDialog(candidates, forced=forced, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.selected_index()
        return None

    def _do_switch_in(
        self, side_state: BattleSideState, idx: int
    ) -> None:
        """Apply a post-faint switch-in: update active index and log the entry."""
        side_state.active_indices = [idx]
        name = side_state.pokemon_states[idx].name
        msg = f"{name}(이)가 출전!"
        self._state.add_log(msg)
        self._bus.emit_message(msg)

    def _handle_post_faint_switch(self) -> None:
        """After a turn, handle forced switches for fainted active Pokémon.

        - Player side (1): show switch dialog (forced — cannot skip).
        - AI side (2):     auto-switch to the first available Pokémon.
        """
        if self._state.battle_over:
            return

        # AI side: auto-switch fainted active Pokémon
        side2 = self._state.side2
        actives2 = side2.active_pokemon
        if actives2 and actives2[0].is_fainted:
            next_idx = self._find_next_available(side2)
            if next_idx is not None:
                self._do_switch_in(side2, next_idx)

        # Player side: prompt for switch
        side1 = self._state.side1
        actives1 = side1.active_pokemon
        if actives1 and actives1[0].is_fainted and not self._state.battle_over:
            idx = self._pick_switch_target(side1, forced=True)
            if idx is not None:
                self._do_switch_in(side1, idx)

    @staticmethod
    def _find_next_available(side_state: BattleSideState) -> int | None:
        """Return the index of the first non-fainted, non-active Pokémon, or None."""
        for i, ps in enumerate(side_state.pokemon_states):
            if not ps.is_fainted and i not in side_state.active_indices:
                return i
        return None


    # ── Save / Load (B-01) ────────────────────────────────────────────────────

    def _save_state(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "배틀 상태 저장", "battle_save.json", "JSON (*.json)"
        )
        if path:
            data = json.dumps(self._state.to_dict(), ensure_ascii=False, separators=(",", ":"))
            Path(path).write_text(data, encoding="utf-8")
            self._status_bar.showMessage(f"저장 완료: {path}", 3000)

    def _load_state(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "배틀 상태 불러오기", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self._state = BattleStateSnapshot.from_dict(data)
            self._reset_result_announcement_flag()
            self._event_history.clear()
            self._refresh_all()
            self._status_bar.showMessage(f"불러오기 완료: {path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"불러오기 실패:\n{e}")

    # ── Undo / Redo (B-02: per-event) ─────────────────────────────────────────

    def _undo(self) -> None:
        snap = self._event_history.undo()
        if snap:
            self._state = snap
            self._refresh_all()
            self._status_bar.showMessage("되돌리기 (이벤트 단위)", 2000)

    def _redo(self) -> None:
        snap = self._event_history.redo()
        if snap:
            self._state = snap
            self._refresh_all()
            self._status_bar.showMessage("다시실행 (이벤트 단위)", 2000)

    # ── Battle Editor (B-04) ─────────────────────────────────────────────────

    def _open_battle_editor(self) -> None:
        from tunaed_pokemon.ui.battle.battle_editor import BattleEditorDialog
        dlg = BattleEditorDialog(self._state, self)
        if dlg.exec() == BattleEditorDialog.DialogCode.Accepted:
            self._state = dlg.get_state()
            self._reset_result_announcement_flag()
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


# ── Switch selection dialog ───────────────────────────────────────────────────

class _SwitchSelectDialog(QDialog):
    """Modal dialog for selecting a Pokémon to switch in.

    Parameters
    ----------
    candidates:
        List of (party_index, display_text) tuples for switchable Pokémon.
    forced:
        If True the Cancel button is hidden (post-faint forced switch).
    """

    def __init__(
        self,
        candidates: list[tuple[int, str]],
        *,
        forced: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._candidates = candidates
        self.setWindowTitle("포켓몬 선택")
        self.setMinimumWidth(300)

        lay = QVBoxLayout(self)
        hint = "교대할 포켓몬을 선택하세요." if not forced else "다음 포켓몬을 선택하세요. (필수)"
        lay.addWidget(QLabel(hint))

        self._list = QListWidget()
        for _, text in candidates:
            self._list.addItem(QListWidgetItem(text))
        if candidates:
            self._list.setCurrentRow(0)
        self._list.itemDoubleClicked.connect(self.accept)
        lay.addWidget(self._list)

        btn_flags = QDialogButtonBox.StandardButton.Ok
        if not forced:
            btn_flags |= QDialogButtonBox.StandardButton.Cancel
        btns = QDialogButtonBox(btn_flags)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def selected_index(self) -> int | None:
        row = self._list.currentRow()
        if 0 <= row < len(self._candidates):
            return self._candidates[row][0]
        return None
