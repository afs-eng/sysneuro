import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Tuple

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction

from backend.apps.assessments.models import AssessmentSession
from backend.apps.patients.models import Patient
from backend.apps.wisc.models import Wisc4NormTable, Wisc4RawScore, Wisc4Result


@dataclass(frozen=True)
class AgeInfo:
    years: int
    months: int
    total_months: int


def calc_age_months(birth_date, test_date) -> AgeInfo:
    rd = relativedelta(test_date, birth_date)
    total_months = rd.years * 12 + rd.months
    return AgeInfo(years=rd.years, months=rd.months, total_months=total_months)


def pick_norm_table(age_months: int) -> Wisc4NormTable:
    table = (
        Wisc4NormTable.objects.filter(is_active=True, min_months__lte=age_months, max_months__gte=age_months)
        .order_by("min_months")
        .first()
    )
    if not table:
        raise ValueError(f"Não há tabela normativa cadastrada para age_months={age_months}.")
    return table


@lru_cache(maxsize=256)
def load_norm_table_csv(file_path: str) -> list[dict]:
    """
    Carrega o CSV uma vez e guarda em cache.
    Retorna lista de dicts (DictReader).
    """
    # Você pode guardar file_path como relativo ao BASE_DIR
    base_dir = Path(settings.BASE_DIR)
    full_path = (base_dir / file_path).resolve()
    if not full_path.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {full_path}")

    with full_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def lookup_scaled_score(rows: list[dict], subtest: str, raw_score: int) -> int:
    """
    SUPORTA DOIS FORMATOS:
    1) Wide: coluna 'raw_score' e colunas por subteste:
       raw_score,CUBOS,SEMELHANCAS,...
    2) Long: colunas: subtest,raw_min,raw_max,scaled
    Ajuste aqui caso seu CSV seja diferente.
    """
    # Detecta formato
    headers = set(rows[0].keys()) if rows else set()

    if "raw_score" in headers and subtest in headers:
        # WIDE
        for r in rows:
            if int(r["raw_score"]) == raw_score:
                v = r.get(subtest)
                if v is None or v == "":
                    raise ValueError(f"Sem valor para subteste={subtest} raw={raw_score}")
                return int(v)

    if {"subtest", "raw_min", "raw_max", "scaled"}.issubset(headers):
        # LONG
        for r in rows:
            if r["subtest"] == subtest:
                mn = int(r["raw_min"])
                mx = int(r["raw_max"])
                if mn <= raw_score <= mx:
                    return int(r["scaled"])

    raise ValueError(f"Não foi possível converter bruto->ponderado: subtest={subtest}, raw={raw_score}")


def compute_index_sums(scaled: Dict[str, int]) -> Dict[str, int]:
    """
    Defina aqui quais subtestes entram em cada índice.
    Esta versão é um ESQUELETO (você ajusta conforme seu conjunto de subtestes).
    """
    # Exemplo (ajuste)
    sum_icv = scaled["SEMELHANCAS"] + scaled["VOCABULARIO"] + scaled["COMPREENSAO"]
    sum_iop = scaled["CUBOS"] + scaled["CONCEITOS"]
    sum_imo = scaled["DIGITOS"] + scaled["SEQ_NUM_LETRAS"]
    sum_ivp = scaled["CODIGO"] + scaled["PROCURAR_SIMBOLOS"]

    return {"ICV": sum_icv, "IOP": sum_iop, "IMO": sum_imo, "IVP": sum_ivp}


def convert_sums_to_composites(index_sums: Dict[str, int]) -> Dict[str, int]:
    """
    Aqui entra a tabela de conversão soma de ponderados -> composto.
    Nesta primeira etapa, deixo como NOT IMPLEMENTED.
    Você vai cadastrar essas tabelas (ou um CSV) e implementar o lookup,
    exatamente como fez com bruto->ponderado.
    """
    raise NotImplementedError("Falta implementar conversão soma->composto (ICV/IOP/IMO/IVP/QIT).")


@transaction.atomic
def score_wisc4_session(session_id: int) -> Wisc4Result:
    s = AssessmentSession.objects.select_related("patient").get(id=session_id)

    if s.instrument != AssessmentSession.Instrument.WISC4:
        raise ValueError("Sessão não é WISC-IV.")

    age = calc_age_months(s.patient.birth_date, s.test_date)
    table = pick_norm_table(age.total_months)
    rows = load_norm_table_csv(table.file_path)

    raw_items = list(Wisc4RawScore.objects.filter(session=s))
    if not raw_items:
        raise ValueError("Não há pontos brutos lançados para esta sessão.")

    scaled_map: Dict[str, int] = {}

    for item in raw_items:
        scaled = lookup_scaled_score(rows, item.subtest, item.raw_score)
        item.scaled_score = scaled
        item.save(update_fields=["scaled_score"])
        scaled_map[item.subtest] = scaled

    index_sums = compute_index_sums(scaled_map)
    composites = convert_sums_to_composites(index_sums)  # implementará depois

    result, _ = Wisc4Result.objects.update_or_create(
        session=s,
        defaults={
            "age_months": age.total_months,
            "norm_table_key": table.key,
            "icv": composites["ICV"],
            "iop": composites["IOP"],
            "imo": composites["IMO"],
            "ivp": composites["IVP"],
            "qit": composites["QIT"],
        },
    )

    s.status = AssessmentSession.Status.SCORED
    s.save(update_fields=["status"])

    return result
