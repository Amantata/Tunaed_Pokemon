"""Application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from tunaed_pokemon.ui.styles import GLOBAL_STYLESHEET
from tunaed_pokemon.ui.launcher import LauncherWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("어장식 포켓몬 배틀 시뮬레이터")
    app.setOrganizationName("TunaGround")
    app.setStyleSheet(GLOBAL_STYLESHEET)

    window = LauncherWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
