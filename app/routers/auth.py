from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Response
from redis.asyncio import Redis

from app.db.redis import get_redis
from app.dependencies.user import get_current_user_email, get_user_service
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    LoginResponseMessage,
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


@auth_router.post("/login", response_model=LoginResponseMessage)
async def login(
    dto: LoginRequest,
    response: Response,
    user_service: UserService = Depends(get_user_service),
    redis: Redis = Depends(get_redis),
) -> LoginResponse:
    return await user_service.login_user(response=response, dto=dto, redis=redis)


@auth_router.post("/refresh", response_model=LoginResponseMessage)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    user_service: UserService = Depends(get_user_service),
    redis: Redis = Depends(get_redis),
):
    print(refresh_token)
    token: RefreshRequest = RefreshRequest(refresh_token=UUID(refresh_token))
    return await user_service.refresh(response=response, dto=token, redis=redis)


@auth_router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    user_service: UserService = Depends(get_user_service),
    user=Depends(get_current_user_email),
    redis: Redis = Depends(get_redis),
):
    token: RefreshRequest = RefreshRequest(refresh_token=UUID(refresh_token))
    return await user_service.logout(
        id=user.id,
        dto=token,
        redis=redis,
        jti=user.auth_token.get("jti"),
        response=response,
    )


@auth_router.post("/logout/all")
async def logout_all(
    response: Response,
    user_service: UserService = Depends(get_user_service),
    user=Depends(get_current_user_email),
    redis: Redis = Depends(get_redis),
):
    return await user_service.logout_all(user.id, redis=redis, response=response)
