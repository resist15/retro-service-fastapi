from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.user import RefreshToken, User


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

    async def get_refresh_token(self, token: UUID) -> RefreshToken:
        q = select(RefreshToken).where(RefreshToken.refresh_token == token)
        result = await self.db.execute(q)
        refresh_token = result.scalar_one_or_none()
        return refresh_token

    async def create_refresh_token(
        self, token: UUID, user_id: int, expiration_time: datetime
    ) -> RefreshToken:
        data = {
            "user_id": user_id,
            "refresh_token": token,
            "valid_till": expiration_time,
        }
        new_token = RefreshToken(**data)
        self.db.add(new_token)
        await self.db.flush()
        await self.db.refresh(new_token)
        return new_token

    async def revoke_oldest_token(self, user_id: int) -> RefreshToken:
        q1 = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked == False)
            .order_by(RefreshToken.created_at)
            .limit(1)
        )
        r1 = await self.db.execute(q1)
        old_token = r1.scalar_one_or_none()
        if not old_token:
            return None

        old_token.revoked = True
        await self.db.flush()
        await self.db.refresh(old_token)
        return old_token

    async def get_refresh_tokens_user_id(self, user_id: int) -> list[RefreshToken]:
        q = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked == False)
        )
        result = await self.db.execute(q)
        refresh_token_list = result.scalars().all()
        return refresh_token_list

    async def revoke_refresh_token(self, token: UUID, user_id: int | None = None):
        if user_id == None:
            q = (
                select(RefreshToken)
                .where(RefreshToken.refresh_token == token)
                .where(RefreshToken.revoked == False)
            )
        else:
            q = (
                select(RefreshToken)
                .where(RefreshToken.user_id == user_id)
                .where(RefreshToken.refresh_token == token)
                .where(RefreshToken.revoked == False)
            )
        result = await self.db.execute(q)
        db_token = result.scalar_one_or_none()
        if db_token == None:
            return None

        db_token.revoked = True
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(db_token)
        print(db_token.revoked)
        return db_token

    async def revoke_all_by_user_id(self, user_id: int):
        q = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked == False)
        )
        result = await self.db.execute(q)
        refresh_token_list = result.scalars().all()
        
        if(refresh_token_list.count < 0):
            return
        
        for token in refresh_token_list:
            token.revoked = True

        await self.db.flush()
        await self.db.commit()
        return