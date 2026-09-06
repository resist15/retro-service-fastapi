from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends
from fastapi.requests import Request

from app.core.config import settings
from app.dependencies.user import get_user_service
from app.service.user import UserService

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)

google_router = APIRouter(prefix="/auth/google")


@google_router.get("/login")
async def google_login_redirect(request: Request):
    callback_url = request.url_for("callback_google")
    return await oauth.google.authorize_redirect(request, callback_url)


@google_router.get("/callback", name="callback_google")
async def google_callback(
    request: Request, user_service: UserService = Depends(get_user_service)
):
    token = await oauth.google.authorize_access_token(request)
    user = token["userinfo"]
    return dict(user)
