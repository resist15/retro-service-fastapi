from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.music import Track


class MusicRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_tracks(self) -> list[Track] | None:
        q = select(Track)
        result = await self.db.execute(q)
        music = result.scalars().all()
        return music
