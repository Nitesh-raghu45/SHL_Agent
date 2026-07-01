"""FAISS vector store for SHL catalog embeddings.

Build, save, and load a FAISS index with metadata mapping.

Usage:
    python -m app.rag.vector_store          # Build index from catalog
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import numpy as np

from app.models.schema import Assessment
from app.rag.embeddings import EMBEDDING_DIM, embed_texts

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CATALOG_FILE = DATA_DIR / "shl_catalog.json"
FAISS_INDEX_FILE = DATA_DIR / "catalog.faiss"
METADATA_FILE = DATA_DIR / "catalog_metadata.json"


def _assessment_to_text(item: Dict) -> str:
    """Convert an assessment dict to a single text for embedding.

    Combines all relevant fields for rich semantic representation.
    """
    parts = [
        item.get("name", ""),
        item.get("description", ""),
        f"Test type: {', '.join(item.get('test_type', []))}",
        f"Skills: {', '.join(item.get('skills', []))}",
        f"Duration: {item.get('duration', '')}",
        f"Job families: {', '.join(item.get('job_families', []))}",
    ]
    return " | ".join(p for p in parts if p)


def build_index() -> Tuple[faiss.IndexFlatIP, List[Dict]]:
    """Build a FAISS index from the SHL catalog JSON."""
    print(f"[INFO] Loading catalog from {CATALOG_FILE}")
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        catalog: List[Dict] = json.load(f)

    texts = [_assessment_to_text(item) for item in catalog]
    print(f"[INFO] Embedding {len(texts)} assessments...")
    embeddings = embed_texts(texts)

    # Inner product index (cosine similarity since embeddings are normalized)
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(embeddings)
    print(f"[INFO] FAISS index built with {index.ntotal} vectors")

    return index, catalog


def save_index(index: faiss.IndexFlatIP, metadata: List[Dict]) -> None:
    """Save FAISS index and metadata to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_FILE))
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Saved FAISS index to {FAISS_INDEX_FILE}")
    print(f"[INFO] Saved metadata to {METADATA_FILE}")


@lru_cache(maxsize=1)
def load_index() -> Tuple[faiss.IndexFlatIP, List[Dict]]:
    """Load FAISS index and metadata from disk.

    Falls back to building from scratch if files don't exist.
    """
    if FAISS_INDEX_FILE.exists() and METADATA_FILE.exists():
        print(f"[INFO] Loading FAISS index from {FAISS_INDEX_FILE}")
        index = faiss.read_index(str(FAISS_INDEX_FILE))
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"[INFO] Loaded {index.ntotal} vectors")
        return index, metadata

    print("[INFO] No saved index found, building from catalog...")
    index, metadata = build_index()
    save_index(index, metadata)
    return index, metadata


def search(query_embedding: np.ndarray, top_k: int = 20) -> List[Tuple[Dict, float]]:
    """Search the FAISS index and return top_k results with scores."""
    index, metadata = load_index()
    scores, indices = index.search(query_embedding, min(top_k, index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        results.append((metadata[idx], float(score)))

    return results


# ---------------------------------------------------------------------------
# CLI entry point: build the index
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    idx, meta = build_index()
    save_index(idx, meta)
    print(f"[DONE] Index ready with {idx.ntotal} assessments")
