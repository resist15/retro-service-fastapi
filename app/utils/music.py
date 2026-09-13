from pathlib import Path

from mutagen import File
from mutagen.flac import FLAC


def extract_embedded_art(file: Path) -> tuple[bytes, str] | None:
    audio = File(file)
    if audio is None:
        return None

    if hasattr(audio, "tags") and audio.tags is not None:
        for tag in audio.tags.values():
            if getattr(tag, "FrameID", None) == "APIC":
                return tag.data, tag.mime

    if isinstance(audio, FLAC) and audio.pictures:
        pic = audio.pictures[0]
        return pic.data, pic.mime

    return None
