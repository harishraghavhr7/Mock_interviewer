# placeholder: evaluations.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from ...interview.session_manager import get_session, set_evaluation, set_report
from ...evaluator.evaluator import eval_answer, aggregate
from ...reports.report_builder import build_report
from ...storage.storage import save_transcript, save_report

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/run/{session_id}")
def api_evaluate(session_id: str):
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")

    transcripts = sess.get("transcripts", [])
    if not transcripts:
        raise HTTPException(status_code=400, detail="no transcripts available for evaluation")

    # For prototype: join candidate segments into a single answer per question
    from ...stt.postproc import segments_to_plain
    full_answer = segments_to_plain(transcripts, speaker="candidate")

    evals: List[Any] = []
    for qid, q in sess["questions"].items():
        ev = eval_answer(q, full_answer, time_sec=0.0)
        set_evaluation(session_id, qid, ev)
        evals.append(ev)

    agg = aggregate(evals, sess["questions"])
    report = build_report(agg, details=agg.get("details"))
    set_report(session_id, report)

    # persist artifacts (non-blocking best-effort)
    try:
        save_transcript(session_id, transcripts)
        save_report(session_id, report)
    except Exception:
        pass

    return {"evaluations": [e.dict() for e in evals], "report": report.dict()}