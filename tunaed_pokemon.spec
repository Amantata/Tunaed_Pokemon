# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec — Windows single-file executable (F-03)
#
# Build:
#   pip install pyinstaller pyinstaller-hooks-contrib
#   pyinstaller tunaed_pokemon.spec
#
# Output: dist/TunaedPokemon.exe

block_cipher = None

a = Analysis(
    ["src/tunaed_pokemon/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        # SVG icons — destination mirrors the package path so _MEIPASS lookup works
        ("src/tunaed_pokemon/ui/icons", "tunaed_pokemon/ui/icons"),
    ],
    hiddenimports=[
        # Qt SVG support (imported via QSvgRenderer in icon_manager.py)
        "PySide6.QtSvg",
        "PySide6.QtXml",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "_pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="TunaedPokemon",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # --windowed: no console window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # replace with path to icon file (e.g., "assets/app.ico") when added
)
