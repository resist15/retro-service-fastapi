from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.model.base import Base, CreatedAtMixin, IDMixin


class PlaybackState(Base, IDMixin, CreatedAtMixin):
    __tablename__ = "playback_state"
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
