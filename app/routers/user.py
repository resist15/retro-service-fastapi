from types import SimpleNamespace

from fastapi import APIRouter, Depends

from app.dependencies.playback import get_playback_service
from app.dependencies.user import get_current_user_email, get_user_service
from app.schemas.user import PlaybackStateResponse, UserResponse
from app.service.playback import PlaybackService
from app.service.user import UserService

user_router = APIRouter(tags=["User"], prefix="/user")


@user_router.get("/me", response_model=UserResponse)
async def register(
    user_service: UserService = Depends(get_user_service),
    user: SimpleNamespace = Depends(get_current_user_email),
) -> UserResponse:
    return await user_service.get_user(user.email)


@user_router.get("/me/state", response_model=PlaybackStateResponse)
async def get_playback_state(
    playback_service: PlaybackService = Depends(get_playback_service),
    user: SimpleNamespace = Depends(get_current_user_email),
) -> PlaybackStateResponse:
    return await playback_service.get_playback_state(user.id)
