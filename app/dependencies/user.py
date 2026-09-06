from types import SimpleNamespace

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.redis import get_redis
from app.db.session import get_db
from app.model.user import User
from app.observability.decorators import observe
from app.observability.logging import bind_request_context
from app.repository.user import UserRepository
from app.service.user import UserService


def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session=session)


def get_user_service(
    repository: UserRepository = Depends(get_user_repo),
) -> UserService:
    return UserService(repository=repository)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@observe("Security.verify_token")
async def get_current_user_email(
    token: str = Depends(oauth2_scheme), redis: Redis = Depends(get_redis)
) -> SimpleNamespace:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        user_id = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    jti = payload.get("jti")

    if await redis.exists(f"retro-service:{user_id}:access-blacklist:{jti}"):
        raise credentials_exception

    key = f"retro-service:{user_id}:token-version"

    version = payload.get("version")
    try:
        token_version = int(version)
    except TypeError, ValueError:
        raise credentials_exception

    version_from_redis = await redis.get(key)

    if version_from_redis is None:
        raise credentials_exception

    if token_version != int(version_from_redis):
        raise credentials_exception

    bind_request_context(email=email, user_id=user_id)
    return SimpleNamespace(id=user_id, email=email, auth_token=payload)


async def get_current_user(
    user: SimpleNamespace = Depends(get_current_user_email),
    repo: UserRepository = Depends(get_user_repo),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    db_user = await repo.get_user_by_email(user.email)
    if db_user is None:
        raise credentials_exception
    return db_user
