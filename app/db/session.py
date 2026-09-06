import contextlib
from collections.abc import AsyncGenerator, AsyncIterator

from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.observability.logging import get_logger

logger = get_logger(__name__)


class DatabaseSessionManager:
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    async def init(self, dsn: str) -> None:
        self._engine = create_async_engine(
            str(dsn),
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
            echo=settings.SQLALCHEMY_LOG,
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        SQLAlchemyInstrumentor().instrument(engine=self._engine.sync_engine)
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error("Database connection failed")
            logger.exception(e)
            raise

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if not self._sessionmaker:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        session = self._sessionmaker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager()


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with sessionmanager.session() as session:
        yield session
