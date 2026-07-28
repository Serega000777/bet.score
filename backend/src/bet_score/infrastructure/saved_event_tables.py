from sqlalchemy import Column, DateTime, ForeignKey, MetaData, Table, text
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

saved_event = Table(
    "saved_event",
    metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("app_user.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("sporting_event.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)
