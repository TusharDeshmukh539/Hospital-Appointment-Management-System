"""Schemas for patients."""
from datetime import date
from typing import Literal, Optional

from pydantic import Field, field_validator

from app.schemas.common import PHONE_PATTERN, PersonName, RequestModel, ResponseModel


class PatientUpdate(RequestModel):
    """Body of PUT /patients/me - every field is optional."""

    full_name: Optional[PersonName] = None
    phone: Optional[str] = Field(default=None, pattern=PHONE_PATTERN)
    date_of_birth: Optional[date] = None
    gender: Optional[Literal["MALE", "FEMALE", "OTHER"]] = None
    blood_group: Optional[str] = Field(default=None, pattern=r"^(A|B|AB|O)[+-]$")
    address: Optional[str] = Field(default=None, max_length=255)

    @field_validator("date_of_birth")
    @classmethod
    def dob_must_be_realistic(cls, value: Optional[date]) -> Optional[date]:
        if value is not None and (value > date.today() or value.year < 1900):
            raise ValueError("date_of_birth must be a past date after 1900")
        return value


class PatientOut(ResponseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]
    blood_group: Optional[str]
    address: Optional[str]
