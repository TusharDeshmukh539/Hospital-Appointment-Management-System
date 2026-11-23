from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.exceptions import ConflictError
from app.core.security import create_access_token
from app.models.appointment import Appointment
from app.models.consultation import Consultation
from app.models.enums import AppointmentStatus, SlotStatus
from app.models.slot import Slot
from app.schemas.appointment import AppointmentCreate, AppointmentReschedule
from app.schemas.consultation import ConsultationCreate
from app.services import appointment_service


def auth_headers(user):
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_health_and_auth_me(client, seed):
    assert client.get("/health").status_code == 200
    response = client.get("/auth/me", headers=auth_headers(seed["admin"]))
    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"
    assert client.get("/auth/me").status_code == 401


def test_register_patient_and_login(client, monkeypatch):
    from app.services import auth_service
    monkeypatch.setattr(auth_service, "hash_password", lambda value: "test-hash")
    monkeypatch.setattr(auth_service, "verify_password",
                        lambda plain, hashed: plain == "Password123")

    register = client.post("/auth/register", json={
        "email": "new.patient@test.com",
        "password": "Password123",
        "full_name": "New Patient",
        "phone": "5555555555",
    })
    assert register.status_code == 201

    login = client.post("/auth/login", data={
        "username": "new.patient@test.com",
        "password": "Password123",
    })
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_speciality_crud(client, seed):
    headers = auth_headers(seed["admin"])
    created = client.post("/specialities", headers=headers,
                          json={"name": "Neurology"})
    assert created.status_code == 201

    listed = client.get("/specialities", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 2

    speciality_id = created.json()["id"]
    updated = client.put(f"/specialities/{speciality_id}", headers=headers,
                         json={"name": "Neuro Science"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Neuro Science"


def test_doctor_create_search_and_profile(client, seed, monkeypatch):
    from app.services import doctor_service
    monkeypatch.setattr(doctor_service, "hash_password", lambda value: "test-hash")
    headers = auth_headers(seed["admin"])
    created = client.post("/doctors", headers=headers, json={
        "email": "doctor2@test.com",
        "password": "Password123",
        "full_name": "Dr. Second",
        "speciality_id": seed["speciality"].id,
        "registration_no": "REG-002",
        "qualification": "MBBS",
        "experience_years": 5,
        "consultation_fee": "450.00",
    })
    assert created.status_code == 201

    search = client.get("/doctors", headers=headers,
                        params={"speciality": "Cardio"})
    assert search.status_code == 200
    assert search.json()["total"] >= 1

    profile = client.get("/doctors/me",
                         headers=auth_headers(seed["doctor_user"]))
    assert profile.status_code == 200
    assert profile.json()["registration_no"] == "REG-001"


def test_patient_profile_and_admin_list(client, seed):
    profile = client.get("/patients/me",
                         headers=auth_headers(seed["patient_user"]))
    assert profile.status_code == 200
    assert profile.json()["full_name"] == "Patient One"

    listed = client.get("/patients", headers=auth_headers(seed["admin"]))
    assert listed.status_code == 200
    assert listed.json()["total"] == 2


def test_availability_generate_list_and_free_slots(client, seed):
    doctor_headers = auth_headers(seed["doctor_user"])
    future = seed["future_date"]

    template = client.post("/doctors/me/availability", headers=doctor_headers, json={
        "weekday": future.weekday(),
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "slot_minutes": 30,
    })
    assert template.status_code == 201

    generated = client.post("/doctors/me/slots/generate", headers=doctor_headers, json={
        "from_date": str(future),
        "to_date": str(future),
    })
    assert generated.status_code == 200
    assert generated.json()["created"] == 2

    mine = client.get("/doctors/me/slots", headers=doctor_headers,
                      params={"date": str(future)})
    assert mine.status_code == 200
    assert len(mine.json()) == 4

    public = client.get(f"/doctors/{seed['doctor'].id}/slots",
                        headers=auth_headers(seed["patient_user"]),
                        params={"date": str(future)})
    assert public.status_code == 200
    assert len(public.json()) >= 2


def test_block_date_only_blocks_free_slots(client, seed, db):
    headers = auth_headers(seed["doctor_user"])
    response = client.post("/doctors/me/slots/block-date", headers=headers,
                           json={"slot_date": str(seed["future_date"])})
    assert response.status_code == 200
    assert response.json()["blocked"] == 2

    db.expire_all()
    assert db.query(Slot).filter(Slot.doctor_id == seed["doctor"].id).count() == 2
    assert all(slot.status == SlotStatus.BLOCKED.value
               for slot in db.query(Slot).all())


def test_concurrent_booking_is_exactly_one_success_and_one_conflict(
        session_factory, seed):
    def attempt_booking():
        db = session_factory()
        try:
            patient = db.get(type(seed["patient_user"]), seed["patient_user"].id)
            return appointment_service.book_appointment(
                db,
                patient,
                AppointmentCreate(slot_id=seed["slot1"].id, reason="Checkup"),
            )
        finally:
            db.close()

    results = []
    errors = []
    for _ in range(2):
        try:
            results.append(attempt_booking())
        except ConflictError as exc:
            errors.append(exc)

    assert len(results) == 1
    assert len(errors) == 1


def test_reschedule_releases_old_slot_and_claims_new_slot(db, seed):
    appointment = Appointment(slot_id=seed["slot1"].id,
                              patient_id=seed["patient1"].id,
                              doctor_id=seed["doctor"].id,
                              status=AppointmentStatus.BOOKED.value,
                              reason="Follow-up")
    db.add(appointment)
    db.commit()

    result = appointment_service.reschedule_appointment(
        db,
        seed["patient_user"],
        appointment.id,
        AppointmentReschedule(new_slot_id=seed["slot2"].id),
    )
    db.expire_all()

    assert result.slot_id == seed["slot2"].id
    assert db.get(Slot, seed["slot1"].id).status == SlotStatus.FREE.value
    assert db.get(Slot, seed["slot2"].id).status == SlotStatus.BOOKED.value


def test_consultation_access_for_owner_and_other_patient(client, seed, db):
    appointment = Appointment(slot_id=seed["slot1"].id,
                              patient_id=seed["patient1"].id,
                              doctor_id=seed["doctor"].id,
                              status=AppointmentStatus.COMPLETED.value,
                              reason="Consult")
    db.add(appointment)
    db.flush()
    consultation = Consultation(appointment_id=appointment.id,
                                diagnosis="Healthy",
                                prescription="Rest",
                                notes="No notes")
    db.add(consultation)
    db.commit()

    owner = client.get(f"/appointments/{appointment.id}/consultation",
                       headers=auth_headers(seed["patient_user"]))
    assert owner.status_code == 200
    assert owner.json()["diagnosis"] == "Healthy"

    other = client.get(f"/appointments/{appointment.id}/consultation",
                       headers=auth_headers(seed["patient2_user"]))
    assert other.status_code == 404


def test_record_consultation_and_doctor_status(client, seed, db):
    appointment = Appointment(slot_id=seed["slot1"].id,
                              patient_id=seed["patient1"].id,
                              doctor_id=seed["doctor"].id,
                              status=AppointmentStatus.BOOKED.value)
    db.add(appointment)
    db.commit()

    status = client.patch(
        f"/appointments/{appointment.id}/status",
        headers=auth_headers(seed["doctor_user"]),
        json={"status": "COMPLETED"},
    )
    assert status.status_code == 200

    record = client.post(
        f"/appointments/{appointment.id}/consultation",
        headers=auth_headers(seed["doctor_user"]),
        json={"diagnosis": "Migraine", "prescription": "Medication",
              "notes": "Review in 2 weeks", "follow_up_date": str(date.today())},
    )
    assert record.status_code == 201


def test_cancel_appointment_releases_slot(client, seed, db):
    seed["slot1"].status = SlotStatus.BOOKED.value
    appointment = Appointment(slot_id=seed["slot1"].id,
                              patient_id=seed["patient1"].id,
                              doctor_id=seed["doctor"].id,
                              status=AppointmentStatus.BOOKED.value)
    db.add(appointment)
    db.commit()

    response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        headers=auth_headers(seed["patient_user"]),
    )
    assert response.status_code == 200
    db.expire_all()
    assert db.get(type(seed["slot1"]), seed["slot1"].id).status == SlotStatus.FREE.value


def test_patient_consultation_history_and_admin_reports(client, seed, db):
    appointment = Appointment(slot_id=seed["slot1"].id,
                              patient_id=seed["patient1"].id,
                              doctor_id=seed["doctor"].id,
                              status=AppointmentStatus.COMPLETED.value)
    db.add(appointment)
    db.flush()
    db.add(Consultation(appointment_id=appointment.id,
                        diagnosis="Cold", prescription="Fluids"))
    db.commit()

    history = client.get("/consultations/me",
                         headers=auth_headers(seed["patient_user"]))
    assert history.status_code == 200
    assert history.json()["total"] == 1

    admin_headers = auth_headers(seed["admin"])
    assert client.get("/reports/doctor-load", headers=admin_headers).status_code == 200
    assert client.get("/reports/no-show-rate", headers=admin_headers).status_code == 200
    assert client.get("/reports/speciality-demand", headers=admin_headers).status_code == 200
