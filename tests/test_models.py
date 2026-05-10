"""Tests for data models: Pokemon, Trainer, Party, enums."""

from __future__ import annotations

import pytest

from tunaed_pokemon.models.pokemon import (
    Pokemon, IVs, EVs, MoveData, AbilityData, PotentialData, AssignedPotential,
    MANDATORY_POTENTIAL_SLOTS, POKEMON_POTENTIAL_SLOTS,
)
from tunaed_pokemon.models.trainer import Trainer, InnatePotential, Quality
from tunaed_pokemon.models.party import Party
from tunaed_pokemon.models.enums import QualityRank


class TestIVsEVs:
    def test_default_ivs_are_zero(self):
        assert IVs().hp == 0

    def test_round_trip(self):
        ivs = IVs(hp=31, attack=25, speed=10)
        ivs2 = IVs.from_dict(ivs.to_dict())
        assert ivs2.hp == 31
        assert ivs2.speed == 10

    def test_evs_default_zero(self):
        """ST-01: EVs default to 0."""
        evs = EVs()
        for attr in ("hp", "attack", "defense", "sp_atk", "sp_def", "speed"):
            assert getattr(evs, attr) == 0


class TestMoveData:
    def test_new_gets_unique_id(self):
        m1 = MoveData.new("기합구슬")
        m2 = MoveData.new("기합구슬")
        assert m1.id != m2.id

    def test_round_trip(self):
        m = MoveData.new("화염방사")
        m.type = "불꽃"
        m.power = 90
        m2 = MoveData.from_dict(m.to_dict())
        assert m2.name == "화염방사"
        assert m2.power == 90


class TestAbilityData:
    def test_round_trip(self):
        a = AbilityData.new("위협")
        a.effect = "전투 시작 시 상대의 공격 1단계 하락"
        a2 = AbilityData.from_dict(a.to_dict())
        assert a2.name == "위협"
        assert "공격" in a2.effect


class TestPokemon:
    def test_exclusive_potential_separate_field(self):
        """PT-05: 전용포텐셜 is a separate field, not in the potentials list."""
        p = Pokemon.new("피카츄")
        excl = AssignedPotential(slot="전용포텐셜", name="번개", effect="초강력 전기")
        p.exclusive_potential = excl
        d = p.to_dict()
        # Must be in its own key, not merged into potentials list
        assert d["exclusive_potential"] is not None
        assert d["exclusive_potential"]["slot"] == "전용포텐셜"
        assert all(pt["slot"] != "전용포텐셜" for pt in d["potentials"])

    def test_round_trip(self):
        p = Pokemon.new("이상해씨")
        p.level = 36
        p.type1 = "풀"
        p.type2 = "독"
        p2 = Pokemon.from_dict(p.to_dict())
        assert p2.level == 36
        assert p2.type2 == "독"

    def test_mandatory_slots_defined(self):
        """All mandatory potential slots are listed in the constant."""
        for slot in {"계제①", "계제②", "속별", "선제", "회피", "내성", "격", "범용"}:
            assert slot in MANDATORY_POTENTIAL_SLOTS


class TestTrainer:
    def test_innate_potential_separate_field(self):
        """PT-05: 고유포텐셜 is a SEPARATE field on Trainer (not on Pokémon)."""
        t = Trainer.new("레드")
        t.innate_potentials = [InnatePotential(name="영웅의 의지", effect="...")]
        d = t.to_dict()
        assert d["innate_potentials"][0]["name"] == "영웅의 의지"

    def test_default_qualities_created(self):
        t = Trainer.new("블루")
        assert len(t.qualities) == 4

    def test_quality_rank_points(self):
        assert QualityRank.E.points == 0
        assert QualityRank.A.points == 10
        assert QualityRank.S.points == 26

    def test_round_trip(self):
        t = Trainer.new("그린")
        t.alias = "오박사의 손자"
        t2 = Trainer.from_dict(t.to_dict())
        assert t2.alias == "오박사의 손자"


class TestParty:
    def test_new_party_is_empty(self):
        p = Party.new("테스트 파티")
        assert p.pokemon_ids == []
        assert p.max_size == 6

    def test_round_trip(self):
        p = Party.new("배틀 파티")
        p.pokemon_ids = ["id1", "id2"]
        p2 = Party.from_dict(p.to_dict())
        assert p2.pokemon_ids == ["id1", "id2"]
