import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import Request, Response
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
    DeviceSession,
    LoginRequest,
    LoginResponseMessage,
    OAuthLoginRequest,
    RefreshRequest,
    UserRequest,
    UserResponse,
)
from app.utils.auth import Authutils
from app.utils.enums import AccountStatus, ProviderType

logger = get_logger(__name__)


class UserService:
    def __init__(self, repository: UserRepository):
        self.repo = repository

    @observe("UserService.create_user")
    async def create_user(self, dto: UserRequest) -> UserResponse:
        db_user = await self.repo.get_user_by_email(dto.email)
        if db_user is not None:
            if db_user.acc_status is AccountStatus.PENDING:
                raise RetroException(ErrorCode.USER_APPROVAL_PENDING)
            raise RetroException(ErrorCode.USER_ALREADY_EXISTS)
        user_data = dto.model_dump()
        user_data["password"] = Authutils.hash_password(user_data["password"])
        user_data["provider_type"] = ProviderType.NORMAL

        user: User = User(**user_data)
        await self.repo.create_user(user)
        return UserResponse.model_validate(user)

    @observe("UserService.oauth_login")
    async def oauth_login_user(
        self, request: Request, dto: OAuthLoginRequest, redis: Redis
    ):
        db_user: User | None = await self.repo.get_user_by_email(dto.email)
        if db_user is None:
            user_data = dto.model_dump()
            user_data["password"] = ""
            db_user: User = User(**user_data)
            await self.repo.create_user(db_user)

        if db_user is not None and db_user.acc_status is AccountStatus.PENDING:
            return RedirectResponse(
                url=settings.FRONTEND_URL + "/login?error=approval_pending"
            )

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
            "user_type": db_user.role.value,
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

        device_info = Authutils.get_device_info(request)

        token = await self.repo.create_refresh_token(
            refresh_token,
            db_user.id,
            expiration_time,
            refresh_jti,
            device_name=device_info["device_name"],
            user_agent=device_info["user_agent"],
            ip_address=device_info["ip_address"],
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
            expires=access_expiration_time,
            domain=settings.DOMAIN,
        )

        response.set_cookie(
            key="refresh_token",
            value=str(token.refresh_token),
            httponly=True,
            secure=True,
            samesite="lax",
            path="/auth",
            expires=refresh_expiration_time,
            domain=settings.DOMAIN,
        )

        return response

        # return LoginResponse.model_validate(
        #     {"access_token": access_token, "refresh_token": token.refresh_token}
        # )

    @observe("UserService.login_user")
    async def login_user(
        self, response: Response, dto: LoginRequest, redis: Redis, request: Request
    ) -> LoginResponseMessage:
        db_user = await self.repo.get_user_by_email(dto.email)
        if db_user is None:
            raise RetroException(ErrorCode.INVALID_CREDENTIALS)

        if db_user is not None and db_user.acc_status is AccountStatus.PENDING:
            raise RetroException(ErrorCode.USER_APPROVAL_PENDING)

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
            "user_type": db_user.role.value,
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

        device_info = Authutils.get_device_info(request)

        token = await self.repo.create_refresh_token(
            refresh_token,
            db_user.id,
            expiration_time,
            refresh_jti,
            device_name=device_info["device_name"],
            user_agent=device_info["user_agent"],
            ip_address=device_info["ip_address"],
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
            expires=access_expiration_time,
            domain=settings.DOMAIN,
        )

        response.set_cookie(
            key="refresh_token",
            value=str(token.refresh_token),
            httponly=True,
            secure=True,
            samesite="lax",
            path="/auth",
            expires=refresh_expiration_time,
            domain=settings.DOMAIN,
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

    async def refresh(
        self, request: Request, response: Response, dto: RefreshRequest, redis: Redis
    ):

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
            "user_type": db_user.role.value,
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

        device_info = Authutils.get_device_info(request)

        token = await self.repo.create_refresh_token(
            refresh_token,
            db_user.id,
            expiration_time,
            refresh_jti,
            device_name=device_info["device_name"],
            user_agent=device_info["user_agent"],
            ip_address=device_info["ip_address"],
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
            expires=access_expiration_time,
            domain=settings.DOMAIN,
        )

        response.set_cookie(
            key="refresh_token",
            value=str(token.refresh_token),
            httponly=True,
            secure=True,
            samesite="lax",
            path="/auth",
            expires=refresh_expiration_time,
            domain=settings.DOMAIN,
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

    async def get_all_session(
        self, user_id: int, refresh_token: UUID
    ) -> list[DeviceSession]:

        token_list = await self.repo.get_refresh_tokens_user_id(user_id)

        return [
            DeviceSession(
                sid=str(token.jti),
                created_at=token.created_at,
                device_name=token.device_name if token.device_name else "",
                valid_till=token.valid_till,
                user_agent=token.user_agent if token.user_agent else "",
                current=token.refresh_token == refresh_token,
            )
            for token in token_list
        ]

    async def logout_specific(
        self,
        dto: RefreshRequest,
        id: int,
        redis: Redis,
        current_jti: str,
        response: Response,
        session_id: str,
    ):
        token = await self.repo.get_refresh_token_by_jti(
            jti=UUID(session_id), user_id=id
        )

        if token is None:
            raise RetroException(ErrorCode.INVALID_SESSION_ID)

        if token.refresh_token == dto.refresh_token:
            await self.logout(
                dto=dto, id=id, redis=redis, response=response, jti=current_jti
            )

        old_token = await self.repo.revoke_refresh_token_by_jti(UUID(session_id), id)

        if old_token is None:
            raise RetroException(ErrorCode.INVALID_SESSION_ID)

        expiration_time = timedelta(minutes=settings.ACCESS_TOKEN_EXP_MINS)

        await redis.set(
            f"retro-service:{id}:access-blacklist:{token.jti!s}",
            "1",
            ex=expiration_time,
        )
        return {"detail": "Logged out sucessfully"}
