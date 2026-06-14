import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRequest(BaseModel):
    name: Annotated[
        str, Field(min_length=2, max_length=50, description="User full name")
    ]

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        if not value.replace(" ", "").isalpha():
            raise ValueError("Name must contain only letters and spaces")
        return value

    email: EmailStr

    password: Annotated[
        str, Field(min_length=8, max_length=128, description="Strong password")
    ]

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character")
        return value

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: UUID

    model_config = {"from_attributes": True}

class RefreshRequest(BaseModel):
    refresh_token: UUID