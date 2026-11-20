"""Patient endpoints."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.routers.deps import Pagination, get_pagination
from app.schemas.common import Page, SortOrder
from app.schemas.patient import PatientOut, PatientUpdate
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/me", response_model=PatientOut, summary="My patient profile (PATIENT)")
def get_my_profile(db: Session = Depends(get_db), user: User = Depends(require_role(Role.PATIENT))):
    return patient_service.get_my_patient_profile(db, user)


@router.put("/me", response_model=PatientOut, summary="Update my patient profile (PATIENT)")
def update_my_profile(data: PatientUpdate, db: Session = Depends(get_db),
                      user: User = Depends(require_role(Role.PATIENT))):
    return patient_service.update_my_profile(db, user, data)


@router.get("", response_model=Page[PatientOut], summary="List all patients with filters (ADMIN)")
def list_patients(
    name: Optional[str] = Query(None, max_length=100, description="Filter: name contains"),
    gender: Optional[Literal["MALE", "FEMALE", "OTHER"]] = None,
    blood_group: Optional[str] = Query(None, pattern=r"^(A|B|AB|O)[+-]$"),
    sort_by: Literal["name", "date_of_birth", "created_at"] = "name",
    sort_order: SortOrder = "asc",
    paging: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
):
    return patient_service.list_patients(
        db, name, gender, blood_group, sort_by, sort_order, paging.page, paging.size
    )
