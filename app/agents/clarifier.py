"""Clarification Engine — asks follow-up questions when request is vague."""
from __future__ import annotations

from app.agents.state import AgentState
from app.prompts.clarify_prompt import CLARIFY_PROMPT
from app.utils.helpers import llm_invoke


def _format_conversation(messages: list) -> str:
    lines = []
    for msg in messages:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def clarify(state: AgentState) -> AgentState:
    """Generate a clarifying question for the user."""
    conversation = _format_conversation(state["messages"])
    prompt = CLARIFY_PROMPT.format(conversation=conversation)

    reply = llm_invoke(prompt)

    state["reply"] = reply
    state["recommendations"] = []
    state["end_of_conversation"] = False
    return state
