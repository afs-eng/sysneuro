import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from datetime import date

def age_in_months(birth: date, ref: date) -> int:
    if ref < birth:
        raise ValueError("Data de avaliação anterior à data de nascimento.")
    months = (ref.year - birth.year) * 12 + (ref.month - birth.month)
    # Se ainda não fez aniversário no mês, reduz 1 mês
    if ref.day < birth.day:
        months -= 1
    return months


@dataclass(frozen=True)
class AgeBand:
    file: Path
    min_months: int
    max_months: int

def _to_months(years: int, months: int) -> int:
    return years * 12 + months

def build_ageband_index(folder: Path) -> List[AgeBand]:
    """
    Lê todos os arquivos 'idade_Y-M-Y-M.csv' e cria uma lista de faixas (min/max em meses).
    """
    pattern = re.compile(r"^idade_(\d+)-(\d+)-(\d+)-(\d+)\.csv$", re.IGNORECASE)
    bands: List[AgeBand] = []

    for f in folder.iterdir():
        if not f.is_file():
            continue
        m = pattern.match(f.name)
        if not m:
            continue
        y1, m1, y2, m2 = map(int, m.groups())
        min_m = _to_months(y1, m1)
        max_m = _to_months(y2, m2)
        if max_m < min_m:
            raise ValueError(f"Faixa invertida no arquivo: {f.name}")
        bands.append(AgeBand(file=f, min_months=min_m, max_months=max_m))

    # ordena para busca previsível
    bands.sort(key=lambda b: (b.min_months, b.max_months))
    if not bands:
        raise FileNotFoundError(f"Nenhuma tabela encontrada em {folder} com padrão idade_Y-M-Y-M.csv")

    return bands

def pick_table_for_age(age_months: int, bands: List[AgeBand]) -> Path:
    """
    Retorna o arquivo cuja faixa inclui age_months (inclusivo).
    """
    for b in bands:
        if b.min_months <= age_months <= b.max_months:
            return b.file
    raise ValueError(f"Não existe tabela para idade {age_months} meses.")
