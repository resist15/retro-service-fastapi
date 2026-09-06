from fastapi import APIRouter, Depends, Header
from redis.asyncio import Redis

from app.db.redis import get_redis
from app.dependencies.user import get_current_user_email, get_user_service
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    UserRequest,
    UserResponse,
)
from app.service.user import UserService

auth_router = APIRouter(tags=["Auth"], prefix="/auth")


@auth_router.post("/register", response_model=UserResponse)
async def register(
    dto: UserRequest, user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await user_service.create_user(dto=dto)


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    dto: LoginRequest,
    user_service: UserService = Depends(get_user_service),
    redis: Redis = Depends(get_redis),
) -> LoginResponse:
    return await user_service.login_user(dto=dto, redis=redis)


@auth_router.post("/refresh", response_model=LoginResponse)
async def refresh(
    dto: RefreshRequest,
    user_service: UserService = Depends(get_user_service),
    redis: Redis = Depends(get_redis),
):
    return await user_service.refresh(dto=dto, redis=redis)


@auth_router.post("/logout")
async def logout(
    dto: RefreshRequest,
    user_service: UserService = Depends(get_user_service),
    user=Depends(get_current_user_email),
    redis: Redis = Depends(get_redis),
):
    return await user_service.logout(
        id=user.id, dto=dto, redis=redis, jti=user.auth_token.get("jti")
    )


@auth_router.post("/logout/all")
async def logout_all(
    user_service: UserService = Depends(get_user_service),
    user=Depends(get_current_user_email),
    redis: Redis = Depends(get_redis),
):
    return await user_service.logout_all(user.id, redis=redis)
