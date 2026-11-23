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
    # no_show / (completed + no_show) * 100
    no_show_rate: float


class NoShowRateReport(ResponseModel):
    # across all doctors
    overall_no_show_rate: float
    doctors: list[DoctorLoadItem]


class SpecialityDemandItem(ResponseModel):
    speciality_id: int
    speciality_name: str
    appointments: int