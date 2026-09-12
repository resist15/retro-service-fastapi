from fastapi import APIRouter, Depends

from app.dependencies.user import get_current_user_email
from app.routers.music import music_router
from app.routers.user import user_router

private_router = APIRouter(dependencies=[Depends(get_current_user_email)])

private_router.include_router(user_router)
private_router.include_router(music_router)
