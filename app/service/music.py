from app.repository.music import MusicRepository
from app.schemas.music import TrackResponse


class MusicService:
    def __init__(self, repository: MusicRepository):
        self.repo = repository

    async def get_tracks(self) -> list[TrackResponse]:
        tracks = await self.repo.get_tracks()

        return [
            TrackResponse(
                id=track.id,
                title=track.title,
                file_extension=track.file_extension,
                duration_secs=track.duration_secs,
                bitrate=track.bitrate,
                release_date=track.release_date,
                sample_rate=track.sample_rate,
                album_id=track.album_id,
                album=track.album.name if track.album else None,
                artists=[artist.name for artist in track.artists],
            )
            for track in tracks
        ]
