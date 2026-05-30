# placeholder: embeddings.py
"""
Embeddings adapter utilities.

Provides a lightweight wrapper around sentence-transformers for:
- lazy model loading
- batch encoding to numpy arrays
- cosine similarity helpers

Make it easy to swap in another provider later by replacing the internal
implementation (keep function signatures stable).
"""

from typing import List, Optional, Union
import threading

import numpy as np

from ..core.config import settings

# Lazy-loaded model and lock for thread safety
_MODEL = None
_MODEL_LOCK = threading.Lock()


def _load_sbert_model(model_name: Optional[str] = None):
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _MODEL_LOCK:
        if _MODEL is not None:
            return _MODEL
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            raise RuntimeError(
                "sentence-transformers is required for the default embedding provider. "
                "Install it (pip install sentence-transformers) or configure another provider."
            ) from exc
        name = model_name or settings.EMBED_MODEL
        _MODEL = SentenceTransformer(name)
        return _MODEL


def embed_texts(texts: List[str], model_name: Optional[str] = None) -> np.ndarray:
    """
    Encode a list of strings into a 2D numpy array of embeddings.

    Returns:
        embeddings: np.ndarray shape (len(texts), dim)
    """
    if not texts:
        return np.zeros((0, 0), dtype=float)
    model = _load_sbert_model(model_name)
    emb = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    # Ensure numpy array
    return np.asarray(emb)


def embed_text(text: str, model_name: Optional[str] = None) -> np.ndarray:
    """
    Encode a single string and return a 1D numpy array.
    """
    arr = embed_texts([text], model_name=model_name)
    if arr.size == 0:
        return np.zeros((0,), dtype=float)
    return arr[0]


def _normalize(v: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    denom = np.linalg.norm(v, axis=-1, keepdims=True)
    denom = np.maximum(denom, eps)
    return v / denom


def cosine_similarity(a: Union[np.ndarray, List[float]], b: Union[np.ndarray, List[float]]) -> float:
    """
    Compute cosine similarity between two 1-D vectors.
    If 2D arrays are provided, returns the mean pairwise similarity.
    """
    a_arr = np.asarray(a)
    b_arr = np.asarray(b)
    if a_arr.ndim == 1 and b_arr.ndim == 1:
        a_n = _normalize(a_arr)
        b_n = _normalize(b_arr)
        return float(np.dot(a_n, b_n))
    # support (N, D) vs (M, D) -> return mean of pairwise dot-products
    a_n = _normalize(a_arr)
    b_n = _normalize(b_arr)
    sim_matrix = np.matmul(a_n, b_n.T)
    return float(np.mean(sim_matrix))


class EmbeddingProvider:
    """
    Simple provider class to keep interface stable.
    Currently uses SBERT under the hood.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBED_MODEL

    def encode(self, texts: List[str]) -> np.ndarray:
        return embed_texts(texts, model_name=self.model_name)

    def encode_one(self, text: str) -> np.ndarray:
        return embed_text(text, model_name=self.model_name)

    def similarity(self, a: Union[np.ndarray, List[float]], b: Union[np.ndarray, List[float]]) -> float:
        return cosine_similarity(a, b)


# Convenience singleton
default_provider = EmbeddingProvider()