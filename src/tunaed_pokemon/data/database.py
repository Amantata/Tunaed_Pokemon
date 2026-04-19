"""SQLAlchemy database schema for persistent master data and entity data.

Tables:
- moves: Master list of moves (기술) — SK-01 CRUD
- abilities: Master list of abilities (특성) — SK-03 CRUD
- items: Master list of items (소지품)
- potential_templates: Pre-defined potential templates — PT-02 selection
- trainers: Trainer entities
- pokemon: Pokémon entities
- parties: Party definitions (trainer + members)
- party_members: Join table for party → pokemon
- pokemon_extended_moves: Extended move pool via 기능확장 potential — SK-02
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all tables."""
    pass


# ---------------------------------------------------------------------------
# Master Data Tables
# ---------------------------------------------------------------------------

class MoveRow(Base):
    """Master list of moves (기술)."""

    __tablename__ = "moves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="노말")
    category: Mapped[str] = mapped_column(String(10), nullable=False, default="물리")
    contact: Mapped[str] = mapped_column(String(10), nullable=False, default="접촉")
    power: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accuracy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pp: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    effect_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    effect_script: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_sound: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_punch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_blade: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<MoveRow(id={self.id}, name='{self.name}')>"


class AbilityRow(Base):
    """Master list of abilities (특성)."""

    __tablename__ = "abilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    effect_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    effect_script: Mapped[str] = mapped_column(Text, nullable=False, default="")

    def __repr__(self) -> str:
        return f"<AbilityRow(id={self.id}, name='{self.name}')>"


class ItemRow(Base):
    """Master list of items (소지품)."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    effect_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    effect_script: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_berry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_jewel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_plate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    jewel_plate_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_consumable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<ItemRow(id={self.id}, name='{self.name}')>"


class PotentialTemplateRow(Base):
    """Pre-defined potential templates for selection (PT-02)."""

    __tablename__ = "potential_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    effect_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    effect_script: Mapped[str] = mapped_column(Text, nullable=False, default="")

    def __repr__(self) -> str:
        return f"<PotentialTemplateRow(id={self.id}, name='{self.name}')>"


# ---------------------------------------------------------------------------
# Entity Tables
# ---------------------------------------------------------------------------

class TrainerRow(Base):
    """Trainer entity."""

    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    alias: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    origin: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    career: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    image_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    # Qualities stored as individual columns for queryability.
    quality_command: Mapped[str] = mapped_column(String(5), nullable=False, default="E")
    quality_leadership: Mapped[str] = mapped_column(String(5), nullable=False, default="E")
    quality_nurturing: Mapped[str] = mapped_column(String(5), nullable=False, default="E")
    quality_ability: Mapped[str] = mapped_column(String(5), nullable=False, default="E")

    # 고유포텐셜 stored as JSON text (list of {name, description, effect_script}).
    innate_potentials_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Command potentials stored as JSON text.
    command_potentials_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Relationships
    parties: Mapped[list["PartyRow"]] = relationship(back_populates="trainer")

    def __repr__(self) -> str:
        return f"<TrainerRow(id={self.id}, name='{self.name}')>"


class PokemonRow(Base):
    """Pokémon entity."""

    __tablename__ = "pokemon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    gender: Mapped[str] = mapped_column(String(5), nullable=False, default="-")
    is_alien_species: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    type1: Mapped[str] = mapped_column(String(20), nullable=False, default="노말")
    type2: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ability_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("abilities.id"), nullable=True)
    ability_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    # Base stats, IVs, EVs stored as JSON text (dict of stat_name -> value).
    base_stats_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    iv_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    ev_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Moves as JSON list of move IDs.
    moves_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Potentials as JSON dict (category -> {name, description, effect_script}).
    potentials_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # 전용포텐셜 stored as separate JSON field (per PT-05).
    exclusive_potential_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Relationships
    party_memberships: Mapped[list["PartyMemberRow"]] = relationship(back_populates="pokemon")

    def __repr__(self) -> str:
        return f"<PokemonRow(id={self.id}, species='{self.species}')>"


class PartyRow(Base):
    """Party entity (trainer + members)."""

    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(Integer, ForeignKey("trainers.id"), nullable=False)
    max_size: Mapped[int] = mapped_column(Integer, nullable=False, default=6)

    # Relationships
    trainer: Mapped["TrainerRow"] = relationship(back_populates="parties")
    members: Mapped[list["PartyMemberRow"]] = relationship(
        back_populates="party",
        order_by="PartyMemberRow.position",
    )

    def __repr__(self) -> str:
        return f"<PartyRow(id={self.id}, trainer_id={self.trainer_id})>"


class PartyMemberRow(Base):
    """Join table: party → Pokémon with ordering."""

    __tablename__ = "party_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    party_id: Mapped[int] = mapped_column(Integer, ForeignKey("parties.id"), nullable=False)
    pokemon_id: Mapped[int] = mapped_column(Integer, ForeignKey("pokemon.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    party: Mapped["PartyRow"] = relationship(back_populates="members")
    pokemon: Mapped["PokemonRow"] = relationship(back_populates="party_memberships")


class PokemonExtendedMoveRow(Base):
    """Extended move pool via 기능확장 potential (SK-02)."""

    __tablename__ = "pokemon_extended_moves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pokemon_id: Mapped[int] = mapped_column(Integer, ForeignKey("pokemon.id"), nullable=False)
    move_id: Mapped[int] = mapped_column(Integer, ForeignKey("moves.id"), nullable=False)


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

def create_database(db_path: str = "tunaed_pokemon.db") -> sessionmaker[Session]:
    """Create the SQLite database and return a session factory.

    Args:
        db_path: Path to the SQLite database file.
                 Use ":memory:" for in-memory testing.

    Returns:
        A sessionmaker bound to the created engine.
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
