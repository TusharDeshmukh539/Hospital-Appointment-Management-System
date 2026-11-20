"""Business logic for the admin reports."""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories import report_repo


def _no_show_rate(completed: int, no_show: int) -> float:
    """Percent of finished appointments where the patient did not come."""
    finished = completed + no_show
    if finished == 0:
        return 0.0  # avoid dividing by zero
    return round(no_show / finished * 100, 2)


def doctor_load(db: Session, from_date: Optional[date], to_date: Optional[date]) -> list[dict]:
    rows = report_repo.doctor_load(db, from_date, to_date)
    for row in rows:
        row["no_show_rate"] = _no_show_rate(row["completed"], row["no_show"])
    return rows


def no_show_rate(db: Session, from_date: Optional[date], to_date: Optional[date]) -> dict:
    rows = doctor_load(db, from_date, to_date)
    total_completed = sum(row["completed"] for row in rows)
    total_no_show = sum(row["no_show"] for row in rows)
    return {
        "overall_no_show_rate": _no_show_rate(total_completed, total_no_show),
        "doctors": rows,
    }


def speciality_demand(db: Session, from_date: Optional[date], to_date: Optional[date]) -> list[dict]:
    return report_repo.speciality_demand(db, from_date, to_date)
