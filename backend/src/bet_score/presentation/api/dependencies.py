from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from bet_score.application.catalog import CatalogService
from bet_score.infrastructure.catalog_repository import SqlAlchemyCatalogRepository
from bet_score.infrastructure.database import get_database_session


def get_catalog_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> CatalogService:
    return CatalogService(SqlAlchemyCatalogRepository(session))


CatalogServiceDependency = Annotated[CatalogService, Depends(get_catalog_service)]
