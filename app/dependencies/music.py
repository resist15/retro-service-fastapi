from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repository.music import MusicRepository
from app.service.music import MusicService


def get_music_repo(session: AsyncSession = Depends(get_db)) -> MusicRepository:
    return MusicRepository(session=session)


def get_music_service(
    repository: MusicRepository = Depends(get_music_repo),
) -> MusicService:
    return MusicService(repository=repository)
