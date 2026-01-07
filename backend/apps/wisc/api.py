from typing import List, Optional
from ninja import Router, Schema
from backend.apps.assessments.models import AssessmentSession
from backend.apps.wisc.models import Wisc4RawScore, Wisc4Result
from backend.apps.wisc.services.scoring import score_wisc4_session

'''from typing import List, Optional
from ninja import Router, Schema
from apps.assessments.models import AssessmentSession
from apps.wisc4.models import Wisc4RawScore, Wisc4Result
from apps.wisc4.services.scoring import score_wisc4_session'''

router = Router(tags=["WISC-IV"])


class RawScoreIn(Schema):
    subtest: str
    raw_score: int


class RawScoreOut(Schema):
    subtest: str
    raw_score: int
    scaled_score: Optional[int] = None


class ResultOut(Schema):
    age_months: int
    norm_table_key: str
    icv: int
    iop: int
    imo: int
    ivp: int
    qit: int


@router.post("/sessions/{session_id}/raw-scores", response=List[RawScoreOut])
def upsert_raw_scores(request, session_id: int, payload: List[RawScoreIn]):
    s = AssessmentSession.objects.get(id=session_id)
    if s.instrument != AssessmentSession.Instrument.WISC4:
        raise ValueError("Sessão não é WISC-IV.")

    out: List[RawScoreOut] = []
    for item in payload:
        obj, _ = Wisc4RawScore.objects.update_or_create(
            session=s,
            subtest=item.subtest,
            defaults={"raw_score": item.raw_score},
        )
        out.append(RawScoreOut(subtest=obj.subtest, raw_score=obj.raw_score, scaled_score=obj.scaled_score))
    return out


@router.post("/sessions/{session_id}/score", response=ResultOut)
def score_session(request, session_id: int):
    r = score_wisc4_session(session_id)
    return ResultOut(
        age_months=r.age_months,
        norm_table_key=r.norm_table_key,
        icv=r.icv, iop=r.iop, imo=r.imo, ivp=r.ivp, qit=r.qit
    )


@router.get("/sessions/{session_id}/export-ai", response=ResultOut)
def export_ai(request, session_id: int):
    r = Wisc4Result.objects.get(session_id=session_id)
    return ResultOut(
        age_months=r.age_months,
        norm_table_key=r.norm_table_key,
        icv=r.icv, iop=r.iop, imo=r.imo, ivp=r.ivp, qit=r.qit
    )
