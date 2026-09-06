from fastapi import APIRouter

from app.routers.auth import auth_router
from app.routers.google_auth import google_router

public_router = APIRouter()

public_router.include_router(auth_router)
public_router.include_router(google_router)
