from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.db.redis import get_redis
from app.dependencies.user import get_user_service
from app.schemas.user import OAuthLoginRequest
from app.service.user import UserService
from app.utils.enums import ProviderType

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)

google_router = APIRouter(tags=["Google"], prefix="/auth/google")


@google_router.get("/login")
async def google_login_redirect(request: Request):
    callback_url = request.url_for("callback_google")
    return await oauth.google.authorize_redirect(request, callback_url)


@google_router.get("/callback", name="callback_google")
async def google_callback(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    redis: Redis = Depends(get_redis),
):
    token = await oauth.google.authorize_access_token(request)

    user = token["userinfo"]

    user_data: OAuthLoginRequest = OAuthLoginRequest(
        email=user["email"],
        first_name=user.get("given_name") or "",
        last_name=user.get("family_name") or "",
        provider_type=ProviderType.GOOGLE,
    )

    return await user_service.oauth_login_user(user_data, redis)
