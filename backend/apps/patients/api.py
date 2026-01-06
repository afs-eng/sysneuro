from datetime import date
from typing import List, Optional

from ninja import Router, Schema
from django.db.models import Q

from .models import Patient, Guardian


router = Router(tags=["Patients"])


class GuardianIn(Schema):
    name: str
    relationship: str = "other"  # mother/father/tutor/other
    phone: str = ""
    email: str = ""


class GuardianOut(Schema):
    id: int
    name: str
    relationship: str
    phone: str
    email: str


class PatientIn(Schema):
    name: str
    birth_date: date


class PatientOut(Schema):
    id: int
    name: str
    birth_date: date
    guardians: List[GuardianOut]


@router.post("", response=PatientOut)
def create_patient(request, payload: PatientIn):
    patient = Patient.objects.create(**payload.dict())
    return PatientOut(
        id=patient.id,
        name=patient.name,
        birth_date=patient.birth_date,
        guardians=[],
    )


@router.get("", response=List[PatientOut])
def list_patients(request, search: Optional[str] = None):
    qs = Patient.objects.all().order_by("-id")
    if search:
        qs = qs.filter(Q(name__icontains=search))

    out: List[PatientOut] = []
    for p in qs[:200]:
        guardians = [
            GuardianOut(
                id=g.id, name=g.name, relationship=g.relationship, phone=g.phone, email=g.email
            )
            for g in p.guardians.all().order_by("id")
        ]
        out.append(PatientOut(id=p.id, name=p.name, birth_date=p.birth_date, guardians=guardians))
    return out


@router.get("/{patient_id}", response=PatientOut)
def get_patient(request, patient_id: int):
    p = Patient.objects.get(id=patient_id)
    guardians = [
        GuardianOut(id=g.id, name=g.name, relationship=g.relationship, phone=g.phone, email=g.email)
        for g in p.guardians.all().order_by("id")
    ]
    return PatientOut(id=p.id, name=p.name, birth_date=p.birth_date, guardians=guardians)


@router.post("/{patient_id}/guardians", response=GuardianOut)
def add_guardian(request, patient_id: int, payload: GuardianIn):
    p = Patient.objects.get(id=patient_id)
    g = Guardian.objects.create(patient=p, **payload.dict())
    return GuardianOut(id=g.id, name=g.name, relationship=g.relationship, phone=g.phone, email=g.email)
