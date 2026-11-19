"""Schemas for appointments."""
from datetime import date, datetime, time
from typing import Literal, Optional

from pydantic import Field

from app.models.enums import AppointmentStatus
from app.schemas.common import RequestModel, ResponseModel

class AppointmentCreate(RequestModel):
    """Body of POST /appointments."""

    slot_id: int = Field(gt=0)
    reason: Optional[str] = Field(default=None, max_length=255)


class AppointmentReschedule(RequestModel):
    """Body of PATCH /appointments/{id}/reschedule."""

    new_slot_id: int = Field(gt=0)


class AppointmentStatusUpdate(RequestModel):
    """Body of PATCH /appointments/{id}/status - a doctor can only set these two."""

    status: Literal["COMPLETED", "NO_SHOW"]


class AppointmentOut(ResponseModel):
    """Appointment details. It never contains clinical data (diagnosis etc.)."""

    id: int
    slot_id: int
    doctor_id: int
    patient_id: int
    doctor_name: str
    patient_name: str
    slot_date: date
    start_time: time
    end_time: time
    status: AppointmentStatus
    reason: Optional[str]
    booked_at: datetime
    cancelled_at: Optional[datetime]
