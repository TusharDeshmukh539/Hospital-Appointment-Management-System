from datetime import date, time, timedelta

from pydantic import Field, model_validator

from app.models.enums import SlotStatus
from app.schemas.common import RequestModel, ResponseModel


MAX_GENERATE_DAYS = 60


class AvailabilityCreate(RequestModel):
    weekday: int = Field(ge=0, le=6)
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
    from_date: date
    to_date: date

    @model_validator(mode="after")
    def check_range(self):
        if self.to_date < self.from_date:
            raise ValueError("to_date must not be before from_date")

        # prevent large slot generation requests
        if (self.to_date - self.from_date) > timedelta(days=MAX_GENERATE_DAYS - 1):
            raise ValueError(f"date range can be at most {MAX_GENERATE_DAYS} days")

        return self


class SlotGenerateResult(ResponseModel):
    created: int
    skipped: int


class BlockDateRequest(RequestModel):
    slot_date: date


class BlockDateResult(ResponseModel):
    blocked: int
    already_booked: int


class SlotOut(ResponseModel):
    id: int
    doctor_id: int
    slot_date: date
    start_time: time
    end_time: time
    status: SlotStatus