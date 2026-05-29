from fastapi import APIRouter, Depends

from app.dependencies.user import get_current_user_email, get_user_service
from app.schemas.user import UserResponse
from app.service.user import UserService

user_router = APIRouter(tags=["User"], prefix="/user")


@user_router.get("/me", response_model=UserResponse)
async def register(
    user_service: UserService = Depends(get_user_service),
    email: str = Depends(get_current_user_email),
) -> UserResponse:
    return await user_service.get_user(email)
