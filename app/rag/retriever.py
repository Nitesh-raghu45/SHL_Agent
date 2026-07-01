"""Retrieval module — wraps FAISS search with typed results."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.models.schema import Assessment
from app.rag.embeddings import embed_query
from app.rag.vector_store import load_index, search


def retrieve(query: str, top_k: int = 20) -> List[Assessment]:
    """Retrieve the top_k most relevant assessments for a query string."""
    query_vec = embed_query(query)
    results = search(query_vec, top_k=top_k)
    return [Assessment(**item) for item, _score in results]


def retrieve_by_name(name: str) -> Optional[Assessment]:
    """Retrieve a specific assessment by (partial) name match.

    Uses exact substring matching against the catalog metadata,
    not vector search — so it's precise.
    """
    _, metadata = load_index()
    name_lower = name.lower().strip()
    for item in metadata:
        if name_lower in item["name"].lower():
            return Assessment(**item)
    return None


def retrieve_multiple_by_names(names: List[str]) -> List[Assessment]:
    """Retrieve multiple assessments by name for comparison."""
    results = []
    for name in names:
        match = retrieve_by_name(name)
        if match:
            results.append(match)
    return results


def get_all_assessment_names() -> List[str]:
    """Return all assessment names in the catalog."""
    _, metadata = load_index()
    return [item["name"] for item in metadata]
