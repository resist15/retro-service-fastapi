from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from app.model.music import Album, Artist, Track


class MusicRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_tracks(self) -> list[Track]:
        q = select(Track).options(
            load_only(
                Track.id,
                Track.title,
                Track.album_id,
                Track.release_date,
                Track.bitrate,
                Track.sample_rate,
                Track.file_extension,
                Track.duration_secs,
            ),
            selectinload(Track.album).load_only(
                Album.id,
                Album.name,
            ),
            selectinload(Track.artists).load_only(
                Artist.id,
                Artist.name,
            ),
        )

        result = await self.db.execute(q)

        return list(result.scalars().all())
