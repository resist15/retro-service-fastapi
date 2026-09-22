from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Request, Response
from redis.asyncio import Redis

from app.db.redis import get_redis
from app.dependencies.user import get_current_user_email, get_user_service
from app.exceptions.custom_exceptions import RetroException
from app.exceptions.errors import ErrorCode
from app.schemas.user import (
    DeviceSession,
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
    request: Request,
    response: Response,
    user_service: UserService = Depends(get_user_service),
    redis: Redis = Depends(get_redis),
) -> LoginResponse:
    return await user_service.login_user(
        response=response, dto=dto, redis=redis, request=request
    )


@auth_router.post("/refresh")
async def refresh(
    response: Response,
    request: Request,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    user_service: UserService = Depends(get_user_service),
    redis: Redis = Depends(get_redis),
):
    if refresh_token is None:
        raise RetroException(ErrorCode.INVALID_CREDENTIALS)
    token: RefreshRequest = RefreshRequest(refresh_token=UUID(refresh_token))
    return await user_service.refresh(
        response=response, dto=token, redis=redis, request=request
    )


@auth_router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    user_service: UserService = Depends(get_user_service),
    user=Depends(get_current_user_email),
    redis: Redis = Depends(get_redis),
):
    if refresh_token is None:
        raise RetroException(ErrorCode.INVALID_CREDENTIALS)

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


@auth_router.get("/sessions", response_model=list[DeviceSession])
async def get_sessions(
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    user_service: UserService = Depends(get_user_service),
    user=Depends(get_current_user_email),
):
    if refresh_token is None:
        raise RetroException(ErrorCode.INVALID_CREDENTIALS)

    return await user_service.get_all_session(
        user_id=user.id,
        refresh_token=UUID(refresh_token),
    )


@auth_router.post("/logout/session/{session_id}")
async def logout_specific(
    response: Response,
    session_id: str,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    user_service: UserService = Depends(get_user_service),
    user=Depends(get_current_user_email),
    redis: Redis = Depends(get_redis),
):
    if refresh_token is None:
        raise RetroException(ErrorCode.INVALID_CREDENTIALS)

    token: RefreshRequest = RefreshRequest(refresh_token=UUID(refresh_token))
    return await user_service.logout_specific(
        id=user.id,
        dto=token,
        session_id=session_id,
        redis=redis,
        current_jti=user.auth_token.get("jti"),
        response=response,
    )
