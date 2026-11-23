from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.rate_limit import login_rate_limit
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=201,
             summary="Register as a patient")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register_patient(db, data)


@router.post("/login", response_model=TokenResponse, summary="Log in and get a JWT",
             dependencies=[Depends(login_rate_limit)])  # per-IP rate limit
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    # OAuth2 password flow: the form field is called "username" - we put the email in it.
    ip_address = request.client.host if request.client else "unknown"
    return auth_service.login(db, form.username, form.password, ip_address)


@router.get("/me", response_model=UserOut, summary="Who am I?")
def me(current_user: User = Depends(get_current_user)):
    return current_user
