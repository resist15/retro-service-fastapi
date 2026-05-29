from alembic.util import status
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.model.user import User
from app.repository.user import UserRepository
from app.service.user import UserService


def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session=session)


def get_user_service(
    repository: UserRepository = Depends(get_user_repo),
) -> UserService:
    return UserService(repository=repository)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user_email(
    token: str = Depends(oauth2_scheme),
) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ENCODING_ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return email


async def get_current_user(
    email: str = Depends(get_current_user_email),
    repo: UserRepository = Depends(get_user_repo),
) -> User:
    db_user = await repo.get_user_by_email(email)
    return db_user
