# placeholder: session_manager.py
"""
In-memory session manager for interview sessions.

Provides:
- start_session(parsed_resume, questions) -> session_id
- get_session(session_id) -> session dict
- add_transcript(session_id, segments)
- record_answer(session_id, question_id, answer_text, time_sec)
- end_session(session_id)

This is a lightweight, thread-safe prototype. Replace persistence with DB/storage adapter for production.
"""

from typing import Dict, List, Any, Optional
import time
import threading

from ..core.schemas import ParsedResume, Question, TranscriptSegment, QuestionEvaluation, SessionRecord

_sessions: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def _now_ms() -> int:
    return int(time.time() * 1000)


def start_session(parsed_resume: ParsedResume, questions: List[Question]) -> str:
    session_id = f"sess_{_now_ms()}"
    with _lock:
        _sessions[session_id] = {
            "session_id": session_id,
            "created_at": time.time(),
            "resume": parsed_resume,
            "questions": {q.question_id: q for q in questions},
            "question_order": [q.question_id for q in questions],
            "transcripts": [],  # List[TranscriptSegment]
            "answers": {},  # question_id -> {"text": str, "time_sec": float}
            "evaluations": {},  # question_id -> QuestionEvaluation
            "report": None,
            "metadata": {},
        }
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        s = _sessions.get(session_id)
        # return a shallow copy to avoid accidental external mutation
        return dict(s) if s else None


def add_transcript(session_id: str, segments: List[TranscriptSegment]) -> None:
    with _lock:
        s = _sessions.get(session_id)
        if not s:
            raise KeyError("session not found")
        s["transcripts"].extend(segments)


def record_answer(session_id: str, question_id: str, answer_text: str, time_sec: float = 0.0) -> None:
    with _lock:
        s = _sessions.get(session_id)
        if not s:
            raise KeyError("session not found")
        if question_id not in s["questions"]:
            raise KeyError("question not part of session")
        s["answers"][question_id] = {"text": answer_text, "time_sec": float(time_sec), "recorded_at": time.time()}


def set_evaluation(session_id: str, question_id: str, evaluation: QuestionEvaluation) -> None:
    with _lock:
        s = _sessions.get(session_id)
        if not s:
            raise KeyError("session not found")
        s["evaluations"][question_id] = evaluation


def set_report(session_id: str, report: Any) -> None:
    with _lock:
        s = _sessions.get(session_id)
        if not s:
            raise KeyError("session not found")
        s["report"] = report


def list_sessions() -> List[str]:
    with _lock:
        return list(_sessions.keys())


def end_session(session_id: str) -> None:
    with _lock:
        if session_id in _sessions:
            del _sessions[session_id]