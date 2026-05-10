"""Battle state editor dialog — direct field editing during battle (B-04).

Allows the operator to correct HP, status conditions, rank stages, reinforcements,
PP, active Pokémon, and field effects without restarting the battle.
Opened ONLY from the BattleWindow toolbar; there is no path to this dialog from
the party/Pokédex editor.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from tunaed_pokemon.engine.battle_state import BattleStateSnapshot, BattlePokemonState
from tunaed_pokemon.models.enums import StatusCondition, Weather, Terrain, SpecialField


class _PokemonEditor(QWidget):
    """Edit HP, ability, status, rank stages, reinforcements, PP, and active flag."""

    def __init__(
        self,
        ps: BattlePokemonState,
        is_active: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._ps = ps
        self._is_active = is_active
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(8)

        # ── HP ────────────────────────────────────────────────────────────────
        hp_grp = QGroupBox("HP")
        hp_lay = QFormLayout(hp_grp)
        self._cur_hp = QSpinBox()
        self._cur_hp.setRange(0, self._ps.max_hp)
        self._cur_hp.setValue(self._ps.current_hp)
        self._max_hp = QSpinBox()
        self._max_hp.setRange(1, 9999)
        self._max_hp.setValue(self._ps.max_hp)
        hp_lay.addRow("현재 HP:", self._cur_hp)
        hp_lay.addRow("최대 HP:", self._max_hp)
        lay.addWidget(hp_grp)

        # ── Status condition ──────────────────────────────────────────────────
        st_grp = QGroupBox("상태이상")
        st_lay = QFormLayout(st_grp)
        self._status_combo = QComboBox()
        self._status_combo.addItem("없음", None)
        for sc in StatusCondition:
            if sc != StatusCondition.CONFUSION:
                self._status_combo.addItem(sc.value, sc.value)
        idx = self._status_combo.findData(self._ps.status.major_status)
        if idx >= 0:
            self._status_combo.setCurrentIndex(idx)
        st_lay.addRow("상태이상:", self._status_combo)
        lay.addWidget(st_grp)

        # ── Rank stages (상승/하락) ────────────────────────────────────────────
        rank_grp = QGroupBox("랭크 (상승/하락)")
        rank_lay = QFormLayout(rank_grp)
        self._rank_spins: dict[str, QSpinBox] = {}
        rs = self._ps.rank_stages
        for stat, label in [
            ("attack", "공격"), ("defense", "방어"),
            ("sp_atk", "특공"), ("sp_def", "특방"),
            ("speed", "속도"), ("accuracy", "명중"), ("evasion", "회피"),
        ]:
            spin = QSpinBox()
            spin.setRange(-6, 6)
            spin.setValue(getattr(rs, stat))
            self._rank_spins[stat] = spin
            rank_lay.addRow(f"{label}:", spin)
        lay.addWidget(rank_grp)

        # ── Reinforcements (강화 배율) ─────────────────────────────────────────
        reinf_grp = QGroupBox("강화 (배율) — ST-02")
        reinf_lay = QFormLayout(reinf_grp)
        self._reinf_spins: dict[str, QDoubleSpinBox] = {}
        rf = self._ps.reinforcements
        for stat, label in [
            ("attack", "공격"), ("defense", "방어"),
            ("sp_atk", "특공"), ("sp_def", "특방"), ("speed", "속도"),
        ]:
            spin = QDoubleSpinBox()
            spin.setRange(0.1, 10.0)
            spin.setSingleStep(0.1)
            spin.setDecimals(2)
            spin.setValue(getattr(rf, stat))
            self._reinf_spins[stat] = spin
            reinf_lay.addRow(f"{label} 배율:", spin)
        lay.addWidget(reinf_grp)

        # ── PP per move ───────────────────────────────────────────────────────
        pp_grp = QGroupBox("PP (남은 횟수)")
        pp_lay = QFormLayout(pp_grp)
        self._pp_spins: list[QSpinBox] = []
        for i, move_id in enumerate(self._ps.move_ids):
            current_pp = (
                self._ps.pp_remaining[i]
                if i < len(self._ps.pp_remaining) else 0
            )
            spin = QSpinBox()
            spin.setRange(0, 64)
            spin.setValue(current_pp)
            self._pp_spins.append(spin)
            label = move_id if move_id else f"기술{i+1}"
            pp_lay.addRow(f"{label}:", spin)
        if not self._ps.move_ids:
            pp_lay.addRow(QLabel("기술 없음"))
        lay.addWidget(pp_grp)

        # ── Active Pokémon flag ───────────────────────────────────────────────
        active_grp = QGroupBox("출전 상태")
        active_lay = QFormLayout(active_grp)
        self._active_chk = QCheckBox("현재 필드에 출전 중")
        self._active_chk.setChecked(self._is_active)
        active_lay.addRow(self._active_chk)
        lay.addWidget(active_grp)

        lay.addStretch()

    def apply_to(self, ps: BattlePokemonState) -> None:
        ps.current_hp = self._cur_hp.value()
        ps.max_hp = self._max_hp.value()
        ps.is_fainted = ps.current_hp == 0
        ps.status.major_status = self._status_combo.currentData()
        for stat, spin in self._rank_spins.items():
            setattr(ps.rank_stages, stat, spin.value())
        for stat, spin in self._reinf_spins.items():
            setattr(ps.reinforcements, stat, spin.value())
        # PP
        ps.pp_remaining = [spin.value() for spin in self._pp_spins]

    @property
    def is_active(self) -> bool:
        return self._active_chk.isChecked()


class BattleEditorDialog(QDialog):
    """Direct battle-state editor — separate screen (B-04)."""

    def __init__(self, state: BattleStateSnapshot, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("배틀 편집 모드 (B-04)")
        self.setMinimumSize(620, 700)
        # Work on a deep copy; only apply on accept
        self._state = state.deep_copy()
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(8)

        tabs = QTabWidget()
        lay.addWidget(tabs)

        # ── Pokémon tabs ──────────────────────────────────────────────────────
        self._pokemon_editors: list[tuple[BattlePokemonState, _PokemonEditor, int, int]] = []
        # tuple: (ps, editor, side_num, pokemon_index_in_side)

        for side_num, side in [(1, self._state.side1), (2, self._state.side2)]:
            for i, ps in enumerate(side.pokemon_states):
                is_active = i in side.active_indices
                editor = _PokemonEditor(ps, is_active)
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setWidget(editor)
                label = f"[{side_num}P] {ps.name}"
                tabs.addTab(scroll, label)
                self._pokemon_editors.append((ps, editor, side_num, i))

        # ── Field state tab ───────────────────────────────────────────────────
        field_widget = QWidget()
        field_lay = QFormLayout(field_widget)
        fs = self._state.field_state

        self._weather_combo = QComboBox()
        for w in Weather:
            self._weather_combo.addItem(w.value, w.value)
        self._weather_combo.setCurrentText(fs.weather)
        field_lay.addRow("날씨:", self._weather_combo)

        self._weather_turns = QSpinBox()
        self._weather_turns.setRange(0, 99)
        self._weather_turns.setValue(fs.weather_turns)
        field_lay.addRow("날씨 남은 턴:", self._weather_turns)

        self._terrain_combo = QComboBox()
        for t in Terrain:
            self._terrain_combo.addItem(t.value, t.value)
        self._terrain_combo.setCurrentText(fs.terrain)
        field_lay.addRow("「필드」 (FE-04):", self._terrain_combo)

        self._terrain_turns = QSpinBox()
        self._terrain_turns.setRange(0, 99)
        self._terrain_turns.setValue(fs.terrain_turns)
        field_lay.addRow("필드 남은 턴:", self._terrain_turns)

        self._sf_combo = QComboBox()
        for sf in SpecialField:
            self._sf_combo.addItem(sf.value, sf.value)
        self._sf_combo.setCurrentText(fs.special_field)
        field_lay.addRow("《필드》 (FE-06):", self._sf_combo)

        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setWidget(field_widget)
        tabs.addTab(scroll2, "필드 환경")

        # ── Buttons ───────────────────────────────────────────────────────────
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("적용")
        btns.accepted.connect(self._apply_and_accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _apply_and_accept(self) -> None:
        for ps, editor, side_num, idx in self._pokemon_editors:
            editor.apply_to(ps)
            # Update active_indices based on the checkbox
            side = self._state.side1 if side_num == 1 else self._state.side2
            if editor.is_active:
                if idx not in side.active_indices:
                    side.active_indices.append(idx)
            else:
                if idx in side.active_indices:
                    side.active_indices.remove(idx)

        fs = self._state.field_state
        fs.weather = self._weather_combo.currentData()
        fs.weather_turns = self._weather_turns.value()
        fs.terrain = self._terrain_combo.currentData()
        fs.terrain_turns = self._terrain_turns.value()
        fs.special_field = self._sf_combo.currentData()

        self.accept()

    def get_state(self) -> BattleStateSnapshot:
        return self._state

