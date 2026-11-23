from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.routers.deps import Pagination, get_pagination
from app.schemas.availability import SlotOut
from app.schemas.common import Page, SortOrder
from app.schemas.doctor import DoctorCreate, DoctorOut, DoctorUpdate
from app.services import availability_service, doctor_service

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.post("", response_model=DoctorOut, status_code=201,
             summary="Create a doctor account + profile (ADMIN)")
def create_doctor(data: DoctorCreate, db: Session = Depends(get_db),
                  admin: User = Depends(require_role(Role.ADMIN))):
    return doctor_service.create_doctor(db, admin, data)


@router.get("", response_model=Page[DoctorOut], summary="Search doctors by speciality and name")
def list_doctors(
    speciality: Optional[str] = Query(None, max_length=100, description="Filter: speciality name contains"),
    name: Optional[str] = Query(None, max_length=100, description="Filter: doctor name contains"),
    sort_by: Literal["name", "fee", "experience"] = "name",
    sort_order: SortOrder = "asc",
    paging: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return doctor_service.list_doctors(
        db, speciality, name, sort_by, sort_order, paging.page, paging.size
    )


@router.get("/me", response_model=DoctorOut, summary="My doctor profile (DOCTOR)")
def get_my_profile(db: Session = Depends(get_db), user: User = Depends(require_role(Role.DOCTOR))):
    return doctor_service.get_my_doctor_profile(db, user)


@router.put("/me", response_model=DoctorOut, summary="Update my doctor profile (DOCTOR)")
def update_my_profile(data: DoctorUpdate, db: Session = Depends(get_db),
                      user: User = Depends(require_role(Role.DOCTOR))):
    return doctor_service.update_my_profile(db, user, data)


@router.get("/{doctor_id}", response_model=DoctorOut, summary="Doctor details")
def get_doctor(doctor_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return doctor_service.get_doctor(db, doctor_id)


@router.get("/{doctor_id}/slots", response_model=list[SlotOut],
            summary="A doctor's free slots on a date")
def get_free_slots(doctor_id: int, slot_date: date = Query(..., alias="date"),
                   db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    doctor_service.get_doctor(db, doctor_id)  # 404 if the doctor does not exist
    return availability_service.list_free_slots(db, doctor_id, slot_date)
