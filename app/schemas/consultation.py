"""Schemas for consultations (clinical records)."""
from datetime import date, datetime
from typing import Optional

from pydantic import Field, field_validator

from app.schemas.common import RequestModel, ResponseModel


class ConsultationCreate(RequestModel):
    """Body of POST /appointments/{id}/consultation."""

    diagnosis: str = Field(min_length=1, max_length=5000)
    prescription: str = Field(min_length=1, max_length=5000)
    notes: Optional[str] = Field(default=None, max_length=5000)
    follow_up_date: Optional[date] = None

    @field_validator("follow_up_date")
    @classmethod
    def follow_up_in_future(cls, value: Optional[date]) -> Optional[date]:
        if value is not None and value < date.today():
            raise ValueError("follow_up_date cannot be in the past")
        return value


class ConsultationOut(ResponseModel):
    id: int
    appointment_id: int
    doctor_name: str
    appointment_date: date
    diagnosis: str
    prescription: str
    notes: Optional[str]
    follow_up_date: Optional[date]
    created_at: datetime
