"""Schemas for the admin reports."""
from app.schemas.common import ResponseModel
class DoctorLoadItem(ResponseModel):
    doctor_id: int
    doctor_name: str
    speciality_name: str
    total: int
    booked: int
    completed: int
    cancelled: int
    no_show: int
    no_show_rate: float  # percent: no_show / (completed + no_show) * 100


class NoShowRateReport(ResponseModel):
    overall_no_show_rate: float  # percent over all doctors
    doctors: list[DoctorLoadItem]


class SpecialityDemandItem(ResponseModel):
    speciality_id: int
    speciality_name: str
    appointments: int
