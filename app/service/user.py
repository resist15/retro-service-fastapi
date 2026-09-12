import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Response
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis

from app.core.config import settings
from app.exceptions.custom_exceptions import RetroException
from app.exceptions.errors import ErrorCode
from app.model.user import RefreshToken, User
from app.observability.decorators import observe
from app.observability.logging import get_logger
from app.repository.user import UserRepository
from app.schemas.user import (
    LoginRequest,
    LoginResponseMessage,
    OAuthLoginRequest,
    RefreshRequest,
    UserRequest,
    UserResponse,
)
from app.utils.auth import Authutils
from app.utils.enums import ProviderType

logger = get_logger(__name__)


class UserService:
    def __init__(self, repository: UserRepository):
        self.repo = repository

    @observe("UserService.create_user")
    async def create_user(self, dto: UserRequest) -> UserResponse:
        db_user = await self.repo.get_user_by_email(dto.email)
        if db_user is not None:
            raise RetroException(ErrorCode.USER_ALREADY_EXISTS)
        user_data = dto.model_dump()
        user_data["password"] = Authutils.hash_password(user_data["password"])
        user_data["provider_type"] = ProviderType.NORMAL

        user: User = User(**user_data)
        await self.repo.create_user(user)
        return UserResponse.model_validate(user)

    @observe("UserService.oauth_login")
    async def oauth_login_user(self, dto: OAuthLoginRequest, redis: Redis):
        db_user: User | None = await self.repo.get_user_by_email(dto.email)
        if db_user is None:
            user_data = dto.model_dump()
            user_data["password"] = ""
            db_user: User = User(**user_data)
            await self.repo.create_user(db_user)

        access_jti = uuid.uuid4()

        version = await redis.get(f"retro-service:{db_user.id}:token-version")

        if version is None:
            await redis.set(f"retro-service:{db_user.id}:token-version", 1)
            version = 1
        else:
            version = int(version)

        name = db_user.first_name + " " + db_user.last_name

        access_payload = {
            "user_id": db_user.id,
            "name": name,
            "sub": db_user.email,
            "jti": str(access_jti),
            "version": version,
        }

        access_token = Authutils.create_access_token(data=access_payload)

        refresh_token = uuid.uuid4()
        refresh_jti = uuid.uuid4()

        token_list = await self.repo.get_refresh_tokens_user_id(db_user.id)

        if len(token_list) >= 5:
            old_token = await self.repo.revoke_oldest_token(db_user.id)
            if old_token is None:
                raise RetroException(ErrorCode.INTERNAL_SERVER_ERROR)

        expiration_time = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXP_DAYS
        )

        token = await self.repo.create_refresh_token(
            refresh_token, db_user.id, expiration_time, refresh_jti
        )

        response = RedirectResponse(url=settings.FRONTEND_URL + "/home")

        refresh_expiration_time = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXP_DAYS
        )
        access_expiration_time = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXP_MINS
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            expires=refresh_expiration_time,
        )

        response.set_cookie(
            key="refresh_token",
            value=str(token.refresh_token),
            httponly=True,
            secure=True,
            samesite="lax",
            path="/auth",
            expires=access_expiration_time,
        )

        return response

        # return LoginResponse.model_validate(
        #     {"access_token": access_token, "refresh_token": token.refresh_token}
        # )

    @observe("UserService.login_user")
    async def login_user(
        self, response: Response, dto: LoginRequest, redis: Redis
    ) -> LoginResponseMessage:
        db_user = await self.repo.get_user_by_email(dto.email)
        if db_user is None:
            raise RetroException(ErrorCode.INVALID_CREDENTIALS)

        if not Authutils.verify_password(db_user.password, dto.password):
            raise RetroException(ErrorCode.INVALID_CREDENTIALS)

        access_jti = uuid.uuid4()

        version = await redis.get(f"retro-service:{db_user.id}:token-version")

        if version is None:
            await redis.set(f"retro-service:{db_user.id}:token-version", 1)
            version = 1
        else:
            version = int(version)

        name = db_user.first_name + " " + db_user.last_name

        access_payload = {
            "user_id": db_user.id,
            "name": name,
            "sub": db_user.email,
            "jti": str(access_jti),
            "version": version,
        }

        access_token = Authutils.create_access_token(data=access_payload)

        refresh_token = uuid.uuid4()
        refresh_jti = uuid.uuid4()

        token_list = await self.repo.get_refresh_tokens_user_id(db_user.id)

        if len(token_list) >= 5:
            old_token = await self.repo.revoke_oldest_token(db_user.id)
            if old_token is None:
                raise RetroException(ErrorCode.INTERNAL_SERVER_ERROR)

        expiration_time = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXP_DAYS
        )

        token = await self.repo.create_refresh_token(
            refresh_token, db_user.id, expiration_time, refresh_jti
        )

        refresh_expiration_time = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXP_DAYS
        )
        access_expiration_time = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXP_MINS
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            expires=refresh_expiration_time,
        )

        response.set_cookie(
            key="refresh_token",
            value=str(token.refresh_token),
            httponly=True,
            secure=True,
            samesite="lax",
            path="/auth",
            expires=access_expiration_time,
        )

        return LoginResponseMessage(detail="Login successful")
        # return LoginResponse.model_validate(
        #     {"access_token": access_token, "refresh_token": token.refresh_token}
        # )

    @observe("UserService.get_user")
    async def get_user(self, email) -> UserResponse:
        db_user = await self.repo.get_user_by_email(email)
        if db_user == None:
            raise RetroException(ErrorCode.USER_NOT_FOUND)
        logger.info("Get user request")
        return UserResponse.model_validate(db_user)

    async def refresh(self, response: Response, dto: RefreshRequest, redis: Redis):

        token: RefreshToken | None = await self.repo.get_refresh_token(
            dto.refresh_token
        )

        if token is None:
            raise RetroException(ErrorCode.INVALID_REFRESH_TOKEN)

        if token.revoked is True:
            raise RetroException(ErrorCode.INVALID_REFRESH_TOKEN)

        present = datetime.now(UTC)

        if token.valid_till < present:
            await self.repo.revoke_refresh_token(dto.refresh_token)
            raise RetroException(ErrorCode.INVALID_REFRESH_TOKEN)

        db_user = await self.repo.get_user_by_id(token.user_id)
        if db_user is None:
            raise RetroException(ErrorCode.USER_NOT_FOUND)

        await self.repo.revoke_refresh_token(dto.refresh_token, db_user.id)

        key = f"retro-service:{db_user.id}:token-version"

        version = await redis.get(key)

        if version is None:
            await redis.set(key, 1)
            version = 1
        else:
            version = int(version)

        access_jti = uuid.uuid4()

        name = db_user.first_name + " " + db_user.last_name

        access_payload = {
            "user_id": db_user.id,
            "name": name,
            "sub": db_user.email,
            "jti": str(access_jti),
            "version": version,
        }

        access_token = Authutils.create_access_token(data=access_payload)
        refresh_token = uuid.uuid4()
        refresh_jti = uuid.uuid4()

        token_list = await self.repo.get_refresh_tokens_user_id(db_user.id)

        if len(token_list) >= 5:
            old_token = await self.repo.revoke_oldest_token(db_user.id)
            if old_token is None:
                raise RetroException(ErrorCode.INTERNAL_SERVER_ERROR)

        expiration_time = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXP_DAYS
        )

        token = await self.repo.create_refresh_token(
            refresh_token, db_user.id, expiration_time, refresh_jti
        )

        refresh_expiration_time = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXP_DAYS
        )
        access_expiration_time = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXP_MINS
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            expires=refresh_expiration_time,
        )

        response.set_cookie(
            key="refresh_token",
            value=str(token.refresh_token),
            httponly=True,
            secure=True,
            samesite="lax",
            path="/auth",
            expires=access_expiration_time,
        )

        return LoginResponseMessage(detail="Refreshed Successfully")
        # return LoginResponse.model_validate(
        #     {"access_token": access_token, "refresh_token": token.refresh_token}
        # )

    async def logout_all(self, id: int, redis: Redis, response: Response):
        await self.repo.revoke_all_by_user_id(id)
        await redis.incr(f"retro-service:{id}:token-version")
        response.delete_cookie(
            key="refresh_token",
            path="/auth",
        )
        response.delete_cookie(
            key="access_token",
            path="/",
        )
        return {"detail": "Logged out all devices sucessfully"}

    async def logout(
        self, dto: RefreshRequest, id: int, redis: Redis, jti: str, response: Response
    ):
        old_token = await self.repo.revoke_refresh_token(dto.refresh_token, id)
        if old_token is None:
            raise RetroException(ErrorCode.INVALID_REFRESH_TOKEN)
        expiration_time = timedelta(minutes=settings.ACCESS_TOKEN_EXP_MINS)
        await redis.set(
            f"retro-service:{id}:access-blacklist:{jti}", "1", ex=expiration_time
        )
        response.delete_cookie(
            key="refresh_token",
            path="/auth",
        )
        response.delete_cookie(
            key="access_token",
            path="/",
        )
        return {"detail": "Logged out sucessfully"}
