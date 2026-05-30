# placeholder: __init__.py
from .embeddings import default_provider, EmbeddingProvider, embed_text, embed_texts, cosine_similarity
from .evaluator import eval_answer, aggregate
from .rubrics import evaluate_answer, RUBRICS
from .scoring import compose_question_score, aggregate_evaluations

__all__ = [
    "default_provider",
    "EmbeddingProvider",
    "embed_text",
    "embed_texts",
    "cosine_similarity",
    "eval_answer",
    "aggregate",
    "evaluate_answer",
    "RUBRICS",
    "compose_question_score",
    "aggregate_evaluations",
]