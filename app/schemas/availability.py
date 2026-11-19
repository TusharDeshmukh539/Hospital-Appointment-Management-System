"""Schemas for weekly availability and slots."""
from datetime import date, time, timedelta

from pydantic import Field, model_validator

from app.models.enums import SlotStatus
from app.schemas.common import RequestModel, ResponseModel

MAX_GENERATE_DAYS = 60  # slots can be generated for at most 60 days at once


class AvailabilityCreate(RequestModel):
    """Body of POST /doctors/me/availability."""

    weekday: int = Field(ge=0, le=6, description="0 = Monday ... 6 = Sunday")
    start_time: time
    end_time: time
    slot_minutes: int = Field(default=30, ge=5, le=240)

    @model_validator(mode="after")
    def check_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time")
        return self


class AvailabilityOut(ResponseModel):
    id: int
    doctor_id: int
    weekday: int
    start_time: time
    end_time: time
    slot_minutes: int


class SlotGenerateRequest(RequestModel):
    """Body of POST /doctors/me/slots/generate."""

    from_date: date
    to_date: date

    @model_validator(mode="after")
    def check_range(self):
        if self.to_date < self.from_date:
            raise ValueError("to_date must not be before from_date")
        if (self.to_date - self.from_date) > timedelta(days=MAX_GENERATE_DAYS - 1):
            raise ValueError(f"Date range can be at most {MAX_GENERATE_DAYS} days")
        return self


class SlotGenerateResult(ResponseModel):
    created: int  # new slots saved
    skipped: int  # slots skipped because they already exist / would overlap


class BlockDateRequest(RequestModel):
    """Body of POST /doctors/me/slots/block-date."""

    slot_date: date


class BlockDateResult(ResponseModel):
    blocked: int  # FREE slots that were blocked
    already_booked: int  # BOOKED slots that could not be blocked


class SlotOut(ResponseModel):
    id: int
    doctor_id: int
    slot_date: date
    start_time: time
    end_time: time
    status: SlotStatus
