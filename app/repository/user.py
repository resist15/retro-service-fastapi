from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> User:
        q = select(User).where(User.email == email)
        result = await self.db.execute(q)
        user = result.scalar_one_or_none()
        return user

    async def get_user_by_id(self, id: int) -> User:
        q = select(User).where(User.id == id)
        result = await self.db.execute(q)
        user = result.scalar_one_or_none()
        return user
