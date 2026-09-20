from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Request
from pwdlib import PasswordHash
from user_agents.parsers import parse

from app.core.config import settings
from app.observability.decorators import observe

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

pwd_context = PasswordHash.recommended()


class Authutils:
    @staticmethod
    def create_access_token(data: dict) -> str:
        expiration_time = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXP_MINS
        )
        payload = {
            **data,
            "exp": expiration_time,
            "iat": datetime.now(UTC),
        }
        token = jwt.encode(
            payload=payload,
            key=settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return token

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    @observe("AuthUtils.verify_password")
    def verify_password(db_password: str, input_password) -> bool:
        return pwd_context.verify(input_password, db_password)

    @staticmethod
    def get_device_info(request: Request) -> dict:
        user_agent_string = request.headers.get("user-agent", "")
        user_agent = parse(user_agent_string)

        device_name = f"{user_agent.browser.family} on {user_agent.os.family}"

        return {
            "device_name": device_name,
            "user_agent": user_agent_string,
            "ip_address": request.client.host if request.client else None,
        }
