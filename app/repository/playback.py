from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.playback import PlaybackState


class PlaybackRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_playback(self, user_id) -> PlaybackState | None:
        stmt = select(PlaybackState).where(PlaybackState.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
