from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def make_engine(database_url: str, **kwargs) -> Engine:
    connect_args = {}
    is_sqlite = database_url.startswith("sqlite")
    if is_sqlite:
        # SQLite normally refuses to be used from more than one thread.
        connect_args["check_same_thread"] = False

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,  # re-connect automatically if the connection went stale
        **kwargs,
    )

    if is_sqlite:
        # SQLite ignores foreign keys unless we switch them on for each connection.
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = make_engine(get_settings().DATABASE_URL)

# Each request gets its own Session created from this factory.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    """FastAPI dependency: open a session for the request and always close it."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
