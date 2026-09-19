from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.playback import PlaybackState


class PlaybackRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_playback(self, user_id) -> PlaybackState | None:
        stmt = select(PlaybackState).where(PlaybackState.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_playback_state(self, data: PlaybackState) -> PlaybackState | None:
        stmt = insert(PlaybackState).values(
            user_id=data.user_id,
            progress=data.progress,
            track_id=data.track_id,
        )

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=[PlaybackState.user_id],
            set_={
                "progress": stmt.excluded.progress,
                "track_id": stmt.excluded.track_id,
            },
        ).returning(PlaybackState)

        result = await self.db.execute(upsert_stmt)
        return result.scalar_one_or_none()
