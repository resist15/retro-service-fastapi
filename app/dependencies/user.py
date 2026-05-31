import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.model.user import User
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


async def get_current_user_email(
    token: str = Depends(oauth2_scheme),
) -> str:
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
    bind_request_context(email=email, user_id=user_id)
    return email


async def get_current_user(
    email: str = Depends(get_current_user_email),
    repo: UserRepository = Depends(get_user_repo),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    db_user = await repo.get_user_by_email(email)
    if db_user is None:
        raise credentials_exception
    return db_user
