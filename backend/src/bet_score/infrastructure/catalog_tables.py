from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

sport = Table(
    "sport",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("code", String, nullable=False, unique=True),
    Column("name", String, nullable=False),
)

competition = Table(
    "competition",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("sport_id", UUID(as_uuid=True), ForeignKey("sport.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("country_code", String(2)),
)

sporting_event = Table(
    "sporting_event",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("competition_id", UUID(as_uuid=True), ForeignKey("competition.id"), nullable=False),
    Column("starts_at", DateTime(timezone=True), nullable=False),
    Column("status", String, nullable=False),
)

team = Table(
    "team",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("sport_id", UUID(as_uuid=True), ForeignKey("sport.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("short_name", String(32), nullable=False),
    Column("country_code", String(2)),
    UniqueConstraint("sport_id", "name", name="team_sport_name_uq"),
)

event_participant = Table(
    "event_participant",
    metadata,
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("sporting_event.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("team_id", UUID(as_uuid=True), ForeignKey("team.id"), primary_key=True),
    Column("role", String, nullable=False),
    Column("score", Integer),
    UniqueConstraint("event_id", "role", name="event_participant_event_role_uq"),
    CheckConstraint("role IN ('home', 'away')", name="event_participant_role_check"),
    CheckConstraint("score IS NULL OR score >= 0", name="event_participant_score_check"),
)
