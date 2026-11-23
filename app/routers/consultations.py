from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.routers.deps import Pagination, get_pagination
from app.schemas.common import Page, SortOrder
from app.schemas.consultation import ConsultationOut
from app.services import consultation_service

router = APIRouter(prefix="/consultations", tags=["Consultations"])


@router.get("/me", response_model=Page[ConsultationOut], summary="My consultation history (PATIENT)")
def my_consultations(
    doctor_id: Optional[int] = Query(None, gt=0, description="Filter: only this doctor"),
    from_date: Optional[date] = Query(None, description="Filter: appointment date from"),
    to_date: Optional[date] = Query(None, description="Filter: appointment date to"),
    sort_order: SortOrder = "desc",
    paging: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.PATIENT)),
):
    return consultation_service.list_my_consultations(
        db, user, doctor_id, from_date, to_date, sort_order, paging.page, paging.size
    )
