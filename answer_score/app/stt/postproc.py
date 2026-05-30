# placeholder: postproc.py
"""
Post-processing helpers for transcripts.

- merge_adjacent_segments(segments, max_gap=0.5)
- normalize_text(text): basic punctuation/whitespace fixes
- segments_to_plain(segments): join candidate segments into one string
- placeholder speaker diarization hook (no external diarization dependency)
"""

from typing import List, Iterable
from ..core.schemas import TranscriptSegment
import re


def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"\s+", " ", t)  # collapse whitespace
    # basic punctuation fixes: ensure sentence ends have a space
    t = re.sub(r"\s*([.,;:!?])\s*", r"\1 ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def merge_adjacent_segments(segments: Iterable[TranscriptSegment], max_gap: float = 0.5) -> List[TranscriptSegment]:
    """
    Merge adjacent segments from the same speaker if the gap between them is <= max_gap seconds.
    Returns a new list of TranscriptSegment.
    """
    segs = sorted(list(segments), key=lambda s: (s.start, s.end))
    if not segs:
        return []
    out: List[TranscriptSegment] = []
    cur = TranscriptSegment(**segs[0].dict())
    for s in segs[1:]:
        if s.speaker == cur.speaker and (s.start - cur.end) <= max_gap:
            # merge
            cur.end = max(cur.end, s.end)
            cur.text = (cur.text.rstrip() + " " + s.text.lstrip()).strip()
        else:
            # finalize current
            cur.text = normalize_text(cur.text)
            out.append(cur)
            cur = TranscriptSegment(**s.dict())
    cur.text = normalize_text(cur.text)
    out.append(cur)
    return out


def segments_to_plain(segments: Iterable[TranscriptSegment], speaker: str = "candidate") -> str:
    """
    Join segments from `speaker` into a single normalized text string.
    """
    segs = [s for s in segments if s.speaker == speaker]
    segs = merge_adjacent_segments(segs)
    texts = [normalize_text(s.text) for s in segs if s.text]
    return " ".join(texts)


def diarize_placeholder(segments: Iterable[TranscriptSegment]) -> List[TranscriptSegment]:
    """
    Simple heuristic diarization placeholder:
    - If segments contain obvious interviewer markers ('interviewer', 'q:'), mark them.
    - Otherwise keep provided speaker labels.
    This is a no-op stub to be replaced with a real diarization step (pyannote.audio, whisperx, etc.).
    """
    out = []
    for s in segments:
        text_l = (s.text or "").lower()
        if "interviewer:" in text_l or text_l.startswith("q:") or "question:" in text_l:
            sp = "interviewer"
        elif "candidate:" in text_l or text_l.startswith("a:") or "answer:" in text_l:
            sp = "candidate"
        else:
            sp = s.speaker or "candidate"
        out.append(TranscriptSegment(start=s.start, end=s.end, speaker=sp, text=normalize_text(s.text)))
    return out