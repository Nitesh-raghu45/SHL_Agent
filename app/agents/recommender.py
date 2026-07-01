"""Recommendation Engine — extracts requirements, retrieves, ranks."""
from __future__ import annotations

import json
from typing import Dict, List

from app.agents.state import AgentState
from app.prompts.router_prompt import REQUIREMENT_EXTRACTION_PROMPT
from app.prompts.recommend_prompt import RECOMMEND_PROMPT, RANKING_PROMPT
from app.rag.retriever import retrieve, retrieve_by_name
from app.utils.helpers import llm_invoke


def _format_conversation(messages: list) -> str:
    lines = []
    for msg in messages:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _format_assessments(assessments) -> str:
    """Format assessment list for LLM context."""
    parts = []
    for i, a in enumerate(assessments, 1):
        if hasattr(a, "model_dump"):
            a = a.model_dump()
        parts.append(
            f"{i}. **{a['name']}**\n"
            f"   URL: {a['url']}\n"
            f"   Description: {a['description']}\n"
            f"   Test Type: {', '.join(a.get('test_type', []))}\n"
            f"   Skills: {', '.join(a.get('skills', []))}\n"
            f"   Duration: {a.get('duration', 'N/A')}\n"
            f"   Job Families: {', '.join(a.get('job_families', []))}"
        )
    return "\n\n".join(parts)


def _extract_top_names(raw: str, assessments) -> List[str]:
    """Parse the LLM's ranked JSON array of assessment names."""
    try:
        # Try to parse JSON array from the response
        # Handle cases where LLM wraps in markdown code blocks
        cleaned = raw.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        names = json.loads(cleaned)
        if isinstance(names, list):
            return [str(n) for n in names[:5]]
    except (json.JSONDecodeError, IndexError):
        pass

    # Fallback: return first 5 assessment names from retrieved list
    return [
        a.name if hasattr(a, "name") else a["name"]
        for a in assessments[:5]
    ]


def recommend(state: AgentState) -> AgentState:
    """Full recommendation pipeline: extract → retrieve → rank → respond."""
    conversation = _format_conversation(state["messages"])

    # Step 1: Extract requirements from conversation
    req_prompt = REQUIREMENT_EXTRACTION_PROMPT.format(conversation=conversation)
    requirements = llm_invoke(req_prompt)
    state["requirements"] = requirements

    # Step 2: Retrieve top 20 from FAISS
    retrieved = retrieve(requirements, top_k=20)
    state["retrieved_assessments"] = [a.model_dump() for a in retrieved]

    # Step 3: LLM ranks and picks top 5
    assessments_text = _format_assessments(retrieved)
    ranking_raw = llm_invoke(
        RANKING_PROMPT.format(
            requirements=requirements,
            assessments=assessments_text,
        )
    )
    top_names = _extract_top_names(ranking_raw, retrieved)

    # Step 4: Build structured recommendations from catalog data
    recommendations = []
    for name in top_names:
        match = retrieve_by_name(name)
        if match:
            recommendations.append({
                "name": match.name,
                "url": match.url,
                "test_type": ", ".join(match.test_type),
            })

    # If ranking failed to match names, fall back to first 5 retrieved
    if not recommendations:
        for a in retrieved[:5]:
            recommendations.append({
                "name": a.name,
                "url": a.url,
                "test_type": ", ".join(a.test_type),
            })

    state["recommendations"] = recommendations

    # Step 5: Generate natural language reply
    reply_prompt = RECOMMEND_PROMPT.format(
        conversation=conversation,
        assessments=assessments_text,
    )
    reply = llm_invoke(reply_prompt)
    state["reply"] = reply
    state["end_of_conversation"] = False

    return state
