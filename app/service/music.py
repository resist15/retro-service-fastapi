from app.repository.music import MusicRepository


class MusicService:
    def __init__(self, repository: MusicRepository):
        self.repo = repository

    async def get_track(self):
       return await self.repo.get_tracks() 