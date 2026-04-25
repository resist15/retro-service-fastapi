from fastapi import APIRouter

from app.routers.auth import auth_router

public_router = APIRouter()

public_router.include_router(auth_router)
