from enum import Enum

class Role(str, Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"


class SlotStatus(str, Enum):
    FREE = "FREE"  # can be booked
    BOOKED = "BOOKED"  # has an active appointment
    BLOCKED = "BLOCKED"  # doctor is unavailable


class AppointmentStatus(str, Enum):
    BOOKED = "BOOKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
