"""Admin reports."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.report import DoctorLoadItem, NoShowRateReport, SpecialityDemandItem
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports (admin)"])

admin_only = require_role(Role.ADMIN)

# The optional filters shared by all reports (slot date range).
FROM_DATE = Query(None, description="Only count appointments with slot date >= this")
TO_DATE = Query(None, description="Only count appointments with slot date <= this")


@router.get("/doctor-load", response_model=list[DoctorLoadItem],
            summary="Appointments per doctor, by status (ADMIN)")
def doctor_load(from_date: Optional[date] = FROM_DATE, to_date: Optional[date] = TO_DATE,
                db: Session = Depends(get_db), _admin: User = Depends(admin_only)):
    return report_service.doctor_load(db, from_date, to_date)


@router.get("/no-show-rate", response_model=NoShowRateReport,
            summary="No-show rate overall and per doctor (ADMIN)")
def no_show_rate(from_date: Optional[date] = FROM_DATE, to_date: Optional[date] = TO_DATE,
                 db: Session = Depends(get_db), _admin: User = Depends(admin_only)):
    return report_service.no_show_rate(db, from_date, to_date)


@router.get("/speciality-demand", response_model=list[SpecialityDemandItem],
            summary="Appointments per speciality (ADMIN)")
def speciality_demand(from_date: Optional[date] = FROM_DATE, to_date: Optional[date] = TO_DATE,
                      db: Session = Depends(get_db), _admin: User = Depends(admin_only)):
    return report_service.speciality_demand(db, from_date, to_date)
