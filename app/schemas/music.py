import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


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
