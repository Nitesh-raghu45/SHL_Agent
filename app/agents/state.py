"""Agent state definition for LangGraph."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from app.models.schema import Message, Recommendation


class AgentState(TypedDict, total=False):
    """State passed through the LangGraph agent nodes."""
    # Input
    messages: List[Dict[str, str]]       # Full conversation history

    # Routing
    intent: str                           # Classified intent

    # Processing
    requirements: str                     # Extracted search query
    retrieved_assessments: List[Dict]     # Raw retrieved catalog items

    # Output
    reply: str                            # Agent's text reply
    recommendations: List[Dict]           # Structured recommendations
    end_of_conversation: bool             # Whether conversation is done
