# placeholder: utils.py
"""
Utility helpers for resume parsing.

- file_type(path) -> suffix
- clean_text(text) -> normalized text
- chunk_text(text, max_chars=1000) -> generator for long texts
- optional OCR helper for image files (uses pytesseract if available)
"""

from pathlib import Path
from typing import Generator, Optional
import re

try:
    import pytesseract
    from PIL import Image
    _HAS_TESSERACT = True
except Exception:
    _HAS_TESSERACT = False


def file_type(path: str) -> str:
    p = Path(path)
    return p.suffix.lower().lstrip(".")


def clean_text(text: str) -> str:
    if not text:
        return ""
    # normalize whitespace, remove non-printable chars
    t = re.sub(r"\r\n?", "\n", text)
    t = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def chunk_text(text: str, max_chars: int = 1000) -> Generator[str, None, None]:
    """
    Yield chunks of the text up to `max_chars` without splitting words when possible.
    """
    text = text.strip()
    if not text:
        return
    i = 0
    n = len(text)
    while i < n:
        end = min(i + max_chars, n)
        if end < n:
            # try to backtrack to last whitespace to avoid mid-word cuts
            split_at = text.rfind(" ", i, end)
            if split_at > i:
                end = split_at
        yield text[i:end].strip()
        i = end


def ocr_image(path: str) -> Optional[str]:
    """
    Run OCR on an image file and return extracted text, or None if pytesseract not available.
    """
    if not _HAS_TESSERACT:
        return None
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception:
        return None