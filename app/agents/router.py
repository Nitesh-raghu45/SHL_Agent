"""Intent Router — classifies user messages into actionable intents."""
from __future__ import annotations

from app.agents.state import AgentState
from app.prompts.router_prompt import ROUTER_PROMPT
from app.utils.helpers import llm_invoke


VALID_INTENTS = {
    "clarification",
    "recommendation",
    "comparison",
    "refinement",
    "off_topic",
    "prompt_injection",
}


def _format_conversation(messages: list) -> str:
    """Format message list into readable conversation string."""
    lines = []
    for msg in messages:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def route_intent(state: AgentState) -> AgentState:
    """Classify the user's latest message intent."""
    conversation = _format_conversation(state["messages"])
    prompt = ROUTER_PROMPT.format(conversation=conversation)

    raw_intent = llm_invoke(prompt).lower().strip().strip('"').strip("'")

    # Normalize — fall back to clarification if LLM gives unexpected output
    if raw_intent not in VALID_INTENTS:
        # Try partial match
        for valid in VALID_INTENTS:
            if valid in raw_intent:
                raw_intent = valid
                break
        else:
            raw_intent = "clarification"

    state["intent"] = raw_intent
    return state
