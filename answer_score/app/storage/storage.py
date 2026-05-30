# placeholder: storage.py
"""
Simple storage adapter (local filesystem) for prototypes.

Provides:
- save_resume(session_id, parsed_resume)
- save_audio(session_id, filename, bytes)
- save_transcript(session_id, segments)
- save_report(session_id, report_dict)
- load_session_artifacts(session_id) -> dict of paths/objects

Storage is organized under settings.storage_path/<session_id>/
"""

from pathlib import Path
import json
from typing import List, Dict, Any, Optional

from ..core.config import settings
from ..core.schemas import ParsedResume, TranscriptSegment, FinalReport

BASE = Path(settings.storage_path)


def _session_dir(session_id: str) -> Path:
    p = BASE / session_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_resume(session_id: str, parsed: ParsedResume) -> Path:
    d = _session_dir(session_id)
    p = d / "resume.json"
    p.write_text(parsed.json(indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def save_audio(session_id: str, filename: str, content: bytes) -> Path:
    d = _session_dir(session_id)
    aud_path = d / filename
    aud_path.write_bytes(content)
    return aud_path


def save_transcript(session_id: str, segments: List[TranscriptSegment]) -> Path:
    d = _session_dir(session_id)
    p = d / "transcript.json"
    data = [s.dict() for s in segments]
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def save_report(session_id: str, report: FinalReport) -> Path:
    d = _session_dir(session_id)
    pjson = d / "report.json"
    pjson.write_text(report.json(indent=2, ensure_ascii=False), encoding="utf-8")
    # also write simple HTML view
    try:
        from ..reports.report_builder import render_report_html
        phtml = d / "report.html"
        phtml.write_text(render_report_html(report), encoding="utf-8")
    except Exception:
        phtml = None
    return pjson


def load_session_artifacts(session_id: str) -> Dict[str, Optional[Path]]:
    d = BASE / session_id
    if not d.exists():
        return {"path": None, "resume": None, "transcript": None, "report": None}
    return {
        "path": d,
        "resume": (d / "resume.json") if (d / "resume.json").exists() else None,
        "transcript": (d / "transcript.json") if (d / "transcript.json").exists() else None,
        "report": (d / "report.json") if (d / "report.json").exists() else None,
        "report_html": (d / "report.html") if (d / "report.html").exists() else None,
    }