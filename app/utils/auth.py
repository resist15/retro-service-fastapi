from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

pwd_context = PasswordHash.recommended()


class Authutils:
    @staticmethod
    def create_access_token(subject: str) -> str:
        expiration_time = datetime.now(timezone.utc) + timedelta(
            days=settings.ACCESS_TOKEN_EXP_DAYS
        )
        payload = {
            "sub": subject,
            "exp": expiration_time,
            "iat": datetime.now(timezone.utc),
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
    def verify_password(db_password: str, input_password) -> bool:
        return pwd_context.verify(input_password, db_password)
