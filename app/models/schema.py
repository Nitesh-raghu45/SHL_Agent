"""Pydantic models for API request/response and internal data."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Internal data model — represents one SHL catalog assessment
# ---------------------------------------------------------------------------
class Assessment(BaseModel):
    """A single SHL assessment from the scraped catalog."""
    name: str
    url: str
    description: str = ""
    test_type: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    duration: str = ""
    remote_testing: bool = False
    adaptive_irt: bool = False
    job_families: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API models — strict contract for /chat endpoint
# ---------------------------------------------------------------------------
class Message(BaseModel):
    """A single message in the conversation."""
    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    """POST /chat request body."""
    messages: List[Message]


class Recommendation(BaseModel):
    """A single assessment recommendation returned to the user."""
    name: str
    url: str
    test_type: str


class ChatResponse(BaseModel):
    """POST /chat response body."""
    reply: str
    recommendations: List[Recommendation] = Field(default_factory=list)
    end_of_conversation: bool = False
