from django.db import models
from backend.apps.assessments.models import AssessmentSession


class Wisc4NormTable(models.Model):
    """
    Tabela de conversão bruto -> ponderado (scaled score) por faixa etária.
    Ex.: key = "idade_6-8_6-11"
    min_months/max_months em meses (auditoria + seleção automática)
    file_path: caminho relativo (ex.: "apps/wisc4/norms/idade_6-8_6-11.csv")
    """
    key = models.CharField(max_length=50, unique=True)
    min_months = models.PositiveIntegerField()
    max_months = models.PositiveIntegerField()
    file_path = models.CharField(max_length=300)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.key


class Wisc4RawScore(models.Model):
    class Subtest(models.TextChoices):
        # Ajuste a lista conforme seus subtestes que você quer corrigir primeiro
        SEMELHANCAS = "SEMELHANCAS", "Semelhanças"
        VOCABULARIO = "VOCABULARIO", "Vocabulário"
        COMPREENSAO = "COMPREENSAO", "Compreensão"
        CUBOS = "CUBOS", "Cubos"
        CONCEITOS = "CONCEITOS", "Conceitos Figurativos"
        CODIGO = "CODIGO", "Código"
        PROCURAR_SIMBOLOS = "PROCURAR_SIMBOLOS", "Procurar Símbolos"
        DIGITOS = "DIGITOS", "Dígitos"
        SEQ_NUM_LETRAS = "SEQ_NUM_LETRAS", "Sequência de Números e Letras"

    session = models.ForeignKey(
        AssessmentSession,
        on_delete=models.CASCADE,
        related_name="wisc4_raw_scores",
    )
    subtest = models.CharField(max_length=40, choices=Subtest.choices)
    raw_score = models.IntegerField()
    scaled_score = models.IntegerField(null=True, blank=True)  # preenchido ao corrigir

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session", "subtest")

    def __str__(self) -> str:
        return f"{self.session_id} {self.subtest}: {self.raw_score}"


class Wisc4Result(models.Model):
    session = models.OneToOneField(
        AssessmentSession,
        on_delete=models.CASCADE,
        related_name="wisc4_result",
    )

    # auditoria
    age_months = models.PositiveIntegerField()
    norm_table_key = models.CharField(max_length=50)

    # compostos
    icv = models.IntegerField()
    iop = models.IntegerField()
    imo = models.IntegerField()
    ivp = models.IntegerField()
    qit = models.IntegerField()

    scored_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"WISC-IV Result session={self.session_id} QIT={self.qit}"
