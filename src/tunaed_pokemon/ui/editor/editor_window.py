"""Editor window — party/encyclopedia editor.

This window is opened from the launcher and has NO route to the battle screen.
All icons use custom SVGs (no emoji).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from tunaed_pokemon.ui.editor.trainer_tab import TrainerTab
from tunaed_pokemon.ui.editor.pokemon_tab import PokemonTab
from tunaed_pokemon.ui.editor.party_tab import PartyTab
from tunaed_pokemon.ui.editor.master_list_tab import MoveListTab, AbilityListTab, PotentialListTab
from tunaed_pokemon.ui.icon_manager import Icons, SMALL


class EditorWindow(QMainWindow):
    """Party / Pokédex editor.

    Opened from the launcher only.  There is NO route from this window to the
    battle screen — the two application paths are completely separate.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("파티/도감 편집")
        self.setMinimumSize(900, 650)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        # Info bar at top clarifying this screen is separate from the battle
        info = QLabel("파티 / 도감 편집 모드 — 전투 화면과 독립된 편집 경로입니다.")
        info.setObjectName("app_subtitle")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(info)

        tabs = QTabWidget()
        lay.addWidget(tabs)

        # Tab: Trainer editor
        trainer_tab = TrainerTab()
        tabs.addTab(trainer_tab, "트레이너")
        tabs.setTabIcon(tabs.count() - 1, Icons.EDITOR)

        # Tab: Pokemon editor
        pokemon_tab = PokemonTab()
        tabs.addTab(pokemon_tab, "포켓몬")
        tabs.setTabIcon(tabs.count() - 1, Icons.BATTLE)

        # Tab: Party builder
        party_tab = PartyTab()
        tabs.addTab(party_tab, "파티")
        tabs.setTabIcon(tabs.count() - 1, Icons.SWITCH)

        # Tab: Move master list (SK-01)
        move_tab = MoveListTab()
        tabs.addTab(move_tab, "기술 목록")
        tabs.setTabIcon(tabs.count() - 1, Icons.NEXT_TURN)

        # Tab: Ability master list (SK-03)
        ability_tab = AbilityListTab()
        tabs.addTab(ability_tab, "특성 목록")
        tabs.setTabIcon(tabs.count() - 1, Icons.SPECIAL_FIELD)

        # Tab: Potential master list (PT-02)
        potential_tab = PotentialListTab()
        tabs.addTab(potential_tab, "포텐셜 목록")
        tabs.setTabIcon(tabs.count() - 1, Icons.TERRAIN)

        tabs.setIconSize(SMALL)

        # Status bar
        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("편집 내용은 자동으로 저장됩니다.")
