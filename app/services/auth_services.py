from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.enums import Role
from app.models.patient import Patient
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    TokenResponse,
)


class AuthService:

    @staticmethod
    def get_user_by_email(
        db: Session,
        email: str,
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.email == email.lower())
            .first()
        )

    @staticmethod
    def register_patient(
        db: Session,
        payload: RegisterRequest,
    ) -> User:

        existing_user = AuthService.get_user_by_email(
            db,
            payload.email,
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            )

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
            role=Role.PATIENT.value,
        )

        db.add(user)
        db.flush()

        patient = Patient(
            user_id=user.id,
        )

        db.add(patient)

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
    ) -> TokenResponse:

        user = AuthService.get_user_by_email(
            db,
            email,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        token = create_access_token(
            user_id=user.id,
            role=user.role,
        )

        return TokenResponse(
            access_token=token,
            expires_in_minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        )