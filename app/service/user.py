import uuid
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis

from app.core.config import settings
from app.exceptions.custom_exceptions import RetroException
from app.exceptions.errors import ErrorCode
from app.model.user import User
from app.observability.decorators import observe
from app.observability.logging import get_logger
from app.repository.user import UserRepository
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    UserRequest,
    UserResponse,
)
from app.utils.auth import Authutils

logger = get_logger(__name__)


class UserService:
    def __init__(self, repository: UserRepository):
        self.repo = repository

    @observe("UserService.create_user")
    async def create_user(self, dto: UserRequest) -> UserResponse:
        db_user = await self.repo.get_user_by_email(dto.email)
        if db_user != None:
            raise RetroException(ErrorCode.USER_ALREADY_EXISTS)
        user_data = dto.model_dump()
        user_data["password"] = Authutils.hash_password(user_data["password"])

        user: User = User(**user_data)
        await self.repo.create_user(user)
        return UserResponse.model_validate(user)

    @observe("UserService.login_user")
    async def login_user(self, dto: LoginRequest, redis: Redis) -> LoginResponse:
        db_user = await self.repo.get_user_by_email(dto.email)
        if db_user == None:
            raise RetroException(ErrorCode.INVALID_CREDENTIALS)

        if not Authutils.verify_password(db_user.password, dto.password):
            raise RetroException(ErrorCode.INVALID_CREDENTIALS)
        jti = uuid.uuid4()
        payload = {
            "sub": db_user.email,
            "user_id": db_user.id,
            "name": db_user.name,
            "jti": str(jti),
        }

        access_token = Authutils.create_access_token(data=payload)
        refresh_token = str(uuid.uuid4())
        token_list = await self.repo.get_refresh_tokens_user_id(db_user.id)

        if len(token_list) >= 5:
            old_token = await self.repo.revoke_oldest_token(db_user.id)
            expiration_time = timedelta(minutes=settings.ACCESS_TOKEN_EXP_MINS)
            await redis.set(f"blacklist:{old_token.jti}", "1", ex=expiration_time)

        expiration_time = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXP_DAYS
        )

        token = await self.repo.create_refresh_token(
            refresh_token, db_user.id, expiration_time, jti
        )

        return LoginResponse.model_validate(
            {"access_token": access_token, "refresh_token": token.refresh_token}
        )

    @observe("UserService.get_user")
    async def get_user(self, email) -> UserResponse:
        db_user = await self.repo.get_user_by_email(email)
        if db_user == None:
            raise RetroException(ErrorCode.USER_NOT_FOUND)
        logger.info("Get user request")
        return UserResponse.model_validate(db_user)

    async def refresh(self, dto: RefreshRequest, redis: Redis):
        token = await self.repo.get_refresh_token(dto.refresh_token)
        if token == None:
            raise RetroException(ErrorCode.INVALID_REFRESH_TOKEN)

        present = datetime.now(timezone.utc)

        if token.valid_till < present:
            await self.repo.revoke_refresh_token(dto.refresh_token)
            raise RetroException(ErrorCode.INVALID_REFRESH_TOKEN)

        db_user = await self.repo.get_user_by_id(token.user_id)
        if db_user == None:
            raise RetroException(ErrorCode.USER_NOT_FOUND)

        await self.repo.revoke_refresh_token(dto.refresh_token, db_user.id)
        payload = {"sub": db_user.email, "user_id": db_user.id, "name": db_user.name}

        access_token = Authutils.create_access_token(data=payload)
        refresh_token = str(uuid.uuid4())
        token_list = await self.repo.get_refresh_tokens_user_id(db_user.id)

        if len(token_list) >= 5:
            old_token = await self.repo.revoke_oldest_token(db_user.id)
            expiration_time = timedelta(minutes=settings.ACCESS_TOKEN_EXP_MINS)
            await redis.set(f"blacklist:{old_token.jti}", "1", ex=expiration_time)

        expiration_time = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXP_DAYS
        )

        token = await self.repo.create_refresh_token(
            refresh_token, db_user.id, expiration_time
        )

        return LoginResponse.model_validate(
            {"access_token": access_token, "refresh_token": token.refresh_token}
        )
        # check if refresh token is revoked the just raise exception
        # if refresh token is valid then create new token expire that token
        # return both new access and new refresh
        # check refresh token duration

    async def logout_all(self, id: int, redis: Redis):
        # add redis integration and JTI token jwt token tracking for blacklisting and one auth middleeware checking in the redis for each call
        refresh_tokens = await self.repo.revoke_all_by_user_id(id)
        expiration_time = timedelta(minutes=settings.ACCESS_TOKEN_EXP_MINS)
        for token in refresh_tokens:
            await redis.set(f"blacklist:{token.jti}", "1", ex=expiration_time)

        return {"detail": "Logged out all devices sucessfully"}

    async def logout(self, dto: RefreshRequest, id: int, redis: Redis):
        old_token = await self.repo.revoke_refresh_token(dto.refresh_token, id)
        if old_token == None:
            raise RetroException(ErrorCode.INVALID_REFRESH_TOKEN)
        expiration_time = timedelta(minutes=settings.ACCESS_TOKEN_EXP_MINS)
        await redis.set(f"blacklist:{old_token.jti}", "1", ex=expiration_time)
        return {"detail": "Logged out sucessfully"}
