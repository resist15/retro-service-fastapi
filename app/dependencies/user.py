from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repository.user import UserRepository
from app.service.user import UserService


def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session=session)


def get_user_service(
    repository: UserRepository = Depends(get_user_repo),
) -> UserService:
    return UserService(repository=repository)
