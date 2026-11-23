from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.auth import UserOut
from app.services import auth_service

router = APIRouter(prefix="/users", tags=["Users (admin)"])


@router.patch("/{user_id}/deactivate", response_model=UserOut,
              summary="Deactivate a user so they can no longer log in")
def deactivate_user(user_id: int, db: Session = Depends(get_db),
                    admin: User = Depends(require_role(Role.ADMIN))):
    return auth_service.set_user_active(db, admin, user_id, active=False)


@router.patch("/{user_id}/activate", response_model=UserOut, summary="Re-activate a user")
def activate_user(user_id: int, db: Session = Depends(get_db),
                  admin: User = Depends(require_role(Role.ADMIN))):
    return auth_service.set_user_active(db, admin, user_id, active=True)
