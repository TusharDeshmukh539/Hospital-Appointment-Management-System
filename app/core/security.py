from datetime import timedelta
from functools import lru_cache

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.utils import utc_now
from app.db.session import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User
from app.repositories import user_repo


@lru_cache
def _get_password_context() -> CryptContext:
    return CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=get_settings().BCRYPT_ROUNDS
    )


def hash_password(plain_password: str) -> str:
    return _get_password_context().hash(plain_password)


def verify_password(
    plain_password: str,
    password_hash: str
) -> bool:
    return _get_password_context().verify(
        plain_password,
        password_hash
    )


def create_access_token(
    user_id: int,
    role: str
) -> str:
    settings = get_settings()

    expires_at = utc_now() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict:
    settings = get_settings()

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)