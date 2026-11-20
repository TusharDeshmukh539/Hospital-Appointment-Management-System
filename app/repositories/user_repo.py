"""Database access for the users table. No business rules here."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalar(select(User).where(User.email == email.lower()))


def create(db: Session, email: str, password_hash: str, full_name: str,
           phone: Optional[str], role: str) -> User:
    user = User(
        email=email.lower(),
        password_hash=password_hash,
        full_name=full_name,
        phone=phone,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()  # sends the INSERT now so that user.id is filled in
    return user
