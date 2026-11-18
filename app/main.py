from fastapi import FastAPI

from app.database import Base, engine
from app import models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hospital Appointment Management System",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Hospital Appointment Management System API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "UP"
    }