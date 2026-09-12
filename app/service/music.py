from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
from fastapi import Request, status
from fastapi.responses import StreamingResponse

from app.exceptions.custom_exceptions import RetroException
from app.model.music import Track
from app.repository.music import MusicRepository
from app.schemas.music import (
    ByteRange,
    InvalidRange,
    TrackResponse,
)


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

    async def stream_music(
        self,
        music_id: int,
        request: Request,
    ) -> StreamingResponse:

        track: Track | None = await self.repo.get_track(music_id)

        if track is None:
            raise RetroException(
                message="Track not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        file_path = Path(track.file_path)

        if not file_path.is_file():
            raise RetroException(
                message="Audio file not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if track.file_extension.lower() not in [".flac", ".mp3"]:
            raise RetroException(
                message="Unsupported audio format",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        file_size = file_path.stat().st_size

        if file_size == 0:
            raise RetroException(
                message="Empty audio file",
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            )

        range_header = request.headers.get("range")

        if range_header is None:
            return StreamingResponse(
                self.iter_file(
                    file_path,
                    start=0,
                    end=file_size - 1,
                ),
                status_code=status.HTTP_200_OK,
                media_type="audio/flac",
                headers={
                    "Content-Length": str(file_size),
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": (f'inline; filename="{track.file_name}"'),
                },
            )

        try:
            byte_range = self.parse_range(
                range_header,
                file_size,
            )

        except InvalidRange:
            return StreamingResponse(
                content=iter(()),
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                headers={
                    "Content-Range": f"bytes */{file_size}",
                },
            )

        start = byte_range.start
        end = byte_range.end

        content_length = end - start + 1

        return StreamingResponse(
            self.iter_file(
                file_path,
                start=start,
                end=end,
            ),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            media_type="audio/flac",
            headers={
                "Content-Range": (f"bytes {start}-{end}/{file_size}"),
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Disposition": (f'inline; filename="{track.file_name}"'),
            },
        )

    async def iter_file(
        self,
        file_path: Path,
        start: int,
        end: int,
    ) -> AsyncIterator[bytes]:

        remaining = end - start + 1

        async with aiofiles.open(
            file_path,
            "rb",
        ) as file:
            await file.seek(start)

            while remaining > 0:
                chunk_size = min(
                    1024 * 1024,
                    remaining,
                )

                chunk = await file.read(chunk_size)

                if not chunk:
                    break

                remaining -= len(chunk)

                yield chunk

    def parse_range(
        self,
        range_header: str,
        file_size: int,
    ) -> ByteRange:

        if not range_header.startswith("bytes="):
            raise InvalidRange

        value = range_header.removeprefix("bytes=")

        if "," in value:
            raise InvalidRange

        try:
            start_str, end_str = value.split("-", 1)

            if not start_str:
                suffix_length = int(end_str)

                if suffix_length <= 0:
                    raise InvalidRange

                start = max(file_size - suffix_length, 0)
                end = file_size - 1

            else:
                start = int(start_str)

                if start < 0 or start >= file_size:
                    raise InvalidRange

                if end_str:
                    end = int(end_str)
                else:
                    end = file_size - 1

                end = min(end, file_size - 1)

                if end < start:
                    raise InvalidRange

        except ValueError, IndexError:
            raise InvalidRange

        return ByteRange(
            start=start,
            end=end,
        )
