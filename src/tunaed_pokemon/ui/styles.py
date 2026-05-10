"""Application-wide Qt stylesheet and colour tokens (UI-02)."""

PRIMARY = "#34E5FF"
SECONDARY = "#FFE66D"
DARK_BG = "#1A1A2E"
PANEL_BG = "#16213E"
BORDER = "#0F3460"
TEXT_MAIN = "#E0E0E0"
TEXT_DIM = "#A0A0B0"
SUCCESS = "#4CAF50"
WARNING = "#FF9800"
DANGER = "#F44336"

GLOBAL_STYLESHEET = f"""
/* ── Base ─────────────────────────────────────────────────── */
QMainWindow, QDialog, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_MAIN};
    font-family: "Malgun Gothic", "맑은 고딕", "Noto Sans KR", sans-serif;
    font-size: 12px;
}}

/* ── Panels ───────────────────────────────────────────────── */
QFrame#panel {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
}}

/* ── Buttons ──────────────────────────────────────────────── */
QPushButton {{
    background-color: {BORDER};
    color: {TEXT_MAIN};
    border: 1px solid {PRIMARY};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover  {{ background-color: {PRIMARY}; color: {DARK_BG}; }}
QPushButton:pressed {{ background-color: #22b8cc; }}
QPushButton:disabled {{ background-color: #333; color: {TEXT_DIM}; border-color: #444; }}

QPushButton#primary {{
    background-color: {PRIMARY};
    color: {DARK_BG};
    font-size: 18px;
    font-weight: bold;
    padding: 18px 36px;
    border-radius: 12px;
    min-width: 180px;
}}
QPushButton#primary:hover  {{ background-color: #22d4ee; }}
QPushButton#primary:pressed {{ background-color: #1abbd0; }}

QPushButton#secondary {{
    background-color: {SECONDARY};
    color: {DARK_BG};
    font-size: 18px;
    font-weight: bold;
    padding: 18px 36px;
    border-radius: 12px;
    min-width: 180px;
}}
QPushButton#secondary:hover  {{ background-color: #f0d84a; }}
QPushButton#secondary:pressed {{ background-color: #dbc030; }}

QPushButton#move_btn {{
    background-color: #1e3a5f;
    border: 1px solid {PRIMARY};
    padding: 8px 6px;
    font-size: 11px;
    border-radius: 6px;
    min-height: 52px;
}}
QPushButton#move_btn:hover  {{ background-color: {PRIMARY}; color: {DARK_BG}; }}
QPushButton#move_btn:disabled {{ background-color: #222; color: {TEXT_DIM}; border-color: #333; }}

QPushButton#toolbar_btn {{
    background-color: transparent;
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
}}
QPushButton#toolbar_btn:hover  {{ background-color: {BORDER}; }}

/* ── Labels ───────────────────────────────────────────────── */
QLabel#app_title {{
    color: {PRIMARY};
    font-size: 32px;
    font-weight: bold;
}}
QLabel#app_subtitle {{
    color: {TEXT_DIM};
    font-size: 14px;
}}
QLabel#section_title {{
    color: {PRIMARY};
    font-size: 14px;
    font-weight: bold;
}}
QLabel#pokemon_name {{
    color: {TEXT_MAIN};
    font-size: 14px;
    font-weight: bold;
}}
QLabel#status_badge {{
    color: {DANGER};
    font-size: 10px;
    font-weight: bold;
    padding: 1px 4px;
    border: 1px solid {DANGER};
    border-radius: 3px;
}}
QLabel#field_tag {{
    background-color: #0F3460;
    color: {PRIMARY};
    border: 1px solid {PRIMARY};
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
}}
QLabel#weather_tag {{
    background-color: #1a2a4a;
    color: {SECONDARY};
    border: 1px solid {SECONDARY};
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
}}

/* ── HP Bar ───────────────────────────────────────────────── */
QProgressBar {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: #2a2a3e;
    max-height: 14px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {SUCCESS};
    border-radius: 3px;
}}

/* ── Lists & Tables ───────────────────────────────────────── */
QListWidget {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    outline: none;
}}
QListWidget::item {{ padding: 4px 8px; }}
QListWidget::item:selected {{ background-color: {PRIMARY}; color: {DARK_BG}; }}
QListWidget::item:hover    {{ background-color: #1e3a5f; }}

/* ── Tabs ─────────────────────────────────────────────────── */
QTabWidget::pane  {{ border: 1px solid {BORDER}; background: {PANEL_BG}; }}
QTabBar::tab      {{ background: {DARK_BG}; color: {TEXT_DIM}; padding: 8px 16px;
                     border: 1px solid {BORDER}; border-bottom: none; }}
QTabBar::tab:selected {{ background: {PANEL_BG}; color: {PRIMARY}; font-weight: bold; }}

/* ── Inputs ───────────────────────────────────────────────── */
QLineEdit, QTextEdit, QSpinBox, QComboBox, QPlainTextEdit {{
    background-color: #1e3a5f;
    border: 1px solid {BORDER};
    border-radius: 4px;
    color: {TEXT_MAIN};
    padding: 4px 8px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{
    border-color: {PRIMARY};
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background: {PANEL_BG}; color: {TEXT_MAIN};
    selection-background-color: {PRIMARY}; selection-color: {DARK_BG};
}}

/* ── Misc ─────────────────────────────────────────────────── */
QScrollArea  {{ background: transparent; border: none; }}
QSplitter::handle {{ background: {BORDER}; width: 4px; height: 4px; }}
QToolBar  {{ background: {PANEL_BG}; border: none; padding: 4px; spacing: 4px; }}
QStatusBar {{ background: {PANEL_BG}; color: {TEXT_DIM}; }}

QTextEdit#battle_log {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    color: {TEXT_MAIN};
    font-size: 11px;
    border-radius: 4px;
}}

QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    color: {TEXT_DIM};
    font-size: 11px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 8px; top: -6px; color: {PRIMARY}; }}
"""
