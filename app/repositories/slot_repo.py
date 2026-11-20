"""Database access for the slots table.

The most important functions here are the status changes (claim/release/block/unblock).
Each one is a single UPDATE ... WHERE status = <expected status>.
The database applies it atomically, so two people can never claim the same FREE slot:
the first UPDATE changes 1 row, the second finds status != FREE and changes 0 rows.
"""
from datetime import date
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.slot import Slot
from app.models.enums import SlotStatus


def get_by_id(db: Session, slot_id: int) -> Optional[Slot]:
    return db.get(Slot, slot_id)


def list_for_doctor_on_date(db: Session, doctor_id: int, slot_date: date,
                            status: Optional[str] = None) -> list[Slot]:
    query = select(Slot).where(Slot.doctor_id == doctor_id, Slot.slot_date == slot_date)
    if status:
        query = query.where(Slot.status == status)
    return list(db.scalars(query.order_by(Slot.start_time)).all())


def list_in_range(db: Session, doctor_id: int, from_date: date, to_date: date) -> list[Slot]:
    query = select(Slot).where(
        Slot.doctor_id == doctor_id, Slot.slot_date >= from_date, Slot.slot_date <= to_date
    )
    return list(db.scalars(query).all())


def add_many(db: Session, slots: list[Slot]) -> None:
    db.add_all(slots)
    db.flush()


def _change_status(db: Session, slot_id: int, from_status: SlotStatus, to_status: SlotStatus) -> bool:
    """Change the status only if it currently equals `from_status`.

    Returns True if the slot was changed, False if it was in a different status.
    """
    result = db.execute(
        update(Slot)
        .where(Slot.id == slot_id, Slot.status == from_status.value)
        .values(status=to_status.value)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount == 1


def claim_slot(db: Session, slot_id: int) -> bool:
    """FREE -> BOOKED. Returns False if somebody else got the slot first."""
    return _change_status(db, slot_id, SlotStatus.FREE, SlotStatus.BOOKED)


def release_slot(db: Session, slot_id: int) -> bool:
    """BOOKED -> FREE (used by cancel and reschedule)."""
    return _change_status(db, slot_id, SlotStatus.BOOKED, SlotStatus.FREE)


def block_slot(db: Session, slot_id: int) -> bool:
    """FREE -> BLOCKED."""
    return _change_status(db, slot_id, SlotStatus.FREE, SlotStatus.BLOCKED)


def unblock_slot(db: Session, slot_id: int) -> bool:
    """BLOCKED -> FREE."""
    return _change_status(db, slot_id, SlotStatus.BLOCKED, SlotStatus.FREE)


def block_free_slots_on_date(db: Session, doctor_id: int, slot_date: date) -> int:
    """Block every FREE slot of the doctor on that date. Returns how many were blocked."""
    result = db.execute(
        update(Slot)
        .where(
            Slot.doctor_id == doctor_id,
            Slot.slot_date == slot_date,
            Slot.status == SlotStatus.FREE.value,
        )
        .values(status=SlotStatus.BLOCKED.value)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount


def count_with_status_on_date(db: Session, doctor_id: int, slot_date: date, status: SlotStatus) -> int:
    query = select(func.count(Slot.id)).where(
        Slot.doctor_id == doctor_id, Slot.slot_date == slot_date, Slot.status == status.value
    )
    return db.scalar(query) or 0
