from fastapi import APIRouter

from app.routers.user import user_router

private_router = APIRouter()

private_router.include_router(user_router)
