# backend/app/agent/graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from app.agent.nodes import (
    intake_node,
    risk_node,
    audit_node,
    compliance_node,
    human_review_node
)

class AgentState(TypedDict):
    application: dict
    application_id: Optional[int]
    original_premium: Optional[float]
    feature_importance: Optional[dict]
    audit_result: Optional[dict]
    final_decision: Optional[dict]
    error: Optional[str]


def route_after_audit(state: AgentState) -> str:
    """Route based on bias detection"""
    if state.get("audit_result") and state["audit_result"].get("needs_human_review"):
        return "human_review"
    return "compliance"


def build_graph():
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("intake", intake_node)
    graph.add_node("risk", risk_node)
    graph.add_node("audit", audit_node)
    graph.add_node("compliance", compliance_node)
    graph.add_node("human_review", human_review_node)

    # Flow
    graph.set_entry_point("intake")
    graph.add_edge("intake", "risk")
    graph.add_edge("risk", "audit")

    graph.add_conditional_edges(
        "audit",
        route_after_audit,
        {
            "human_review": "human_review",
            "compliance": "compliance",
        },
    )

    graph.add_edge("human_review", "compliance")
    graph.add_edge("compliance", END)

    return graph.compile()


agent_graph = build_graph()