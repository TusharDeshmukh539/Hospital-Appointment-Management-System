from datetime import timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)

from app.core.utils import utc_now
from app.models.enums import Role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash : str) -> bool:

    return pwd_context.verify(plain_password, password_hash)

def create_access_token(
        user_id: int,
        role: Role,
) -> str:
    """
    Create a JWT access token for a user.
    
    """

    expire = utc_now() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "role": role.value,   
        "exp": expire
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(
        token: str
) -> dict:
    """
    Decode a JWT token and return the payload.
    
    """

    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])