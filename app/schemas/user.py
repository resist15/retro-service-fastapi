from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.schemas.base import Base, IDMixin, TimestampMixin


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
