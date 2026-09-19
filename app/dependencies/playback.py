from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repository.playback import PlaybackRepository
from app.service.playback import PlaybackService


def get_playback_repo(session: AsyncSession = Depends(get_db)) -> PlaybackRepository:
    return PlaybackRepository(session=session)


def get_playback_service(
    repository: PlaybackRepository = Depends(get_playback_repo),
) -> PlaybackService:
    return PlaybackService(repository=repository)
