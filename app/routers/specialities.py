"""Speciality endpoints."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.routers.deps import Pagination, get_pagination
from app.schemas.common import Page, SortOrder
from app.schemas.speciality import SpecialityCreate, SpecialityOut, SpecialityUpdate
from app.services import speciality_service

router = APIRouter(prefix="/specialities", tags=["Specialities"])


@router.post("", response_model=SpecialityOut, status_code=201, summary="Create a speciality (ADMIN)")
def create_speciality(data: SpecialityCreate, db: Session = Depends(get_db),
                      admin: User = Depends(require_role(Role.ADMIN))):
    return speciality_service.create_speciality(db, admin, data)


@router.get("", response_model=Page[SpecialityOut], summary="List specialities")
def list_specialities(
    name: Optional[str] = Query(None, max_length=100, description="Filter: name contains"),
    sort_by: Literal["name", "id"] = "name",
    sort_order: SortOrder = "asc",
    paging: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return speciality_service.list_specialities(
        db, name, sort_by, sort_order, paging.page, paging.size
    )


@router.put("/{speciality_id}", response_model=SpecialityOut, summary="Rename a speciality (ADMIN)")
def update_speciality(speciality_id: int, data: SpecialityUpdate, db: Session = Depends(get_db),
                      admin: User = Depends(require_role(Role.ADMIN))):
    return speciality_service.update_speciality(db, admin, speciality_id, data)


@router.delete("/{speciality_id}", status_code=204, summary="Delete an unused speciality (ADMIN)")
def delete_speciality(speciality_id: int, db: Session = Depends(get_db),
                      admin: User = Depends(require_role(Role.ADMIN))):
    speciality_service.delete_speciality(db, admin, speciality_id)
    return Response(status_code=204)
