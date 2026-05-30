# placeholder: recorder_adapter.py
"""
Recorder adapter: small helpers to normalize client audio uploads.

Responsibilities:
- Accept bytes or base64 audio payloads and write to a temp file
- Normalize common formats (wav, mp3) using pydub if available
- Validate duration and file size limits using `settings`
- Returns local path to the normalized WAV file ready for STT

This is intentionally small — production should move heavy work to background workers.
"""

import base64
import tempfile
import os
from pathlib import Path
from typing import Tuple, Optional

from ..core.config import settings

try:
    from pydub import AudioSegment
    _HAS_PYDUB = True
except Exception:
    _HAS_PYDUB = False


def _write_temp_bytes(content: bytes, suffix: str = ".wav") -> str:
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tf.write(content)
    tf.flush()
    tf.close()
    return tf.name


def decode_base64_to_file(b64: str, filename_hint: str = "upload.wav") -> str:
    headered = "," in b64
    if headered:
        b64 = b64.split(",", 1)[1]
    content = base64.b64decode(b64)
    return _write_temp_bytes(content, suffix=Path(filename_hint).suffix or ".wav")


def normalize_to_wav(input_path: str, target_rate: int = 16000, target_channels: int = 1) -> str:
    """
    Convert `input_path` to a WAV file with `target_rate` Hz and `target_channels` channels.
    Returns path to the normalized wav file.
    Requires pydub + ffmpeg for conversion; if pydub not available, returns input_path if already .wav.
    """
    p = Path(input_path)
    if p.suffix.lower() == ".wav" and not _HAS_PYDUB:
        return str(p)

    if not _HAS_PYDUB:
        raise RuntimeError("pydub (and ffmpeg) required to normalize audio formats")

    audio = AudioSegment.from_file(str(p))
    audio = audio.set_frame_rate(target_rate).set_channels(target_channels).set_sample_width(2)
    out_path = _write_temp_bytes(b"", suffix=".wav")
    audio.export(out_path, format="wav")
    return out_path


def validate_audio_file(path: str) -> Tuple[bool, Optional[str]]:
    """
    Basic validation: file exists, size under MAX_FILE_SIZE_MB, duration under MAX_AUDIO_SECONDS (if pydub available).
    Returns (ok, message_if_error)
    """
    p = Path(path)
    if not p.exists():
        return False, "file not found"
    size_mb = p.stat().st_size / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        return False, f"file size {size_mb:.1f}MB exceeds limit {settings.MAX_FILE_SIZE_MB}MB"
    if _HAS_PYDUB:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(p))
            duration_sec = len(audio) / 1000.0
            if duration_sec > settings.MAX_AUDIO_SECONDS:
                return False, f"audio duration {duration_sec:.1f}s exceeds limit {settings.MAX_AUDIO_SECONDS}s"
        except Exception:
            # can't measure duration reliably; allow for now
            pass
    return True, None