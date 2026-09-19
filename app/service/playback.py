from app.model.playback import PlaybackState
from app.observability.decorators import observe
from app.observability.logging import get_logger
from app.repository.playback import PlaybackRepository
from app.schemas.user import (
    PlaybackStateResponse,
)

logger = get_logger(__name__)


class PlaybackService:
    def __init__(self, repository: PlaybackRepository):
        self.repo = repository

    @observe("PlaybackService.get_playback_state")
    async def get_playback_state(self, user_id: int) -> PlaybackStateResponse:
        state: PlaybackState | None = await self.repo.get_playback(user_id=user_id)

        if state is None:
            return PlaybackStateResponse()

        return PlaybackStateResponse(
            progress=state.progress, playing=True, track_id=state.track_id
        )
