"""Tests for data model construction and basic validation."""

from __future__ import annotations

import pytest

from tunaed_pokemon.models.enums import (
    Gender,
    PokemonType,
    PotentialCategory,
    QualityRank,
    StatType,
    StatusCondition,
    ALWAYS_PRESENT_POTENTIALS,
    VARIABLE_POTENTIALS,
    QUALITY_RANK_POINTS,
    stat_value_to_rank,
    quality_rank_difference,
)
from tunaed_pokemon.models.trainer import (
    Trainer,
    TrainerQualities,
    CommandPotential,
    InnatePotential,
    BASIC_COMMANDS,
)
from tunaed_pokemon.models.pokemon import (
    Pokemon,
    PokemonStats,
    PokemonPotentials,
    PotentialSlot,
    ExclusivePotential,
)
from tunaed_pokemon.models.party import Party, DEFAULT_PARTY_SIZE, MAX_PARTY_SIZE
from tunaed_pokemon.models.move import Move
from tunaed_pokemon.models.ability import Ability
from tunaed_pokemon.models.item import Item
from tunaed_pokemon.models.potential import PotentialTemplate


# ---------------------------------------------------------------------------
# Trainer Tests
# ---------------------------------------------------------------------------

class TestTrainer:
    def test_default_trainer(self) -> None:
        trainer = Trainer()
        assert trainer.name == ""
        assert trainer.qualities.command == QualityRank.E
        assert len(trainer.command_potentials) == 4

    def test_trainer_with_qualities(self) -> None:
        qualities = TrainerQualities(
            command=QualityRank.C,
            leadership=QualityRank.B,
            nurturing=QualityRank.A,
            ability=QualityRank.C,
        )
        trainer = Trainer(name="달크", qualities=qualities)
        assert trainer.name == "달크"
        assert trainer.qualities.command == QualityRank.C
        assert trainer.qualities.nurturing == QualityRank.A

    def test_quality_rank_display(self) -> None:
        q = TrainerQualities(command=QualityRank.A, leadership=QualityRank.B)
        assert "A" in q.command_kr
        assert "B" in q.leadership_kr

    def test_basic_commands(self) -> None:
        assert len(BASIC_COMMANDS) == 4
        names = [c.name for c in BASIC_COMMANDS]
        assert "물러나！" in names
        assert "피해라！" in names
        assert "돌아와！" in names
        assert "버텨라！" in names

    def test_innate_potential_is_separate(self) -> None:
        """고유포텐셜 is stored on the trainer, not on Pokémon (PT-05)."""
        trainer = Trainer(
            name="테스트",
            innate_potentials=[
                InnatePotential(name="테스트 고유", description="테스트용")
            ],
        )
        assert len(trainer.innate_potentials) == 1
        assert trainer.innate_potentials[0].name == "테스트 고유"


# ---------------------------------------------------------------------------
# Pokémon Tests
# ---------------------------------------------------------------------------

class TestPokemon:
    def test_default_pokemon(self) -> None:
        pkmn = Pokemon()
        assert pkmn.species == ""
        assert pkmn.type1 == PokemonType.NORMAL
        assert pkmn.type2 is None
        assert pkmn.types == [PokemonType.NORMAL]
        assert pkmn.level == 50

    def test_dual_type(self) -> None:
        pkmn = Pokemon(type1=PokemonType.FIRE, type2=PokemonType.FLYING)
        assert pkmn.types == [PokemonType.FIRE, PokemonType.FLYING]

    def test_stats_total(self) -> None:
        stats = PokemonStats()
        stats.base[StatType.HP] = 100
        stats.base[StatType.ATTACK] = 80
        stats.base[StatType.DEFENSE] = 70
        stats.base[StatType.SP_ATK] = 90
        stats.base[StatType.SP_DEF] = 75
        stats.base[StatType.SPEED] = 85
        assert stats.total_base == 500

    def test_ev_defaults_to_zero(self) -> None:
        """ST-01: Effort Values exist but default to 0."""
        stats = PokemonStats()
        for stat in stats.ev.values():
            assert stat == 0

    def test_max_move_count(self) -> None:
        pkmn = Pokemon()
        pkmn.stats.base[StatType.HP] = 100
        pkmn.stats.base[StatType.ATTACK] = 100
        pkmn.stats.base[StatType.DEFENSE] = 100
        pkmn.stats.base[StatType.SP_ATK] = 100
        pkmn.stats.base[StatType.SP_DEF] = 100
        pkmn.stats.base[StatType.SPEED] = 100
        assert pkmn.stats.total_base == 600
        assert pkmn.max_move_count == 8

    def test_exclusive_potential_separate(self) -> None:
        """전용포텐셜 is stored separately from regular potentials (PT-05)."""
        pkmn = Pokemon()
        pkmn.potentials.exclusive = ExclusivePotential(
            name="테스트 전용",
            description="특히 강력한 포텐셜",
        )
        assert pkmn.potentials.exclusive.name == "테스트 전용"
        # Regular slots should be empty.
        assert len(pkmn.potentials.slots) == 0

    def test_potential_slots(self) -> None:
        pkmn = Pokemon()
        slot = PotentialSlot(
            category=PotentialCategory.TIER_1,
            name="제1계제",
            description="테스트",
        )
        pkmn.potentials.set_slot(slot)
        assert pkmn.potentials.get(PotentialCategory.TIER_1) is not None
        assert pkmn.potentials.get(PotentialCategory.TIER_1).name == "제1계제"

    def test_alien_species_flag(self) -> None:
        pkmn = Pokemon(is_alien_species=True)
        assert pkmn.is_alien_species is True


# ---------------------------------------------------------------------------
# Party Tests
# ---------------------------------------------------------------------------

class TestParty:
    def test_default_party(self) -> None:
        party = Party()
        assert party.max_size == DEFAULT_PARTY_SIZE
        assert party.size == 0
        assert not party.is_full

    def test_add_member(self) -> None:
        party = Party()
        for i in range(6):
            party.add_member(Pokemon(species=f"포켓몬{i}"))
        assert party.size == 6
        assert party.is_full

    def test_add_member_overflow(self) -> None:
        party = Party(max_size=2)
        party.add_member(Pokemon(species="A"))
        party.add_member(Pokemon(species="B"))
        with pytest.raises(ValueError, match="full"):
            party.add_member(Pokemon(species="C"))

    def test_remove_member(self) -> None:
        party = Party()
        party.add_member(Pokemon(species="A"))
        party.add_member(Pokemon(species="B"))
        removed = party.remove_member(0)
        assert removed.species == "A"
        assert party.size == 1

    def test_variable_party_size(self) -> None:
        """P-02: Party size is variable (1-8)."""
        party = Party(max_size=MAX_PARTY_SIZE)
        for i in range(MAX_PARTY_SIZE):
            party.add_member(Pokemon(species=f"Member{i}"))
        assert party.size == MAX_PARTY_SIZE
        assert party.is_full


# ---------------------------------------------------------------------------
# Move Tests
# ---------------------------------------------------------------------------

class TestMove:
    def test_default_move(self) -> None:
        move = Move()
        assert move.name == ""
        assert move.type == PokemonType.NORMAL
        assert move.additional_flags == []

    def test_move_with_data(self) -> None:
        move = Move(
            name="화염방사",
            type=PokemonType.FIRE,
            category="특수",
            power=90,
            accuracy=100,
            pp=15,
        )
        assert move.name == "화염방사"
        assert move.power == 90


# ---------------------------------------------------------------------------
# Ability Tests
# ---------------------------------------------------------------------------

class TestAbility:
    def test_default_ability(self) -> None:
        ability = Ability()
        assert ability.name == ""

    def test_ability_with_data(self) -> None:
        ability = Ability(name="위협", effect_description="등장 시 상대의 공격을 내린다.")
        assert ability.name == "위협"


# ---------------------------------------------------------------------------
# Item Tests
# ---------------------------------------------------------------------------

class TestItem:
    def test_default_item(self) -> None:
        item = Item()
        assert item.name == ""
        assert item.is_banned is False

    def test_banned_item(self) -> None:
        item = Item(name="진화의휘석", is_banned=True)
        assert item.is_banned is True

    def test_jewel_item(self) -> None:
        item = Item(
            name="불꽃쥬얼",
            is_jewel=True,
            jewel_plate_type=PokemonType.FIRE,
            is_consumable=True,
        )
        assert item.is_jewel is True
        assert item.jewel_plate_type == PokemonType.FIRE


# ---------------------------------------------------------------------------
# Enum / Constant Tests
# ---------------------------------------------------------------------------

class TestEnums:
    def test_always_present_potentials(self) -> None:
        """All Pokémon must have these potentials."""
        assert PotentialCategory.TIER_1 in ALWAYS_PRESENT_POTENTIALS
        assert PotentialCategory.TIER_2 in ALWAYS_PRESENT_POTENTIALS
        assert PotentialCategory.AFFINITY in ALWAYS_PRESENT_POTENTIALS
        assert PotentialCategory.PREEMPTIVE in ALWAYS_PRESENT_POTENTIALS
        assert PotentialCategory.EVASION in ALWAYS_PRESENT_POTENTIALS
        assert PotentialCategory.RESISTANCE in ALWAYS_PRESENT_POTENTIALS
        assert PotentialCategory.STRIKE in ALWAYS_PRESENT_POTENTIALS
        assert PotentialCategory.GENERAL in ALWAYS_PRESENT_POTENTIALS

    def test_variable_potentials(self) -> None:
        assert PotentialCategory.ROLE in VARIABLE_POTENTIALS
        assert PotentialCategory.BOND in VARIABLE_POTENTIALS
        assert PotentialCategory.PT_1 in VARIABLE_POTENTIALS

    def test_stat_value_to_rank(self) -> None:
        assert stat_value_to_rank(1) == "E"
        assert stat_value_to_rank(50) == "D"
        assert stat_value_to_rank(100) == "B"
        assert stat_value_to_rank(135) == "A+"
        assert stat_value_to_rank(200) == "S"

    def test_quality_rank_difference(self) -> None:
        diff = quality_rank_difference(QualityRank.A, QualityRank.C)
        assert diff == 2  # A is 2 ranks above C

    def test_quality_rank_points(self) -> None:
        assert QUALITY_RANK_POINTS[QualityRank.E] == 0
        assert QUALITY_RANK_POINTS[QualityRank.C] == 4
        assert QUALITY_RANK_POINTS[QualityRank.S] == 26
