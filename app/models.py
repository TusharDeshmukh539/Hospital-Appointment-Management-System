from datetime import datetime, date, time
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Date,
    DateTime,
    Time,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
    Numeric,
    Enum
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)


class Base(DeclarativeBase):
    pass


# USERS

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    phone: Mapped[str | None] = mapped_column(
        String(20)
    )

    role: Mapped[str] = mapped_column(
        Enum(
            "ADMIN",
            "DOCTOR",
            "PATIENT",
            name="user_role"
        ),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    doctor = relationship(
        "Doctor",
        back_populates="user",
        uselist=False
    )

    patient = relationship(
        "Patient",
        back_populates="user",
        uselist=False
    )


# ==========================
# SPECIALITIES
# ==========================
class Speciality(Base):
    __tablename__ = "specialities"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    doctors = relationship(
        "Doctor",
        back_populates="speciality"
    )


# ==========================
# DOCTORS
# ==========================
class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    speciality_id: Mapped[int] = mapped_column(
        ForeignKey("specialities.id"),
        nullable=False
    )

    registration_no: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    qualification: Mapped[str | None] = mapped_column(
        String(255)
    )

    experience_years: Mapped[int | None] = mapped_column(
        Integer
    )

    consultation_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="doctor"
    )

    speciality = relationship(
        "Speciality",
        back_populates="doctors"
    )

    availability_templates = relationship(
        "AvailabilityTemplate",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )

    slots = relationship(
        "Slot",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )

    appointments = relationship(
        "Appointment",
        back_populates="doctor"
    )


# ==========================
# PATIENTS
# ==========================
class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    date_of_birth: Mapped[date | None] = mapped_column(Date)

    gender: Mapped[str | None] = mapped_column(
        Enum(
            "MALE",
            "FEMALE",
            "OTHER",
            name="gender_enum"
        )
    )

    blood_group: Mapped[str | None] = mapped_column(
        String(10)
    )

    address: Mapped[str | None] = mapped_column(Text)

    user = relationship(
        "User",
        back_populates="patient"
    )

    appointments = relationship(
        "Appointment",
        back_populates="patient"
    )


# ==========================
# AVAILABILITY TEMPLATES
# ==========================
class AvailabilityTemplate(Base):
    __tablename__ = "availability_templates"

    id: Mapped[int] = mapped_column(primary_key=True)

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False
    )

    weekday: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )  # 0-6

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    slot_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    doctor = relationship(
        "Doctor",
        back_populates="availability_templates"
    )


# ==========================
# SLOTS
# ==========================
class Slot(Base):
    __tablename__ = "slots"

    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "slot_date",
            "start_time",
            name="uq_doctor_slot"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False
    )

    slot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "FREE",
            "BOOKED",
            "BLOCKED",
            name="slot_status"
        ),
        default="FREE",
        nullable=False
    )

    doctor = relationship(
        "Doctor",
        back_populates="slots"
    )

    appointment = relationship(
        "Appointment",
        back_populates="slot",
        uselist=False
    )


# ==========================
# APPOINTMENTS
# ==========================
class Appointment(Base):
    __tablename__ = "appointments"

    __table_args__ = (
        Index(
            "idx_appointments_doctor_status",
            "doctor_id",
            "status"
        ),
        Index(
            "idx_appointments_patient",
            "patient_id"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    slot_id: Mapped[int] = mapped_column(
        ForeignKey("slots.id"),
        unique=True,
        nullable=False
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        nullable=False
    )

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "BOOKED",
            "COMPLETED",
            "CANCELLED",
            "NO_SHOW",
            name="appointment_status"
        ),
        default="BOOKED",
        nullable=False
    )

    booked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime
    )

    reason: Mapped[str | None] = mapped_column(
        Text
    )

    slot = relationship(
        "Slot",
        back_populates="appointment"
    )

    patient = relationship(
        "Patient",
        back_populates="appointments"
    )

    doctor = relationship(
        "Doctor",
        back_populates="appointments"
    )

    consultation = relationship(
        "Consultation",
        back_populates="appointment",
        uselist=False
    )


# ==========================
# CONSULTATIONS
# ==========================
class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(primary_key=True)

    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id"),
        unique=True,
        nullable=False
    )

    diagnosis: Mapped[str | None] = mapped_column(
        Text
    )

    prescription: Mapped[str | None] = mapped_column(
        Text
    )

    notes: Mapped[str | None] = mapped_column(
        Text
    )

    follow_up_date: Mapped[date | None] = mapped_column(
        Date
    )

    appointment = relationship(
        "Appointment",
        back_populates="consultation"
    )