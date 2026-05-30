# placeholder: transcripts.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from ...interview.session_manager import add_transcript, get_session
from ...stt.stt_service import transcribe
from ...stt.postproc import merge_adjacent_segments

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("/upload/{session_id}")
async def upload_audio(session_id: str, file: UploadFile = File(...)):
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")

    raw = await file.read()
    # write tempfile
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
        tf.write(raw)
        tf.flush()
        tmp = tf.name

    try:
        segments = transcribe(tmp)
        segments = merge_adjacent_segments(segments)
        add_transcript(session_id, segments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"transcription error: {e}")
    finally:
        try:
            import os
            os.unlink(tmp)
        except Exception:
            pass

    return {"status": "ok", "segments": [s.dict() for s in segments]}