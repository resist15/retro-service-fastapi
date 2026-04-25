from fastapi import APIRouter, Depends

from app.dependencies.user import get_user_service
from app.schemas.user import UserRequest, UserResponse
from app.service.user import UserService

auth_router = APIRouter(tags=["Auth"], prefix="/auth")


@auth_router.post("/register", response_model=UserResponse)
async def register(
    dto: UserRequest, user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await user_service.create_user(dto=dto)
