from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

from app.dependencies.music import get_music_service
from app.dependencies.user import require_role
from app.exceptions.custom_exceptions import RetroException
from app.schemas.music import (
    ScanRequest,
    ScanState,
    ScanStatus,
    TrackResponse,
    scan_state,
)
from app.service.music import MusicService
from app.service.music_scan import run_scan
from app.utils.enums import UserRole

music_router = APIRouter(tags=["Music"], prefix="/music")


@music_router.post("/scan")
async def scan_full(
    payload: ScanRequest,
    background_tasks: BackgroundTasks,
    user=Depends(require_role(UserRole.SUPER_USER)),
) -> ScanState:
    if scan_state.status == ScanStatus.RUNNING:
        raise RetroException(
            message="Scan already running", status_code=status.HTTP_409_CONFLICT
        )

    background_tasks.add_task(run_scan, payload)
    scan_state.status = ScanStatus.RUNNING
    scan_state.inserted = 0

    return scan_state


@music_router.get("/scan/status")
async def get_scan_status() -> ScanState:
    return scan_state


@music_router.get("/tracks", response_model=list[TrackResponse])
async def get_tracks(music_service: MusicService = Depends(get_music_service)):
    return await music_service.get_tracks()


@music_router.get("/tracks/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: int, music_service: MusicService = Depends(get_music_service)
):
    return await music_service.get_track(track_id)


@music_router.get("/stream/{music_id}")
async def stream_music(
    music_id: int,
    request: Request,
    music_service: MusicService = Depends(get_music_service),
):
    return await music_service.stream_music(music_id, request)
