from app.models.user import User
from app.models.speciality import Speciality
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.availability_template import AvailabilityTemplate
from app.models.slot import Slot
from app.models.appointment import Appointment
from app.models.consultation import Consultation

__all__ = [
    "User",
    "Speciality",
    "Doctor",
    "Patient",
    "AvailabilityTemplate",
    "Slot",
    "Appointment",
    "Consultation",
]