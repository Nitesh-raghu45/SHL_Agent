"""Embedding model wrapper using sentence-transformers (BAAI/bge-small-en-v1.5)."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

import numpy as np

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIM = 384  # bge-small-en-v1.5 output dimension


@lru_cache(maxsize=1)
def _get_model():
    """Lazy-load and cache the SentenceTransformer model."""
    from sentence_transformers import SentenceTransformer
    print(f"[INFO] Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    return model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a list of texts and return a numpy array of shape (n, dim).

    Uses instruction prefix for better retrieval quality with bge models.
    """
    model = _get_model()
    # bge models benefit from a query instruction prefix
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 10,
        batch_size=32,
    )
    return np.array(embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string (with retrieval prefix)."""
    model = _get_model()
    # bge recommends prepending "Represent this sentence:" for queries
    prefixed = f"Represent this sentence: {query}"
    embedding = model.encode(
        [prefixed],
        normalize_embeddings=True,
    )
    return np.array(embedding, dtype=np.float32)
