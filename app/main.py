from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.logging_config import app_logger, setup_logging
from app.exceptions import AppError
from app.routers import (
    appointments,
    auth,
    availability,
    consultations,
    doctors,
    health,
    patients,
    reports,
    slots,
    specialities,
    users,
)

settings = get_settings()
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Backend API for a multi-speciality clinic: doctor availability, "
        "conflict-free appointment booking and secure consultation records.\n\n"
        "Click **Authorize** and log in with an email + password to call protected endpoints."
    ),
)

# --- CORS: only the origins listed in the environment may call the API from a browser ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handlers: every error becomes {"detail": ..., "code": ...}
# and never exposes stack traces or SQL.
# ---------------------------------------------------------------------------
@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    """Our own business errors (raised by services)."""
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail, "code": exc.code}, headers=headers
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    """Errors raised by FastAPI itself (unknown URL -> 404, wrong method -> 405, ...)."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": f"HTTP_{exc.status_code}"},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    """Pydantic found invalid input. We return only the field and a message.

    We do NOT echo the submitted values: they could contain passwords or
    sensitive patient data.
    """
    errors = [
        {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors, "code": "VALIDATION_ERROR"})


@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError):
    """A database constraint was violated (e.g. duplicate unique value)."""
    app_logger.warning("Database integrity error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=409,
        content={"detail": "The request conflicts with existing data", "code": "CONFLICT"},
    )


@app.exception_handler(SQLAlchemyError)
async def handle_database_error(request: Request, exc: SQLAlchemyError):
    # Only the error type is logged: the message may contain SQL with patient data.
    app_logger.error("Database error on %s %s (%s)", request.method, request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=500, content={"detail": "A database error occurred", "code": "DATABASE_ERROR"}
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    """Last safety net for any bug we did not expect."""
    app_logger.error("Unexpected error on %s %s (%s)", request.method, request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error", "code": "INTERNAL_ERROR"}
    )


# ---------------------------------------------------------------------------
# Routers. "availability" must come before "doctors" so that /doctors/me/...
# is matched before /doctors/{doctor_id}.
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(specialities.router)
app.include_router(availability.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(slots.router)
app.include_router(appointments.router)
app.include_router(consultations.router)
app.include_router(reports.router)
