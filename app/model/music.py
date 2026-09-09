from __future__ import annotations

import datetime

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import Base, TimestampMixin

album_artists = Table(
    "album_artists",
    Base.metadata,
    Column("album_id", ForeignKey("albums.id"), primary_key=True),
    Column("artist_id", ForeignKey("artists.id"), primary_key=True),
)

track_artists = Table(
    "track_artists",
    Base.metadata,
    Column("track_id", ForeignKey("tracks.id"), primary_key=True),
    Column("artist_id", ForeignKey("artists.id"), primary_key=True),
)

track_composers = Table(
    "track_composers",
    Base.metadata,
    Column("track_id", ForeignKey("tracks.id"), primary_key=True),
    Column("artist_id", ForeignKey("artists.id"), primary_key=True),
)


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)

    artists: Mapped[list[Artist]] = relationship(secondary=album_artists)
    tracks: Mapped[list[Track]] = relationship(back_populates="album")


class Track(Base, TimestampMixin):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]

    album_id: Mapped[int | None] = mapped_column(ForeignKey("albums.id"))
    album: Mapped[Album | None] = relationship(back_populates="tracks")

    track_number: Mapped[int | None]
    track_total: Mapped[int | None]
    disc_number: Mapped[int | None]
    disc_total: Mapped[int | None]

    release_date: Mapped[datetime.date | None]

    publisher: Mapped[str | None]
    copyright: Mapped[str | None]
    isrc: Mapped[str | None]
    upc: Mapped[str | None]
    lyrics: Mapped[str | None]

    duration_secs: Mapped[float]
    bitrate: Mapped[int | None]
    sample_rate: Mapped[int | None]
    channels: Mapped[int | None]
    bits_per_sample: Mapped[int | None]

    min_blocksize: Mapped[int | None]
    max_blocksize: Mapped[int | None]
    min_framesize: Mapped[int | None]
    max_framesize: Mapped[int | None]
    total_samples: Mapped[int | None]
    audio_md5: Mapped[str | None]

    file_path: Mapped[str] = mapped_column(unique=True)
    file_name: Mapped[str]
    file_extension: Mapped[str]

    raw_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    artists: Mapped[list[Artist]] = relationship(secondary=track_artists)
    composers: Mapped[list[Artist]] = relationship(secondary=track_composers)
