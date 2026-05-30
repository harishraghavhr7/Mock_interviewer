# placeholder: parser.py
"""
Simple resume parser.

Capabilities:
- Extract text from PDF, DOCX, or plain TXT.
- Optional OCR for image PDFs using pytesseract (if installed).
- Naive structured extraction: email, phone, basic skill matching, and returns ParsedResume.

This is intentionally lightweight and easy to extend. For production, replace parts
with a robust parser or resume-specific library.
"""

from pathlib import Path
import re
from typing import List, Optional

from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
from PIL import Image
import io
import tempfile

try:
    import pytesseract
    _HAS_TESSERACT = True
except Exception:
    _HAS_TESSERACT = False

from ..core.schemas import ParsedResume, Experience

COMMON_SKILLS = [
    "python", "java", "c++", "c#", "sql", "nosql", "spark", "pandas", "numpy",
    "aws", "gcp", "azure", "docker", "kubernetes", "etl", "hadoop", "redis",
    "react", "node", "flask", "django", "tensorflow", "pytorch", "linux"
]


_EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
_PHONE_RE = re.compile(r"(\+?\d[\d\-\s\(\)]{6,}\d)")


def _extract_from_docx(path: Path) -> str:
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _extract_from_pdf(path: Path, use_ocr: bool = False) -> str:
    # First try text extraction
    try:
        txt = pdf_extract_text(str(path))
        if txt and txt.strip():
            return txt
    except Exception:
        txt = ""

    # Fallback to OCR if available and requested
    if use_ocr and _HAS_TESSERACT:
        try:
            from pdf2image import convert_from_path
        except Exception:
            return txt or ""

        pages = convert_from_path(str(path))
        texts = []
        for page in pages:
            txt_page = pytesseract.image_to_string(page)
            texts.append(txt_page)
        return "\n".join(texts)
    return txt or ""


def _extract_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _find_email(text: str) -> Optional[str]:
    m = _EMAIL_RE.search(text)
    return m.group(0) if m else None


def _find_phone(text: str) -> Optional[str]:
    m = _PHONE_RE.search(text)
    return m.group(0) if m else None


def _extract_skills(text: str, skills_list: Optional[List[str]] = None) -> List[str]:
    skills_list = skills_list or COMMON_SKILLS
    low = text.lower()
    found = []
    for s in skills_list:
        if re.search(r"\b" + re.escape(s.lower()) + r"\b", low):
            found.append(s)
    return sorted(set(found), key=lambda x: skills_list.index(x) if x in skills_list else 9999)


def parse_resume(pathlike: str, use_ocr: bool = False) -> ParsedResume:
    """
    Parse a resume file and return a ParsedResume object.

    Args:
      pathlike: path to resume (pdf, docx, txt)
      use_ocr: If True, try OCR fallback for PDFs when text extraction fails.

    Returns:
      ParsedResume
    """
    p = Path(pathlike)
    if not p.exists():
        raise FileNotFoundError(f"Resume not found: {p}")

    suffix = p.suffix.lower()
    if suffix == ".pdf":
        raw = _extract_from_pdf(p, use_ocr=use_ocr)
    elif suffix in (".docx", ".doc"):
        try:
            raw = _extract_from_docx(p)
        except Exception:
            # fallback to reading as plain text
            raw = _extract_from_pdf(p, use_ocr=use_ocr)
    else:
        # assume plain text
        raw = _extract_from_txt(p)

    # Basic field extraction
    email = _find_email(raw)
    phone = _find_phone(raw)
    skills = _extract_skills(raw)

    # Very naive experience extraction: split by lines, look for years or company hints
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    experiences = []
    for i, ln in enumerate(lines):
        # detect possible experience lines by presence of years, "at", "company", or title-like words
        if re.search(r"\b(20\d{2}|19\d{2}|\d{4}|years)\b", ln.lower()) or re.search(r"\bat\b|\bcompany\b|\brelevant\b", ln.lower()):
            # take this line and the next 1-3 lines as a block
            block = " ".join(lines[i:i+3])
            experiences.append(Experience(title=None, company=None, start=None, end=None, description=block))

    parsed = ParsedResume(
        name=None,
        email=email,
        phone=phone,
        headline=None,
        summary=None,
        skills=skills,
        experience=experiences,
        education=[],
        raw_text=raw,
        meta={"source": str(p.name)}
    )
    return parsed


def parse_resume_bytes(content: bytes, filename_hint: str = "resume.pdf", use_ocr: bool = False) -> ParsedResume:
    """
    Parse resume content from bytes. Writes to a temporary file and delegates to parse_resume.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename_hint).suffix) as tf:
        tf.write(content)
        tf.flush()
        tmp_path = tf.name
    try:
        return parse_resume(tmp_path, use_ocr=use_ocr)
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass