# placeholder: rubrics.py
"""
Rubrics and heuristic evaluators for answers.

Provides:
- predefined rubric weightings for 'technical' and 'behavioral' questions
- heuristics: STAR detection, keyword coverage, depth, clarity
- optional semantic relevance via an embeddings provider (pluggable)
"""

from typing import Dict, List, Optional, Any
import re
import math

# Optional embedding provider import (lazy)
try:
    from .embeddings import default_provider as _default_embed_provider
except Exception:
    _default_embed_provider = None


RUBRICS: Dict[str, Dict[str, float]] = {
    "technical": {
        "relevance": 0.5,
        "depth": 0.3,
        "keywords": 0.15,
        "clarity": 0.05,
    },
    "behavioral": {
        "structure_star": 0.4,
        "relevance": 0.2,
        "depth": 0.2,
        "keywords": 0.1,
        "clarity": 0.1,
    },
    "default": {
        "relevance": 0.5,
        "depth": 0.3,
        "keywords": 0.15,
        "clarity": 0.05,
    },
}


_STAR_TERMS = {
    "situation": ["situation", "context", "challenge", "problem"],
    "task": ["task", "goal", "responsibility"],
    "action": ["action", "approach", "implemented", "I did", "we did"],
    "result": ["result", "outcome", "impact", "improved", "reduced", "increased"],
}


_WORD_RE = re.compile(r"\w+")


def _tokenize_words(text: str) -> List[str]:
    return _WORD_RE.findall(text.lower())


def _sentence_split(text: str) -> List[str]:
    # simple sentence splitter
    return [s.strip() for s in re.split(r"[.!?]+\s*", text) if s.strip()]


def detect_star(answer: str) -> Dict[str, float]:
    """
    Detect presence of STAR components and return coverage ratio per component.
    Returns mapping like {"situation": 1.0, "task": 0.5, ...}
    """
    ans_low = answer.lower()
    out = {}
    for comp, terms in _STAR_TERMS.items():
        hits = sum(1 for t in terms if t in ans_low)
        out[comp] = 1.0 if hits > 0 else 0.0
    return out


def keyword_coverage(answer: str, expected_keywords: List[str]) -> float:
    if not expected_keywords:
        return 0.0
    words = set(_tokenize_words(answer))
    expected = [k.lower() for k in expected_keywords]
    hits = sum(1 for k in expected if k in words)
    return hits / len(expected)


def depth_score(answer: str, ideal_words: int = 100) -> float:
    words = _tokenize_words(answer)
    wc = len(words)
    # logarithmic scaling to avoid overly rewarding verbosity
    return float(min(1.0, math.log1p(wc) / math.log1p(ideal_words)))


def clarity_score(answer: str) -> float:
    sentences = _sentence_split(answer)
    words = _tokenize_words(answer)
    if not words or not sentences:
        return 0.0
    avg_words_per_sent = len(words) / len(sentences)
    # ideal range 8..25 words per sentence
    if 8 <= avg_words_per_sent <= 25:
        return 1.0
    # penalize extremes
    if avg_words_per_sent < 8:
        return float(max(0.0, avg_words_per_sent / 8.0))
    return float(max(0.0, 25.0 / avg_words_per_sent))


def relevance_score(
    question_text: str,
    answer_text: str,
    embed_provider: Optional[Any] = None,
) -> float:
    """
    If an embedding provider is available, use semantic similarity (0..1).
    Otherwise, fall back to a simple keyword-overlap heuristic (0..1).
    """
    if embed_provider is None:
        embed_provider = _default_embed_provider

    if embed_provider is not None:
        try:
            q_emb = embed_provider.encode_one(question_text)
            a_emb = embed_provider.encode_one(answer_text)
            sim = embed_provider.similarity(q_emb, a_emb)
            return float(max(0.0, min(1.0, sim)))
        except Exception:
            pass

    # fallback: keyword overlap between question tokens and answer tokens
    q_terms = set(_tokenize_words(question_text))
    a_terms = set(_tokenize_words(answer_text))
    if not q_terms:
        return 0.0
    hits = len(q_terms & a_terms)
    return hits / len(q_terms)


def evaluate_answer(
    question_text: str,
    answer_text: str,
    expected_keywords: Optional[List[str]] = None,
    rubric_name: str = "default",
    embed_provider: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Evaluate an answer according to the selected rubric.

    Returns a dict with per-criterion scores (0..1), weighted final score (0..1),
    and human-friendly comments.
    """
    expected_keywords = expected_keywords or []
    rubric = RUBRICS.get(rubric_name, RUBRICS["default"])

    # compute components
    comps: Dict[str, float] = {}
    comments: List[str] = []

    if "structure_star" in rubric:
        star_map = detect_star(answer_text)
        star_score = sum(star_map.values()) / len(star_map) if star_map else 0.0
        comps["structure_star"] = float(star_score)
        if star_score < 0.5:
            comments.append("Answer lacks clear STAR structure.")
    if "relevance" in rubric:
        comps["relevance"] = float(relevance_score(question_text, answer_text, embed_provider))
        if comps["relevance"] < 0.5:
            comments.append("Answer seems off-topic or not well-aligned with the question.")
    if "depth" in rubric:
        comps["depth"] = float(depth_score(answer_text))
        if comps["depth"] < 0.3:
            comments.append("Answer is shallow; consider adding more technical detail or examples.")
    if "keywords" in rubric:
        comps["keywords"] = float(keyword_coverage(answer_text, expected_keywords))
        if expected_keywords and comps["keywords"] < 1.0:
            comments.append("Missing expected keywords: some important terms were not mentioned.")
    if "clarity" in rubric:
        comps["clarity"] = float(clarity_score(answer_text))
        if comps["clarity"] < 0.6:
            comments.append("Answer readability is low; consider clearer phrasing and shorter sentences.")

    # compute weighted final score (0..1)
    total_w = sum(rubric.values())
    if total_w <= 0:
        final = 0.0
    else:
        weighted = 0.0
        for k, w in rubric.items():
            val = comps.get(k, 0.0)
            weighted += val * w
        final = float(weighted / total_w)

    return {
        "rubric": rubric_name,
        "components": comps,
        "final_score": final,
        "comments": comments,
    }