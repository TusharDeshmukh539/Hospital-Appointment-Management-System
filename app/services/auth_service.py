"""Business logic for registration, login and user (de)activation.

Services contain the business rules. They never touch HTTP objects.
"""
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import audit_log
from app.core.security import create_access_token, hash_password, verify_password
from app.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.models.enums import Role
from app.models.user import User
from app.repositories import patient_repo, user_repo
from app.schemas.auth import RegisterRequest


def register_patient(db: Session, data: RegisterRequest) -> User:
    """A visitor registers: we create a users row (role PATIENT) + an empty patient profile."""
    if user_repo.get_by_email(db, data.email):
        raise ConflictError("An account with this email already exists")

    user = user_repo.create(
        db,
        email=data.email,
        password_hash=hash_password(data.password),  # only the hash is stored
        full_name=data.full_name,
        phone=data.phone,
        role=Role.PATIENT.value,
    )
    patient_repo.create(db, user_id=user.id)
    db.commit()

    audit_log("auth.register", user_id=user.id, role=user.role)
    return user


def login(db: Session, email: str, password: str, ip_address: str) -> dict:
    """Check the credentials and return a JWT access token."""
    user = user_repo.get_by_email(db, email)

    # Same error for "unknown email" and "wrong password" so attackers
    # cannot find out which emails are registered.
    if user is None or not verify_password(password, user.password_hash):
        audit_log("auth.login_failed", user_id=user.id if user else None, email=email, ip=ip_address)
        raise UnauthorizedError("Incorrect email or password")

    if not user.is_active:
        audit_log("auth.login_blocked_inactive", user_id=user.id, ip=ip_address)
        raise ForbiddenError("This account has been deactivated")

    token = create_access_token(user_id=user.id, role=user.role)
    audit_log("auth.login_success", user_id=user.id, ip=ip_address)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": get_settings().ACCESS_TOKEN_EXPIRE_MINUTES,
    }


def set_user_active(db: Session, admin: User, user_id: int, active: bool) -> User:
    """Admin activates or deactivates (soft delete) a user account."""
    user = user_repo.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User not found")
    if user.id == admin.id and not active:
        raise ConflictError("You cannot deactivate your own account")

    user.is_active = active
    db.commit()

    audit_log("user.activate" if active else "user.deactivate", user_id=admin.id, target_user_id=user.id)
    return user
