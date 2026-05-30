# placeholder: main.py
"""
FastAPI app wiring the interview flow:
- Parse resume upload
- Generate questions from parsed resume
- Start a session
- Upload audio (STT)
- Evaluate answers and produce report

This is a lightweight prototype. For production: add auth, persistence, background tasks.
"""
from typing import List
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..core.schemas import ParsedResume, Question
from ..resume_parser.parser import parse_resume_bytes
from ..question_generator.generator import generate_questions
from ..interview.session_manager import start_session, add_transcript, get_session
from ..stt.stt_service import transcribe_whisper
from ..evaluator.evaluator import eval_answer, aggregate
from ..reports.report_builder import build_report

app = FastAPI(title="Mock Interviewer API - Prototype")

# Allow local development CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/parse_resume", response_model=ParsedResume)
async def api_parse_resume(file: UploadFile = File(...)):
    content = await file.read()
    try:
        parsed = parse_resume_bytes(content, filename_hint=file.filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"parse error: {e}")
    return parsed


@app.post("/generate_questions", response_model=List[Question])
def api_generate_questions(parsed: ParsedResume, max_questions: int = 5):
    qs = generate_questions(parsed, max_questions=max_questions)
    return qs


@app.post("/start_session")
def api_start_session(parsed: ParsedResume, questions: List[Question]):
    sid = start_session(parsed, questions)
    return {"session_id": sid}


@app.post("/upload_audio/{session_id}")
async def api_upload_audio(session_id: str, file: UploadFile = File(...)):
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")

    content = await file.read()
    # write to temp file (OS temporary dir)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
        tf.write(content)
        tf.flush()
        tmp_path = tf.name

    try:
        segments = transcribe_whisper(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {e}")
    finally:
        # best-effort cleanup
        try:
            import os
            os.unlink(tmp_path)
        except Exception:
            pass

    try:
        add_transcript(session_id, segments)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found while adding transcript")

    return {"status": "ok", "segments": [s.dict() for s in segments]}


@app.post("/evaluate/{session_id}")
def api_evaluate(session_id: str):
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")

    # simple prototype: join all candidate transcript text as the answer for every question
    transcripts = sess.get("transcripts", [])
    if not transcripts:
        raise HTTPException(status_code=400, detail="no transcripts uploaded for session")

    full_text = " ".join([t.text for t in transcripts if getattr(t, "speaker", "candidate") == "candidate"])

    evals = []
    for qid, q in sess["questions"].items():
        ev = eval_answer(q, full_text, time_sec=0.0)
        evals.append(ev)

    agg = aggregate(evals, sess["questions"])
    report = build_report(agg)

    # store results back into session (in-memory prototype)
    sess["evaluations"] = {e.question_id: e for e in evals}
    sess["report"] = report

    return {
        "evaluations": [e.dict() for e in evals],
        "report": report.dict()
    }