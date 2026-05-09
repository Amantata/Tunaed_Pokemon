"""Launcher / home screen — the application entry point.

From this screen the user chooses ONE of two independent paths:
  • 전투 시작  → BattleSetupDialog → BattleWindow
  • 파티/도감 편집 → EditorWindow

These paths are SEPARATE.  The BattleWindow has no route back to the editor,
and the EditorWindow has no route to a battle.  The launcher hides itself
while either window is open and reappears when it is closed.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from tunaed_pokemon import __version__
from tunaed_pokemon.ui.styles import TEXT_DIM
from tunaed_pokemon.ui.icon_manager import Icons, LAUNCHER


class LauncherWindow(QMainWindow):
    """Home screen.  Opens the battle or editor window; never both at once."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("어장식 포켓몬 배틀 시뮬레이터")
        self.setMinimumSize(640, 440)
        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setSpacing(0)
        outer.setContentsMargins(48, 48, 48, 48)

        # Title
        title = QLabel("어장식 포켓몬\n배틀 시뮬레이터")
        title.setObjectName("app_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        outer.addSpacing(8)

        subtitle = QLabel("오레마스 시스템 기반 배틀 시뮬레이터")
        subtitle.setObjectName("app_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(subtitle)

        outer.addSpacing(48)

        # Two main buttons — horizontally centred
        btn_row = QHBoxLayout()
        btn_row.setSpacing(32)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._btn_battle = QPushButton("전투 시작")
        self._btn_battle.setObjectName("primary")
        self._btn_battle.setToolTip("배틀 화면을 엽니다")
        self._btn_battle.setIcon(Icons.BATTLE)
        self._btn_battle.setIconSize(LAUNCHER)
        self._btn_battle.clicked.connect(self._open_battle)

        self._btn_editor = QPushButton("파티/도감 편집")
        self._btn_editor.setObjectName("secondary")
        self._btn_editor.setToolTip("파티·포켓몬·트레이너 데이터를 편집합니다")
        self._btn_editor.setIcon(Icons.EDITOR)
        self._btn_editor.setIconSize(LAUNCHER)
        self._btn_editor.clicked.connect(self._open_editor)

        btn_row.addWidget(self._btn_battle)
        btn_row.addWidget(self._btn_editor)
        outer.addLayout(btn_row)

        outer.addSpacing(48)

        # Version footer
        ver = QLabel(f"v{__version__}")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        outer.addWidget(ver)

    # ── Actions ──────────────────────────────────────────────────────────────

    def _open_battle(self) -> None:
        """Open the battle setup dialog, then (if confirmed) the battle window."""
        # Import here to avoid circular refs and to keep the two paths independent
        from tunaed_pokemon.ui.battle.battle_setup import BattleSetupDialog
        from tunaed_pokemon.ui.battle.battle_window import BattleWindow

        dlg = BattleSetupDialog(self)
        if dlg.exec() != BattleSetupDialog.DialogCode.Accepted:
            return

        config = dlg.get_config()
        self.hide()

        win = BattleWindow(config)
        win.show()
        # Re-show launcher when the battle window is closed
        win.destroyed.connect(self._on_child_closed)

    def _open_editor(self) -> None:
        """Open the party/Pokédex editor window."""
        from tunaed_pokemon.ui.editor.editor_window import EditorWindow

        self.hide()
        win = EditorWindow()
        win.show()
        win.destroyed.connect(self._on_child_closed)

    def _on_child_closed(self) -> None:
        """Called when the battle or editor window is closed."""
        self.show()
        self.activateWindow()
