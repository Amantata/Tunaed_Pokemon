"""Tests for the database layer."""

from __future__ import annotations

import pytest

from tunaed_pokemon.data.database import (
    Base,
    MoveRow,
    AbilityRow,
    ItemRow,
    PotentialTemplateRow,
    TrainerRow,
    PokemonRow,
    PartyRow,
    PartyMemberRow,
    PokemonExtendedMoveRow,
    create_database,
)


@pytest.fixture
def session():
    """Create an in-memory database session for testing."""
    SessionFactory = create_database(":memory:")
    session = SessionFactory()
    yield session
    session.close()


class TestDatabase:
    def test_create_tables(self, session) -> None:
        """All tables should be created successfully."""
        # If we got here without error, tables were created.
        assert session is not None

    def test_insert_move(self, session) -> None:
        move = MoveRow(name="화염방사", type="불꽃", category="특수", power=90, accuracy=100, pp=15)
        session.add(move)
        session.commit()

        result = session.query(MoveRow).filter_by(name="화염방사").first()
        assert result is not None
        assert result.power == 90

    def test_insert_ability(self, session) -> None:
        ability = AbilityRow(name="위협", effect_description="등장 시 상대의 공격을 내린다.")
        session.add(ability)
        session.commit()

        result = session.query(AbilityRow).filter_by(name="위협").first()
        assert result is not None

    def test_insert_item(self, session) -> None:
        item = ItemRow(name="구애머리띠", effect_description="공격 1.5배, 같은 기술만 사용")
        session.add(item)
        session.commit()

        result = session.query(ItemRow).filter_by(name="구애머리띠").first()
        assert result is not None

    def test_insert_trainer_and_party(self, session) -> None:
        trainer = TrainerRow(
            name="달크",
            quality_command="C",
            quality_leadership="B",
            quality_nurturing="A",
            quality_ability="C",
        )
        session.add(trainer)
        session.commit()

        party = PartyRow(trainer_id=trainer.id, max_size=6)
        session.add(party)
        session.commit()

        pkmn = PokemonRow(
            species="리자몽",
            name="리자몽",
            type1="불꽃",
            type2="비행",
            level=50,
        )
        session.add(pkmn)
        session.commit()

        member = PartyMemberRow(party_id=party.id, pokemon_id=pkmn.id, position=0)
        session.add(member)
        session.commit()

        # Verify relationships
        loaded_party = session.query(PartyRow).filter_by(id=party.id).first()
        assert loaded_party is not None
        assert loaded_party.trainer.name == "달크"
        assert len(loaded_party.members) == 1
        assert loaded_party.members[0].pokemon.species == "리자몽"

    def test_potential_template(self, session) -> None:
        template = PotentialTemplateRow(
            category="역할",
            name="에이스",
            trigger_text="자진 에이스",
            effect_text="T 개시 시 자신의 임의의 능력을 올린다.",
        )
        session.add(template)
        session.commit()

        result = session.query(PotentialTemplateRow).filter_by(name="에이스").first()
        assert result is not None
        assert result.category == "역할"

    def test_extended_moves(self, session) -> None:
        """SK-02: 기능확장 extended move pool."""
        move = MoveRow(name="냉동빔", type="얼음", category="특수", power=90, accuracy=100, pp=10)
        session.add(move)
        session.commit()

        pkmn = PokemonRow(species="피카츄", name="피카츄", type1="전기", level=50)
        session.add(pkmn)
        session.commit()

        ext = PokemonExtendedMoveRow(pokemon_id=pkmn.id, move_id=move.id)
        session.add(ext)
        session.commit()

        result = session.query(PokemonExtendedMoveRow).filter_by(pokemon_id=pkmn.id).all()
        assert len(result) == 1
        assert result[0].move_id == move.id
