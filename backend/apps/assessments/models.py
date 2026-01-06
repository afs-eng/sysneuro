from django.db import models
from backend.apps.patients.models import Patient


class AssessmentSession(models.Model):
    class Instrument(models.TextChoices):
        WISC4 = "WISC4", "WISC-IV"
        WAIS3 = "WAIS3", "WAIS-III"
        ETDAH_PAIS = "ETDAH_PAIS", "E-TDAH-PAIS"
        ETDAH_AD = "ETDAH_AD", "E-TDAH-AD"

    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        IN_PROGRESS = "in_progress", "Em andamento"
        SCORED = "scored", "Corrigido"
        LOCKED = "locked", "Bloqueado"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="sessions")
    instrument = models.CharField(max_length=30, choices=Instrument.choices)
    test_date = models.DateField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.patient.name} - {self.instrument} ({self.test_date})"
