"""Icon manager — loads SVG icon files as QIcon objects.

All icons are custom-designed SVGs (no platform emoji).
Use these constants everywhere in the UI instead of emoji text.

Usage:
    from tunaed_pokemon.ui.icon_manager import Icons
    button.setIcon(Icons.BATTLE)
    button.setIconSize(QSize(28, 28))
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtSvg import QSvgRenderer       # noqa: F401 — ensures SVG plugin loaded
from PySide6.QtWidgets import QAbstractButton, QLabel

_ICONS_DIR = Path(__file__).parent / "icons"


def _icon(name: str) -> QIcon:
    path = _ICONS_DIR / f"{name}.svg"
    return QIcon(str(path))


# ── Icon constants ────────────────────────────────────────────────────────────

class Icons:
    """All UI icons as QIcon objects, loaded from custom SVG files."""

    BATTLE:        QIcon   # 전투 시작 — crossed swords
    EDITOR:        QIcon   # 파티/도감 편집 — pencil on book
    SAVE:          QIcon   # 저장 — floppy disk
    LOAD:          QIcon   # 불러오기 — open folder
    UNDO:          QIcon   # 되돌리기 — CCW arrow
    REDO:          QIcon   # 다시실행 — CW arrow
    DIRECT_EDIT:   QIcon   # 배틀 직접 편집 — wrench
    NEXT_TURN:     QIcon   # 다음 턴 — play triangle
    ADD:           QIcon   # 추가 — plus circle
    DELETE:        QIcon   # 삭제 — trash can
    IMPORT:        QIcon   # 가져오기 — arrow into box
    EXPORT:        QIcon   # 내보내기 — arrow from box
    IMAGE_PICK:    QIcon   # 이미지 선택 — picture frame
    SWITCH:        QIcon   # 포켓몬 교대 — swap arrows
    FAINTED:       QIcon   # 쓰러짐 — X circle
    WEATHER:       QIcon   # 날씨 — cloud + sun
    TERRAIN:       QIcon   # 「필드」 지형 — diamond
    GLOBAL_EFFECT: QIcon   # 전체 효과 — orbital rings
    BARRIER:       QIcon   # 장벽 — shield
    SPECIAL_FIELD: QIcon   # 《필드》 특수 경기장 — star burst
    HOME:          QIcon   # 홈 — house


def _load_all() -> None:
    for name in [
        "BATTLE", "battle",
        "EDITOR", "editor",
        "SAVE", "save",
        "LOAD", "load",
        "UNDO", "undo",
        "REDO", "redo",
        "DIRECT_EDIT", "direct_edit",
        "NEXT_TURN", "next_turn",
        "ADD", "add",
        "DELETE", "delete",
        "IMPORT", "import",
        "EXPORT", "export",
        "IMAGE_PICK", "image_pick",
        "SWITCH", "switch",
        "FAINTED", "fainted",
        "WEATHER", "weather",
        "TERRAIN", "terrain",
        "GLOBAL_EFFECT", "global_effect",
        "BARRIER", "barrier",
        "SPECIAL_FIELD", "special_field",
        "HOME", "home",
    ]:
        pass  # populated below

    Icons.BATTLE        = _icon("battle")
    Icons.EDITOR        = _icon("editor")
    Icons.SAVE          = _icon("save")
    Icons.LOAD          = _icon("load")
    Icons.UNDO          = _icon("undo")
    Icons.REDO          = _icon("redo")
    Icons.DIRECT_EDIT   = _icon("direct_edit")
    Icons.NEXT_TURN     = _icon("next_turn")
    Icons.ADD           = _icon("add")
    Icons.DELETE        = _icon("delete")
    Icons.IMPORT        = _icon("import")
    Icons.EXPORT        = _icon("export")
    Icons.IMAGE_PICK    = _icon("image_pick")
    Icons.SWITCH        = _icon("switch")
    Icons.FAINTED       = _icon("fainted")
    Icons.WEATHER       = _icon("weather")
    Icons.TERRAIN       = _icon("terrain")
    Icons.GLOBAL_EFFECT = _icon("global_effect")
    Icons.BARRIER       = _icon("barrier")
    Icons.SPECIAL_FIELD = _icon("special_field")
    Icons.HOME          = _icon("home")


# Eager-load on import so icons are immediately available
_load_all()


# ── Convenience helpers ───────────────────────────────────────────────────────

SMALL  = QSize(16, 16)
MEDIUM = QSize(24, 24)
LARGE  = QSize(36, 36)
LAUNCHER = QSize(48, 48)


def apply_icon(btn: QAbstractButton, icon: QIcon, size: QSize = MEDIUM) -> None:
    """Set an icon on a button at the given size."""
    btn.setIcon(icon)
    btn.setIconSize(size)
