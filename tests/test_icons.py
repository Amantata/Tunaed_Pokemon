"""Tests for SVG icon files — verifies all icons exist and are valid SVG."""

from __future__ import annotations

from pathlib import Path

ICONS_DIR = Path(__file__).parent.parent / "src" / "tunaed_pokemon" / "ui" / "icons"

REQUIRED_ICONS = [
    "battle", "editor", "save", "load", "undo", "redo",
    "direct_edit", "next_turn", "add", "delete", "import", "export",
    "image_pick", "switch", "fainted",
    "weather", "terrain", "global_effect", "barrier", "special_field",
    "home",
]


def test_all_icon_files_exist():
    missing = [name for name in REQUIRED_ICONS if not (ICONS_DIR / f"{name}.svg").exists()]
    assert not missing, f"Missing icon files: {missing}"


def test_icon_files_are_valid_svg():
    for name in REQUIRED_ICONS:
        path = ICONS_DIR / f"{name}.svg"
        content = path.read_text(encoding="utf-8")
        assert "<svg" in content, f"{name}.svg does not contain <svg"
        assert "viewBox" in content, f"{name}.svg does not have viewBox"


def test_no_emoji_in_icon_files():
    """All SVG files must not contain emoji codepoints."""
    for name in REQUIRED_ICONS:
        path = ICONS_DIR / f"{name}.svg"
        content = path.read_text(encoding="utf-8")
        # Check for common emoji unicode ranges
        for char in content:
            cp = ord(char)
            is_emoji = (
                0x1F600 <= cp <= 0x1F64F or   # Emoticons
                0x1F300 <= cp <= 0x1F5FF or   # Misc Symbols and Pictographs
                0x1F680 <= cp <= 0x1F6FF or   # Transport and Map
                0x2600  <= cp <= 0x27BF or    # Misc symbols (some emoji-ish)
                0x1F900 <= cp <= 0x1F9FF       # Supplemental Symbols
            )
            assert not is_emoji, f"{name}.svg contains emoji character U+{cp:04X}"


def test_no_emoji_in_ui_python_files():
    """Python UI source files must not contain emoji codepoints."""
    ui_dir = Path(__file__).parent.parent / "src" / "tunaed_pokemon" / "ui"
    py_files = list(ui_dir.rglob("*.py"))
    assert py_files, "No .py files found in ui/"

    violations: list[str] = []
    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        for i, char in enumerate(content):
            cp = ord(char)
            is_emoji = (
                0x1F600 <= cp <= 0x1F64F or
                0x1F300 <= cp <= 0x1F5FF or
                0x1F680 <= cp <= 0x1F6FF or
                0x1F900 <= cp <= 0x1F9FF
            )
            if is_emoji:
                violations.append(f"{py_file.name}:{i} U+{cp:04X} '{char}'")

    assert not violations, "Emoji found in UI files:\n" + "\n".join(violations)
