from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from app.model.music import Album, Artist, Track


class MusicRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_tracks(
        self,
        limit: int = 30,
        cursor: int | None = None,
    ) -> list[Track]:

        q = (
            select(Track)
            .options(
                load_only(
                    Track.id,
                    Track.title,
                    Track.album_id,
                    Track.release_date,
                    Track.bitrate,
                    Track.sample_rate,
                    Track.file_extension,
                    Track.duration_secs,
                    Track.cover_path,
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
            .order_by(Track.id.asc())
            .limit(limit)
        )

        if cursor is not None:
            q = q.where(Track.id > cursor)

        result = await self.db.execute(q)

        return list(result.scalars().all())

    async def get_track(
        self,
        track_id: int,
    ) -> Track | None:

        query = (
            select(Track)
            .options(
                load_only(
                    Track.id,
                    Track.title,
                    Track.album_id,
                    Track.release_date,
                    Track.bitrate,
                    Track.sample_rate,
                    Track.file_extension,
                    Track.duration_secs,
                    Track.cover_path,
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
            .where(Track.id == track_id)
        )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_single_track(self, track_id) -> Track | None:
        stmt = select(Track).where(Track.id == track_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
