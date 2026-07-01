"""LangGraph Agent — wires all nodes into a state machine.

Flow:
    START → router → [clarifier | recommender | comparator | recommender(refinement) | guardrail] → END
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.router import route_intent
from app.agents.clarifier import clarify
from app.agents.recommender import recommend
from app.agents.comparator import compare
from app.agents.guardrails import guardrail


def _route_by_intent(state: AgentState) -> str:
    """Conditional edge: route to the appropriate handler based on intent."""
    intent = state.get("intent", "clarification")

    if intent == "clarification":
        return "clarifier"
    elif intent == "recommendation":
        return "recommender"
    elif intent == "comparison":
        return "comparator"
    elif intent == "refinement":
        # Refinement reuses the recommender — it extracts previous context
        # from conversation history and merges with new constraints
        return "recommender"
    elif intent in ("off_topic", "prompt_injection"):
        return "guardrail"
    else:
        return "clarifier"  # Safe fallback


def build_graph() -> StateGraph:
    """Build and compile the LangGraph agent."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", route_intent)
    graph.add_node("clarifier", clarify)
    graph.add_node("recommender", recommend)
    graph.add_node("comparator", compare)
    graph.add_node("guardrail", guardrail)

    # Set entry point
    graph.set_entry_point("router")

    # Conditional routing from router
    graph.add_conditional_edges(
        "router",
        _route_by_intent,
        {
            "clarifier": "clarifier",
            "recommender": "recommender",
            "comparator": "comparator",
            "guardrail": "guardrail",
        },
    )

    # All handler nodes go to END
    graph.add_edge("clarifier", END)
    graph.add_edge("recommender", END)
    graph.add_edge("comparator", END)
    graph.add_edge("guardrail", END)

    return graph.compile()


# Singleton compiled graph
_agent = None


def get_agent():
    """Get the compiled LangGraph agent (singleton)."""
    global _agent
    if _agent is None:
        _agent = build_graph()
    return _agent


def run_agent(messages: list) -> AgentState:
    """Run the agent with a list of messages and return the final state."""
    agent = get_agent()
    initial_state: AgentState = {
        "messages": messages,
        "intent": "",
        "requirements": "",
        "retrieved_assessments": [],
        "reply": "",
        "recommendations": [],
        "end_of_conversation": False,
    }
    result = agent.invoke(initial_state)
    return result
