"""Health check endpoint (public, no login needed)."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import app_logger
from app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service and database status")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))  # the cheapest possible query
        database_status = "up"
    except Exception as exc:
        app_logger.error("Health check: database is down (%s)", type(exc).__name__)
        database_status = "down"

    body = {
        "status": "ok" if database_status == "up" else "degraded",
        "service": get_settings().APP_NAME,
        "database": database_status,
    }
    return JSONResponse(status_code=200 if database_status == "up" else 503, content=body)
