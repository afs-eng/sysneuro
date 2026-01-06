from datetime import date
from typing import List, Optional

from ninja import Router, Schema
from backend.apps.patients.models import Patient
from .models import AssessmentSession


router = Router(tags=["Sessions"])


class SessionIn(Schema):
    patient_id: int
    instrument: str  # WISC4, WAIS3, ETDAH_PAIS, ETDAH_AD
    test_date: date


class SessionOut(Schema):
    id: int
    patient_id: int
    instrument: str
    test_date: date
    status: str


@router.post("", response=SessionOut)
def create_session(request, payload: SessionIn):
    patient = Patient.objects.get(id=payload.patient_id)
    s = AssessmentSession.objects.create(
        patient=patient,
        instrument=payload.instrument,
        test_date=payload.test_date,
    )
    return SessionOut(
        id=s.id,
        patient_id=s.patient.id,
        instrument=s.instrument,
        test_date=s.test_date,
        status=s.status,
    )


@router.get("", response=List[SessionOut])
def list_sessions(request, patient_id: Optional[int] = None, instrument: Optional[str] = None):
    qs = AssessmentSession.objects.all().order_by("-id")
    if patient_id:
        qs = qs.filter(patient_id=patient_id)
    if instrument:
        qs = qs.filter(instrument=instrument)

    return [
        SessionOut(
            id=s.id,
            patient_id=s.patient_id,
            instrument=s.instrument,
            test_date=s.test_date,
            status=s.status,
        )
        for s in qs[:200]
    ]


@router.get("/{session_id}", response=SessionOut)
def get_session(request, session_id: int):
    s = AssessmentSession.objects.get(id=session_id)
    return SessionOut(
        id=s.id,
        patient_id=s.patient_id,
        instrument=s.instrument,
        test_date=s.test_date,
        status=s.status,
    )
