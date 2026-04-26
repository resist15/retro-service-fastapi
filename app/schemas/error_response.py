from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    message: str = Field(...)
    details: list[ErrorDetail] | None = None
    status_code: int
    path: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
