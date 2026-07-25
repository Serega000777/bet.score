import asyncio
import hashlib
from pathlib import Path

import asyncpg

from bet_score.config import get_settings

MIGRATION_LOCK_ID = 7_203_114_092


def migrations_path() -> Path:
    for candidate in (
        Path("database/migrations"),
        Path("../database/migrations"),
        Path("/app/database/migrations"),
    ):
        if candidate.is_dir():
            return candidate
    raise RuntimeError("Каталог миграций не найден")


async def migrate() -> None:
    database_url = get_settings().database_url.replace("postgresql+asyncpg://", "postgresql://")
    connection = await asyncpg.connect(database_url)
    try:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migration (
              version text PRIMARY KEY,
              checksum text NOT NULL,
              applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        await connection.execute("SELECT pg_advisory_lock($1)", MIGRATION_LOCK_ID)
        try:
            await apply_pending_migrations(connection)
        finally:
            await connection.execute("SELECT pg_advisory_unlock($1)", MIGRATION_LOCK_ID)
    finally:
        await connection.close()


async def apply_pending_migrations(connection: asyncpg.Connection) -> None:
    applied_rows = await connection.fetch("SELECT version, checksum FROM schema_migration")
    applied = {str(row["version"]): str(row["checksum"]) for row in applied_rows}

    for migration in sorted(migrations_path().glob("*.sql")):
        version = migration.name
        if version.startswith("900_") and get_settings().app_env == "production":
            continue
        sql = migration.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode()).hexdigest()
        if version in applied:
            if applied[version] != checksum:
                raise RuntimeError(f"Применённая миграция {version} была изменена")
            continue

        async with connection.transaction():
            await connection.execute(sql)
            await connection.execute(
                "INSERT INTO schema_migration(version, checksum) VALUES($1, $2)",
                version,
                checksum,
            )
        print(f"Применена миграция {version}")


def main() -> None:
    asyncio.run(migrate())


if __name__ == "__main__":
    main()
