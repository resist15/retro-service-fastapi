from app.exceptions.custom_exceptions import RetroException
from app.exceptions.errors import ErrorCode
from app.model.user import User
from app.repository.user import UserRepository
from app.schemas.user import UserRequest, UserResponse


class UserService:
    def __init__(self, repository: UserRepository):
        self.repo = repository

    async def create_user(self, dto: UserRequest) -> UserResponse:
        db_user = await self.repo.get_user_by_email(dto.email)
        if db_user != None:
            raise RetroException(ErrorCode.USER_ALREADY_EXISTS)
        user: User = User(**dto.model_dump())
        await self.repo.create_user(user)
        return UserResponse.model_validate(user)
