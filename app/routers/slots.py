"""Endpoints that act on one slot (doctor only)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.availability import SlotOut
from app.services import availability_service

router = APIRouter(prefix="/slots", tags=["Slots"])


@router.patch("/{slot_id}/block", response_model=SlotOut, summary="Block one of my FREE slots")
def block_slot(slot_id: int, db: Session = Depends(get_db),
               user: User = Depends(require_role(Role.DOCTOR))):
    return availability_service.block_slot(db, user, slot_id)


@router.patch("/{slot_id}/unblock", response_model=SlotOut, summary="Unblock one of my BLOCKED slots")
def unblock_slot(slot_id: int, db: Session = Depends(get_db),
                 user: User = Depends(require_role(Role.DOCTOR))):
    return availability_service.unblock_slot(db, user, slot_id)
