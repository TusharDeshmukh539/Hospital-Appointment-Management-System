"""Schemas for doctors."""
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import EmailStr, Field, StringConstraints, field_validator

from app.schemas.auth import check_password_strength
from app.schemas.common import PHONE_PATTERN, PersonName, RequestModel, ResponseModel

RegistrationNo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50)]
Qualification = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)]
# Money: max 12 digits in total, 2 after the decimal point, never negative.
Fee = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class DoctorCreate(RequestModel):
    """Body of POST /doctors (ADMIN): creates the login account AND the doctor profile."""

    # login details
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: PersonName
    phone: Optional[str] = Field(default=None, pattern=PHONE_PATTERN)
    # doctor profile
    speciality_id: int = Field(gt=0)
    registration_no: RegistrationNo
    qualification: Qualification
    experience_years: int = Field(ge=0, le=70)
    consultation_fee: Fee

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return check_password_strength(value)


class DoctorUpdate(RequestModel):
    """Body of PUT /doctors/me - every field is optional (send only what changes)."""

    speciality_id: Optional[int] = Field(default=None, gt=0)
    qualification: Optional[Qualification] = None
    experience_years: Optional[int] = Field(default=None, ge=0, le=70)
    consultation_fee: Optional[Fee] = None


class DoctorOut(ResponseModel):
    id: int
    full_name: str
    speciality_id: int
    speciality_name: str
    registration_no: str
    qualification: str
    experience_years: int
    consultation_fee: Decimal
