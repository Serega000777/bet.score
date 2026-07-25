from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    LargeBinary,
    MetaData,
    String,
    Table,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

app_user = Table(
    "app_user",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    Column("external_subject", String, nullable=False, unique=True),
    Column("display_name", String, nullable=False),
    Column("username", String),
    Column("locale", String, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)

user_session = Table(
    "user_session",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    Column("user_id", UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=False),
    Column("token_hash", LargeBinary, nullable=False, unique=True),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("revoked", Boolean, nullable=False),
)
