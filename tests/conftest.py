import os
from datetime import date, time, timedelta
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_hospital.db")
os.environ.setdefault("JWT_SECRET_KEY", "pytest-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("BCRYPT_ROUNDS", "4")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.appointment import Appointment
from app.models.availability_template import AvailabilityTemplate
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus, Role, SlotStatus
from app.models.patient import Patient
from app.models.slot import Slot
from app.models.speciality import Speciality
from app.models.user import User


@pytest.fixture(scope="session")
def engine():
    test_engine = create_engine(
        "sqlite:///./test_hospital.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def db(session_factory):
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_database(db):
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    yield
    db.rollback()


@pytest.fixture
def seed(db):
    password_hash = "test-hash"

    admin = User(email="admin@test.com", password_hash=password_hash,
                 full_name="Admin User", phone="9999999999",
                 role=Role.ADMIN.value, is_active=True)
    doctor_user = User(email="doctor@test.com", password_hash=password_hash,
                       full_name="Dr. Test", phone="8888888888",
                       role=Role.DOCTOR.value, is_active=True)
    patient_user = User(email="patient1@test.com", password_hash=password_hash,
                        full_name="Patient One", phone="7777777777",
                        role=Role.PATIENT.value, is_active=True)
    patient2_user = User(email="patient2@test.com", password_hash=password_hash,
                         full_name="Patient Two", phone="6666666666",
                         role=Role.PATIENT.value, is_active=True)
    db.add_all([admin, doctor_user, patient_user, patient2_user])
    db.flush()

    speciality = Speciality(name="Cardiology")
    db.add(speciality)
    db.flush()

    doctor = Doctor(user_id=doctor_user.id, speciality_id=speciality.id,
                    registration_no="REG-001", qualification="MD",
                    experience_years=10, consultation_fee=Decimal("500.00"))
    patient1 = Patient(user_id=patient_user.id, gender="FEMALE",
                       blood_group="A+")
    patient2 = Patient(user_id=patient2_user.id, gender="MALE",
                       blood_group="O+")
    db.add_all([doctor, patient1, patient2])
    db.flush()

    future_date = date.today() + timedelta(days=7)
    slot1 = Slot(doctor_id=doctor.id, slot_date=future_date,
                 start_time=time(9, 0), end_time=time(9, 30),
                 status=SlotStatus.FREE.value)
    slot2 = Slot(doctor_id=doctor.id, slot_date=future_date,
                 start_time=time(9, 30), end_time=time(10, 0),
                 status=SlotStatus.FREE.value)
    db.add_all([slot1, slot2])
    db.commit()

    return {
        "admin": admin,
        "doctor_user": doctor_user,
        "doctor": doctor,
        "patient_user": patient_user,
        "patient1": patient1,
        "patient2_user": patient2_user,
        "patient2": patient2,
        "speciality": speciality,
        "slot1": slot1,
        "slot2": slot2,
        "future_date": future_date,
    }


@pytest.fixture
def client(db):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_headers(user):
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}
