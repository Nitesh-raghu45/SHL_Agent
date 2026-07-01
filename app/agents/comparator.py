"""Comparison Engine — grounded comparison of specific SHL assessments."""
from __future__ import annotations

import json
from typing import List

from app.agents.state import AgentState
from app.prompts.compare_prompt import COMPARE_PROMPT, EXTRACT_NAMES_PROMPT
from app.rag.retriever import retrieve_by_name, retrieve_multiple_by_names, get_all_assessment_names
from app.utils.helpers import llm_invoke


def _format_conversation(messages: list) -> str:
    lines = []
    for msg in messages:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _extract_assessment_names(message: str) -> List[str]:
    """Use LLM to fuzzy-match assessment names from user message."""
    available = get_all_assessment_names()
    prompt = EXTRACT_NAMES_PROMPT.format(
        message=message,
        available_names="\n".join(f"- {n}" for n in available),
    )
    raw = llm_invoke(prompt)

    try:
        cleaned = raw.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        names = json.loads(cleaned)
        if isinstance(names, list):
            return [str(n) for n in names]
    except (json.JSONDecodeError, IndexError):
        pass

    return []


def _format_assessments_detail(assessments) -> str:
    """Format assessments with full detail for comparison."""
    parts = []
    for a in assessments:
        if hasattr(a, "model_dump"):
            a = a.model_dump()
        parts.append(
            f"### {a['name']}\n"
            f"- **URL:** {a['url']}\n"
            f"- **Description:** {a['description']}\n"
            f"- **Test Type:** {', '.join(a.get('test_type', []))}\n"
            f"- **Skills Measured:** {', '.join(a.get('skills', []))}\n"
            f"- **Duration:** {a.get('duration', 'N/A')}\n"
            f"- **Remote Testing:** {'Yes' if a.get('remote_testing') else 'No'}\n"
            f"- **Adaptive/IRT:** {'Yes' if a.get('adaptive_irt') else 'No'}\n"
            f"- **Job Families:** {', '.join(a.get('job_families', []))}"
        )
    return "\n\n".join(parts)


def compare(state: AgentState) -> AgentState:
    """Compare specific SHL assessments mentioned by the user."""
    # Get the latest user message
    latest_msg = ""
    for msg in reversed(state["messages"]):
        if msg.get("role") == "user":
            latest_msg = msg["content"]
            break

    # Extract assessment names using LLM
    names = _extract_assessment_names(latest_msg)

    # Retrieve the matching assessments
    assessments = retrieve_multiple_by_names(names)

    if len(assessments) < 2:
        # If we couldn't find enough assessments, ask for clarification
        state["reply"] = (
            "I'd be happy to compare SHL assessments for you. However, I couldn't identify "
            "the specific assessments you're referring to. Could you please specify the exact "
            "assessment names you'd like to compare? For example: 'Compare OPQ32 with Verify G+'"
        )
        state["recommendations"] = []
        state["end_of_conversation"] = False
        return state

    # Format and compare
    assessments_text = _format_assessments_detail(assessments)
    prompt = COMPARE_PROMPT.format(assessments=assessments_text)
    reply = llm_invoke(prompt)

    # Build recommendation entries for the compared assessments
    recommendations = []
    for a in assessments:
        recommendations.append({
            "name": a.name,
            "url": a.url,
            "test_type": ", ".join(a.test_type),
        })

    state["reply"] = reply
    state["recommendations"] = recommendations
    state["end_of_conversation"] = False
    return state
