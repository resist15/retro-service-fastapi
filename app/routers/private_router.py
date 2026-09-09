from fastapi import APIRouter

from app.routers.music import music_router
from app.routers.user import user_router

private_router = APIRouter()

private_router.include_router(user_router)
private_router.include_router(music_router)
