# placeholder: evaluator.py
"""
Answer evaluation orchestration.

- Computes semantic similarity using the embeddings provider.
- Computes keyword coverage.
- Optionally factors answer duration into scoring.
- Exposes helpers to aggregate per-question evaluations into a final report.
"""

from typing import List, Dict, Optional
import numpy as np

from ..core.config import settings
from ..core.schemas import Question, QuestionEvaluation
from .embeddings import default_provider


def _keyword_score(answer: str, expected_keywords: List[str]) -> float:
    if not expected_keywords:
        return 0.0
    ans_low = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in ans_low)
    return hits / len(expected_keywords)


def _time_score(time_sec: float, min_seconds: float = 10.0, ideal_seconds: float = 120.0) -> float:
    if time_sec <= 0:
        return 0.0
    # score 0.0..1.0 where answers shorter than min_seconds score low,
    # answers >= ideal_seconds saturate at 1.0
    if time_sec < min_seconds:
        return time_sec / min_seconds * 0.5  # penalize very short answers
    return min(1.0, time_sec / ideal_seconds)


def eval_answer(question: Question, answer_text: str, time_sec: float = 0.0) -> QuestionEvaluation:
    """
    Evaluate a single answer.

    Returns a QuestionEvaluation (scores in 0..1 for semantic_sim/keyword_score, final_score 0..1).
    """
    # semantic similarity (0..1)
    try:
        q_emb = default_provider.encode_one(question.text)
        a_emb = default_provider.encode_one(answer_text)
        semantic_sim = default_provider.similarity(q_emb, a_emb)
        # clamp to [0,1]
        semantic_sim = max(0.0, min(1.0, float(semantic_sim)))
    except Exception:
        semantic_sim = 0.0

    keyword_score = _keyword_score(answer_text, question.expected_keywords or [])
    time_component = _time_score(time_sec)

    # Combine weights from settings
    sem_w = float(settings.SEMANTIC_WEIGHT)
    kw_w = float(settings.KEYWORD_WEIGHT)
    # Optionally incorporate a small time factor (kept low-weighted)
    time_w = 0.05
    total_w = sem_w + kw_w + time_w
    final_score = (sem_w * semantic_sim + kw_w * keyword_score + time_w * time_component) / total_w
    final_score = max(0.0, min(1.0, float(final_score)))

    metrics = {
        "semantic_sim": semantic_sim,
        "keyword_score": keyword_score,
        "time_score": time_component,
    }

    return QuestionEvaluation(
        question_id=question.question_id,
        semantic_sim=float(semantic_sim),
        keyword_score=float(keyword_score),
        time_sec=float(time_sec),
        final_score=float(final_score),
        comments=[],
        metrics=metrics
    )


def aggregate(evals: List[QuestionEvaluation], question_map: Dict[str, Question]) -> Dict:
    """
    Aggregate a list of QuestionEvaluation into overall scores.

    Returns a dict:
      {
        "final_score": float (0..100),
        "per_skill": {skill: float (0..100)},
        "details": {question_id: evaluation.dict()}
      }
    """
    if not evals:
        return {"final_score": 0.0, "per_skill": {}, "details": {}}

    total_weight = 0.0
    weighted_sum = 0.0
    per_skill_scores: Dict[str, List[float]] = {}
    details = {}

    for e in evals:
        q = question_map.get(e.question_id)
        w = getattr(q, "weight", float(settings.DEFAULT_QUESTION_WEIGHT))
        weighted_sum += e.final_score * w
        total_weight += w
        skill = (q.skill or "general")
        per_skill_scores.setdefault(skill, []).append(e.final_score * 100.0)
        details[e.question_id] = e.dict()

    final_pct = (weighted_sum / total_weight) * 100.0 if total_weight > 0 else 0.0
    per_skill_avg = {k: float(np.mean(v)) if v else 0.0 for k, v in per_skill_scores.items()}

    return {"final_score": float(final_pct), "per_skill": per_skill_avg, "details": details}