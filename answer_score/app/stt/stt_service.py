# placeholder: stt_service.py
"""
app/stt/stt_service.py

Wrapper around Whisper (or other STT) to produce timestamped TranscriptSegment list.
Provides:
- transcribe_whisper(audio_path) -> List[TranscriptSegment]
- transcribe(audio_path, provider="whisper") generic entrypoint
"""

from typing import List, Optional
from ..core.schemas import TranscriptSegment
from ..core.config import settings

def _to_segments_whisper(result) -> List[TranscriptSegment]:
    segs = []
    for s in result.get("segments", []):
        segs.append(TranscriptSegment(
            start=float(s.get("start", 0.0)),
            end=float(s.get("end", 0.0)),
            speaker="candidate",
            text=(s.get("text") or "").strip()
        ))
    return segs

def transcribe_whisper(audio_path: str, model_name: Optional[str] = None) -> List[TranscriptSegment]:
    """
    Transcribe audio using Whisper (sync). Returns list of TranscriptSegment.
    Raises RuntimeError if Whisper or dependencies are missing.
    """
    try:
        import whisper
    except Exception as exc:
        raise RuntimeError("whisper package not available; install 'whisper' or set another STT provider") from exc

    model = whisper.load_model(model_name or getattr(settings, "WHISPER_MODEL", "small"))
    # model.transcribe returns dict with 'segments'
    result = model.transcribe(audio_path)
    return _to_segments_whisper(result)

def transcribe(audio_path: str, provider: Optional[str] = None, **kwargs) -> List[TranscriptSegment]:
    """
    Generic entry: choose provider by name. Currently supports 'whisper'.
    """
    provider = provider or settings.STT_PROVIDER or "whisper"
    if provider.lower() == "whisper":
        return transcribe_whisper(audio_path, model_name=kwargs.get("model_name"))
    raise RuntimeError(f"Unsupported STT provider: {provider}")