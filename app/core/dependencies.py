from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.db.session import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User
from app.repositories import user_repo


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(token)

    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise UnauthorizedError(
            "Invalid or expired token"
        )

    user = user_repo.get_by_id(
        db,
        user_id
    )

    if user is None or not user.is_active:
        raise UnauthorizedError(
            "Invalid or expired token"
        )

    return user


def require_role(*allowed_roles):
    def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                "You do not have permission to perform this action"
            )

        return current_user

    return role_checker