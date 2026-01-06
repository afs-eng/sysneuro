from django.db import models


class Patient(models.Model):
    name = models.CharField(max_length=200)
    birth_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Guardian(models.Model):
    class Relationship(models.TextChoices):
        MOTHER = "mother", "Mãe"
        FATHER = "father", "Pai"
        TUTOR = "tutor", "Tutor/Responsável legal"
        OTHER = "other", "Outro"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="guardians")
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=20, choices=Relationship.choices, default=Relationship.OTHER)

    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.get_relationship_display()})"
