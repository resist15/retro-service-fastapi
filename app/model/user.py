from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.model.base import Base, CreatedAtMixin, IDMixin, TimestampMixin
from app.utils.enums import AccountStatus, ProviderType, UserRole


class User(Base, IDMixin, TimestampMixin):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    provider_type: Mapped[ProviderType] = mapped_column(nullable=False)

    first_name: Mapped[str] = mapped_column(String(255))

    last_name: Mapped[str] = mapped_column(String(255))

    password: Mapped[str] = mapped_column(
        String(255),
    )

    role: Mapped[UserRole] = mapped_column(nullable=False, default=UserRole.USER)
    acc_status: Mapped[AccountStatus] = mapped_column(
        nullable=False, default=AccountStatus.PENDING
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

    device_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
