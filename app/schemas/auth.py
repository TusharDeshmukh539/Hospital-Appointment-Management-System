from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from app.models.enums import Role
from app.schemas.common import PHONE_PATTERN, PersonName, RequestModel, ResponseModel


def check_password_strength(password: str) -> str:
    # require letters and numbers
    if not any(ch.isalpha() for ch in password) or not any(ch.isdigit() for ch in password):
        raise ValueError("password must contain at least one letter and one digit")

    # bcrypt limit
    if len(password.encode("utf-8")) > 72:
        raise ValueError("password is too long")

    return password


class RegisterRequest(RequestModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: PersonName
    phone: Optional[str] = Field(default=None, pattern=PHONE_PATTERN)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return check_password_strength(value)


class TokenResponse(ResponseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class UserOut(ResponseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    role: Role
    is_active: bool
    created_at: datetime