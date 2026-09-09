import datetime
from pathlib import Path
from sqlite3 import IntegrityError
from typing import Any

from mutagen import File
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

import app.model.music
from app.core.config import settings
from app.db.session import sessionmanager
from app.model.music import Album, Artist, Track, track_artists, track_composers
from app.schemas.music import MusicFile, ScanStatus, scan_state


async def insert_music_file(
    session: AsyncSession,
    music: MusicFile,
) -> bool:

    async def get_or_create_artist(name: str) -> Artist:
        result = await session.execute(select(Artist).where(Artist.name == name))

        artist = result.scalar_one_or_none()

        if artist is None:
            artist = Artist(name=name)
            session.add(artist)
            await session.flush()

        return artist

    artists = [await get_or_create_artist(name) for name in music.artists]
    composers = [await get_or_create_artist(name) for name in music.composer]
    album_artists = [await get_or_create_artist(name) for name in music.album_artists]

    album: Album | None = None

    if music.album:
        result = await session.execute(select(Album).where(Album.name == music.album))

        album = result.scalar_one_or_none()

        if album is None:
            album = Album(
                name=music.album,
                artists=album_artists,
            )

            session.add(album)
            await session.flush()

    track_data = {
        "title": music.title,
        "album_id": album.id if album else None,
        "track_number": music.track_number,
        "track_total": music.track_total,
        "disc_number": music.disc_number,
        "disc_total": music.disc_total,
        "release_date": music.release_date,
        "publisher": music.publisher,
        "copyright": music.copyright,
        "isrc": music.isrc,
        "upc": music.upc,
        "lyrics": music.lyrics,
        "duration_secs": music.duration_secs,
        "bitrate": music.bitrate,
        "sample_rate": music.sample_rate,
        "channels": music.channels,
        "bits_per_sample": music.bits_per_sample,
        "min_blocksize": music.min_blocksize,
        "max_blocksize": music.max_blocksize,
        "min_framesize": music.min_framesize,
        "max_framesize": music.max_framesize,
        "total_samples": music.total_samples,
        "audio_md5": music.audio_md5,
        "file_path": music.file_path,
        "file_name": music.file_name,
        "file_extension": music.file_extension,
        "raw_metadata": music.raw_metadata,
    }

    stmt = pg_insert(Track).values(**track_data)
    stmt = stmt.on_conflict_do_nothing(index_elements=["file_path"])
    result = await session.execute(stmt.returning(Track.id))

    track_id = result.scalar_one_or_none()

    if track_id is None:
        return False

    await session.execute(
        pg_insert(track_artists).values(
            [{"track_id": track_id, "artist_id": artist.id} for artist in artists]
        )
    )

    await session.execute(
        pg_insert(track_composers).values(
            [{"track_id": track_id, "artist_id": composer.id} for composer in composers]
        )
    )

    if album:
        await session.execute(
            pg_insert(app.model.music.album_artists).values(
                [
                    {"album_id": album.id, "artist_id": artist.id}
                    for artist in album_artists
                ]
            )
        )

    return True


def parse_music_file(file: Path) -> MusicFile:
    def get_tag(audio: Any, key: str) -> list[str]:
        if not audio.tags:
            return []

        value = audio.tags.get(key)

        if value is None:
            return []

        if isinstance(value, list):
            return [str(item) for item in value]

        return [str(value)]

    def first_tag(audio: Any, key: str) -> str | None:
        values = get_tag(audio, key)

        return values[0] if values else None

    def parse_number(value: str | None) -> int | None:
        if not value:
            return None

        try:
            return int(value.split("/")[0])
        except ValueError:
            return None

    def parse_total(value: str | None) -> int | None:
        if not value or "/" not in value:
            return None

        try:
            return int(value.split("/")[1])
        except ValueError:
            return None

    def parse_date(value: str | None) -> datetime.date | None:
        if not value:
            return None
        try:
            return datetime.date.fromisoformat(value[:10])
        except ValueError:
            return None

    audio = File(file, easy=True)

    if audio is None:
        raise ValueError(f"Unable to read audio file: {file}")

    track_number = first_tag(audio, "TRACKNUMBER")
    disc_number = first_tag(audio, "DISCNUMBER")
    date = first_tag(audio, "DATE")

    raw_metadata = {
        key: [str(item) for item in value] for key, value in (audio.tags or {}).items()
    }

    md5 = getattr(audio.info, "md5_signature", None)

    return MusicFile(
        title=first_tag(audio, "TITLE") or file.stem,
        artists=get_tag(audio, "ARTIST"),
        album=first_tag(audio, "ALBUM"),
        album_artists=get_tag(audio, "ALBUMARTIST"),
        track_number=parse_number(track_number),
        track_total=parse_total(track_number),
        disc_number=parse_number(disc_number),
        disc_total=parse_total(disc_number),
        release_date=parse_date(date),
        composer=get_tag(audio, "COMPOSER"),
        publisher=first_tag(audio, "PUBLISHER"),
        copyright=first_tag(audio, "COPYRIGHT"),
        isrc=first_tag(audio, "ISRC"),
        upc=first_tag(audio, "UPC"),
        lyrics=first_tag(audio, "LYRICS"),
        comment=get_tag(audio, "COMMENT"),
        description=get_tag(audio, "DESCRIPTION"),
        duration_secs=audio.info.length,
        bitrate=getattr(audio.info, "bitrate", None),
        sample_rate=getattr(audio.info, "sample_rate", None),
        channels=getattr(audio.info, "channels", None),
        bits_per_sample=getattr(audio.info, "bits_per_sample", None),
        min_blocksize=getattr(audio.info, "min_blocksize", None),
        max_blocksize=getattr(audio.info, "max_blocksize", None),
        min_framesize=getattr(audio.info, "min_framesize", None),
        max_framesize=getattr(audio.info, "max_framesize", None),
        total_samples=getattr(audio.info, "total_samples", None),
        audio_md5=str(md5) if md5 is not None else None,
        file_path=str(file),
        file_name=file.name,
        file_extension=file.suffix.lower(),
        raw_metadata=raw_metadata,
    )


async def run_scan() -> None:
    music_dir = Path(settings.MUSIC_DIR)
    allowed_extensions = {".flac", ".mp3"}

    scan_state.status = ScanStatus.RUNNING
    scan_state.inserted = 0
    scan_state.percentage = 0

    files = music_dir.rglob("*")
    music_files = [
        file
        for file in files
        if file.is_file() and file.suffix.lower() in allowed_extensions
    ]
    total_music = len(music_files)

    async with sessionmanager.session() as session:
        count = 0
        for file in music_files:
            count += 1
            try:
                music = parse_music_file(file)
                inserted = await insert_music_file(session, music)
                scan_state.percentage = int((count / total_music) * 100)
                if inserted:
                    scan_state.inserted += 1
            except IntegrityError:
                continue

    scan_state.status = ScanStatus.DONE
