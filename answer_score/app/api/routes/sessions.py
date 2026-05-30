# placeholder: sessions.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from ...core.schemas import ParsedResume, Question
from ...interview.session_manager import start_session, get_session, list_sessions, end_session
from ...storage.storage import save_resume

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start")
def api_start(parsed: ParsedResume, questions: List[Question]):
    sid = start_session(parsed, questions)
    try:
        save_resume(sid, parsed)
    except Exception:
        # non-fatal for prototype
        pass
    return {"session_id": sid}


@router.get("/{session_id}")
def api_get(session_id: str):
    s = get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    return s


@router.get("/")
def api_list():
    return {"sessions": list_sessions()}


@router.delete("/{session_id}")
def api_end(session_id: str):
    s = get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    end_session(session_id)
    return {"status": "ended", "session_id": session_id}