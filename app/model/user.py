from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.model.base import Base, CreatedAtMixin, IDMixin, TimestampMixin


class User(Base, IDMixin, TimestampMixin):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
    )

    password: Mapped[str] = mapped_column(
        String(255),
    )


class RefreshToken(Base, IDMixin, CreatedAtMixin):
    __tablename__ = "refresh_tokens"
    refresh_token: Mapped[UUID] = mapped_column(
        Uuid,
        nullable=False,
    )
    valid_till: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    jti: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
