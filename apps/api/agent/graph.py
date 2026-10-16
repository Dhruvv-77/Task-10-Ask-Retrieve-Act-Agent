import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes.planner import planner_node
from agent.nodes.retriever import retriever_node
from agent.nodes.tool_executor import tool_executor_node
from agent.nodes.responder import responder_node
from agent.nodes.clarify import clarify_node

logger = logging.getLogger("agent.graph")

def route_after_planner(state: AgentState) -> Literal["retriever", "tool_executor", "retriever_and_tool", "responder", "clarify"]:
    plan = state.get("plan", {})
    decision = plan.get("decision", "insufficient_info")
    
    if decision in ("retrieve_and_tool", "retrieve_and_tool_call"):
        return "retriever_and_tool"
    elif decision == "retrieve_only":
        return "retriever"
    elif decision == "tool_only":
        return "tool_executor"
    elif decision == "answer_directly":
        return "responder"
    else:
        return "clarify"

def route_after_retriever(state: AgentState) -> Literal["responder", "clarify", "tool_executor"]:
    plan = state.get("plan", {})
    decision = plan.get("decision", "")
    
    # If chained, proceed to tool_executor
    if decision in ("retrieve_and_tool", "retrieve_and_tool_call"):
        return "tool_executor"
    
    # If retrieval flagged for clarification
    if state.get("needs_clarification"):
        return "clarify"
        
    return "responder"

def route_after_responder(state: AgentState) -> Literal["clarify", "end"]:
    if state.get("needs_clarification") and not state.get("final_answer"):
        return "clarify"
    return "end"

def build_agent_graph():
    """Construct and compile the LangGraph agent state machine."""
    workflow = StateGraph(AgentState)

    # 1. Register Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("responder", responder_node)
    workflow.add_node("clarify", clarify_node)

    # 2. Set Entry Point
    workflow.set_entry_point("planner")

    # 3. Add Conditional Routing from Planner
    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "retriever": "retriever",
            "tool_executor": "tool_executor",
            "retriever_and_tool": "retriever",
            "responder": "responder",
            "clarify": "clarify"
        }
    )

    # 4. Routing from Retriever
    workflow.add_conditional_edges(
        "retriever",
        route_after_retriever,
        {
            "tool_executor": "tool_executor",
            "responder": "responder",
            "clarify": "clarify"
        }
    )

    # 5. Routing from Tool-Executor -> Responder
    workflow.add_edge("tool_executor", "responder")

    # 6. Routing from Responder -> END or Clarify
    workflow.add_conditional_edges(
        "responder",
        route_after_responder,
        {
            "clarify": "clarify",
            "end": END
        }
    )

    # 7. Routing from Clarify -> END
    workflow.add_edge("clarify", END)

    return workflow.compile()

agent_app = build_agent_graph()
