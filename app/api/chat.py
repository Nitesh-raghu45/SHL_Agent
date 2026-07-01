"""Chat endpoint — main conversation interface."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schema import ChatRequest, ChatResponse, Recommendation
from app.agents.graph import run_agent

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return recommendations.

    Accepts the full conversation history and returns a reply
    with optional assessment recommendations.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty")

    # Convert Pydantic models to dicts for the agent
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        # Run the LangGraph agent
        result = run_agent(messages)

        # Build structured recommendations
        recommendations = []
        for rec in result.get("recommendations", []):
            recommendations.append(
                Recommendation(
                    name=rec.get("name", ""),
                    url=rec.get("url", ""),
                    test_type=rec.get("test_type", ""),
                )
            )

        return ChatResponse(
            reply=result.get("reply", "I'm sorry, I couldn't process your request. Please try again."),
            recommendations=recommendations,
            end_of_conversation=result.get("end_of_conversation", False),
        )

    except Exception as e:
        # Log the error but return a graceful response
        print(f"[ERROR] Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            reply="I'm experiencing a technical issue. Please try again in a moment.",
            recommendations=[],
            end_of_conversation=False,
        )
