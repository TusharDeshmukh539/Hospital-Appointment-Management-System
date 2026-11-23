from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityOut,
    BlockDateRequest,
    BlockDateResult,
    SlotGenerateRequest,
    SlotGenerateResult,
    SlotOut,
)
from app.services import availability_service

router = APIRouter(prefix="/doctors/me", tags=["Doctor availability & slots"])

doctor_only = require_role(Role.DOCTOR)


@router.post("/availability", response_model=AvailabilityOut, status_code=201,
             summary="Define a weekly availability window")
def add_availability(data: AvailabilityCreate, db: Session = Depends(get_db),
                     user: User = Depends(doctor_only)):
    return availability_service.add_template(db, user, data)


@router.get("/availability", response_model=list[AvailabilityOut],
            summary="List my weekly availability")
def list_availability(db: Session = Depends(get_db), user: User = Depends(doctor_only)):
    return availability_service.list_templates(db, user)


@router.delete("/availability/{template_id}", status_code=204,
               summary="Remove a weekly availability window")
def delete_availability(template_id: int, db: Session = Depends(get_db),
                        user: User = Depends(doctor_only)):
    availability_service.delete_template(db, user, template_id)
    return Response(status_code=204)


@router.post("/slots/generate", response_model=SlotGenerateResult,
             summary="Generate slots from my weekly template for a date range")
def generate_slots(data: SlotGenerateRequest, db: Session = Depends(get_db),
                   user: User = Depends(doctor_only)):
    return availability_service.generate_slots(db, user, data)


@router.get("/slots", response_model=list[SlotOut], summary="My slots (all statuses) on a date")
def list_my_slots(slot_date: date = Query(..., alias="date"), db: Session = Depends(get_db),
                  user: User = Depends(doctor_only)):
    return availability_service.list_my_slots(db, user, slot_date)


@router.post("/slots/block-date", response_model=BlockDateResult,
             summary="Block all FREE slots on a date (e.g. leave day)")
def block_date(data: BlockDateRequest, db: Session = Depends(get_db),
               user: User = Depends(doctor_only)):
    return availability_service.block_date(db, user, data)
