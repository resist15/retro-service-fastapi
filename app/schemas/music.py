import datetime
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, computed_field


class ScanRequest(BaseModel):
    full: bool = False


class ScanStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"


class ScanState(BaseModel):
    status: ScanStatus = ScanStatus.IDLE
    inserted: int = 0
    percentage: int = 0


scan_state = ScanState()


class MusicFile(BaseModel):
    title: str
    artists: list[str] = Field(default_factory=list)

    album: str | None = None
    album_artists: list[str] = Field(default_factory=list)

    track_number: int | None = None
    track_total: int | None = None

    disc_number: int | None = None
    disc_total: int | None = None

    release_date: datetime.date | None = None

    composer: list[str] = Field(default_factory=list)
    publisher: str | None = None
    copyright: str | None = None

    isrc: str | None = None
    upc: str | None = None

    lyrics: str | None = None
    comment: list[str] = Field(default_factory=list)
    description: list[str] = Field(default_factory=list)

    duration_secs: float
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    bits_per_sample: int | None = None

    min_blocksize: int | None = None
    max_blocksize: int | None = None
    min_framesize: int | None = None
    max_framesize: int | None = None
    total_samples: int | None = None
    audio_md5: str | None = None

    file_path: str
    file_name: str
    file_extension: str

    raw_metadata: dict[str, list[str]] = Field(default_factory=dict)

    file_mtime: datetime.datetime


class TrackResponse(BaseModel):
    id: int
    file_extension: str
    duration_secs: float
    bitrate: int | None
    release_date: date | None
    sample_rate: int | None
    title: str
    album_id: int | None
    album: str | None
    artists: list[str]
    cover_path: str | None = Field(exclude=True)

    @computed_field
    @property
    def cover_url(self) -> str | None:
        if not self.cover_path:
            return None
        return f"/covers/{Path(self.cover_path).name}"

    class Config:
        from_attributes = True


@dataclass(frozen=True)
class ByteRange:
    start: int
    end: int


class InvalidRange(Exception):
    pass


class TrackPageResponse(BaseModel):
    items: list[TrackResponse]
    next_cursor: int | None
    has_more: bool


class PlaybackStateRequest(BaseModel):
    track_id: int
    progress_secs: int
