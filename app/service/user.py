from app.exceptions.custom_exceptions import RetroException
from app.exceptions.errors import ErrorCode
from app.model.user import User
from app.repository.user import UserRepository
from app.schemas.user import LoginRequest, LoginResponse, UserRequest, UserResponse
from app.utils.auth import Authutils


class UserService:
    def __init__(self, repository: UserRepository):
        self.repo = repository

    async def create_user(self, dto: UserRequest) -> UserResponse:
        db_user = await self.repo.get_user_by_email(dto.email)
        if db_user != None:
            raise RetroException(ErrorCode.USER_ALREADY_EXISTS)
        user_data = dto.model_dump()
        user_data["password"] = Authutils.hash_password(user_data["password"])

        user: User = User(**user_data)
        await self.repo.create_user(user)
        return UserResponse.model_validate(user)

    async def login_user(self, dto: LoginRequest) -> LoginResponse:
        db_user = await self.repo.get_user_by_email(dto.email)
        if db_user == None:
            raise RetroException(ErrorCode.INVALID_CREDENTIALS)

        if not Authutils.verify_password(db_user.password, dto.password):
            raise RetroException(ErrorCode.INVALID_CREDENTIALS)

        access_token = Authutils.create_access_token(subject=db_user.email)
        return LoginResponse.model_validate({"access_token": access_token})

    async def get_user(self, email) -> UserResponse:
        db_user = await self.repo.get_user_by_email(email)
        if db_user != None:
            raise RetroException(ErrorCode.USER_NOT_FOUND)
        return UserResponse.model_validate(db_user)
