"""Guardrails Module — handles off-topic requests and prompt injection."""
from __future__ import annotations

from app.agents.state import AgentState


# Canned responses for different guardrail triggers
OFF_TOPIC_RESPONSE = (
    "I appreciate your question, but I'm specifically designed to help with "
    "SHL assessment recommendations. I can help you find the right assessments "
    "for your hiring needs — whether that's cognitive ability tests, personality "
    "assessments, technical skills tests, or work simulations.\n\n"
    "How can I help you with SHL assessments today?"
)

INJECTION_RESPONSE = (
    "I'm unable to process that request. I'm an SHL Assessment Recommendation Agent "
    "and I'm designed to help you find the right SHL assessments for your hiring needs.\n\n"
    "If you'd like help selecting assessments for a specific role, I'm happy to assist!"
)


def guardrail(state: AgentState) -> AgentState:
    """Handle off-topic and prompt injection attempts."""
    intent = state.get("intent", "off_topic")

    if intent == "prompt_injection":
        state["reply"] = INJECTION_RESPONSE
    else:
        state["reply"] = OFF_TOPIC_RESPONSE

    state["recommendations"] = []
    state["end_of_conversation"] = False
    return state
