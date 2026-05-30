# placeholder: scoring.py
"""
Scoring formulas and helpers.

Contains:
- per-question scoring composition (semantic + keyword + optional time)
- weighted aggregation across questions into final score and per-skill breakdown
- utility to normalize scores to 0..100
"""

from typing import Dict, List, Any
import numpy as np

from ..core.config import settings
from ..core.schemas import Question, QuestionEvaluation


def compose_question_score(semantic_sim: float, keyword_score: float, time_score: float = 0.0,
                           semantic_w: float = None, keyword_w: float = None, time_w: float = 0.05) -> float:
    """
    Compose a single-question final score in 0..1 using configured weights.
    """
    sem_w = semantic_w if semantic_w is not None else float(settings.SEMANTIC_WEIGHT)
    kw_w = keyword_w if keyword_w is not None else float(settings.KEYWORD_WEIGHT)
    total = sem_w + kw_w + time_w
    if total <= 0:
        return 0.0
    val = (sem_w * semantic_sim + kw_w * keyword_score + time_w * time_score) / total
    return float(max(0.0, min(1.0, val)))


def aggregate_evaluations(evals: List[QuestionEvaluation], question_map: Dict[str, Question]) -> Dict[str, Any]:
    """
    Aggregate evaluations into final percent score and per-skill averages.

    Returns:
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