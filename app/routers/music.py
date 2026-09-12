from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.dependencies.music import get_music_service
from app.exceptions.custom_exceptions import RetroException
from app.schemas.music import ScanState, ScanStatus, TrackResponse, scan_state
from app.service.music import MusicService
from app.service.music_scan import run_scan

music_router = APIRouter(tags=["Music"], prefix="/music")


@music_router.post("/scan")
async def start_scan(background_tasks: BackgroundTasks) -> ScanState:
    if scan_state.status == ScanStatus.RUNNING:
        raise RetroException(
            message="Scan already running", status_code=status.HTTP_409_CONFLICT
        )

    background_tasks.add_task(run_scan)
    scan_state.status = ScanStatus.RUNNING
    scan_state.inserted = 0

    return scan_state


@music_router.get("/scan/status")
async def get_scan_status() -> ScanState:
    return scan_state


@music_router.get("/tracks", response_model=list[TrackResponse])
async def get_tracks(music_service: MusicService = Depends(get_music_service)):
    return await music_service.get_tracks()
