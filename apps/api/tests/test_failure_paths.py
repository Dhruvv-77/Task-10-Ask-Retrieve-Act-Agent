import pytest
from rag.retrieve import retrieve_chunks
from mcp_client.client import call_mcp_tool
from agent.nodes.responder import responder_node
from agent.nodes.tool_executor import tool_executor_node

def test_failure_path_empty_retrieval():
    """Test when vector retrieval returns nothing above 0.65 threshold (Clarify path)."""
    res = retrieve_chunks("What is the recipe to make Italian pasta from scratch?")
    assert res["is_relevant"] is False
    assert res["top_score"] < 0.65

def test_failure_path_tool_failure():
    """Test when tool call returns structured error (e.g. student not found)."""
    tool_res = call_mcp_tool("student_lookup", {"student_id": "STU-9999_NON_EXISTENT"})
    assert "error" in tool_res
    assert tool_res["code"] == "STUDENT_NOT_FOUND"

    # Verify responder presents the error clearly rather than hallucinating
    state = {
        "user_query": "Check student STU-9999_NON_EXISTENT",
        "plan": {"decision": "tool_only", "tool_name": "student_lookup"},
        "retrieved_chunks": [],
        "tool_results": [{
            "tool": "student_lookup",
            "input": {"student_id": "STU-9999_NON_EXISTENT"},
            "output": tool_res
        }]
    }
    resp = responder_node(state)
    ans = resp["final_answer"].lower()
    assert any(phrase in ans for phrase in ["not found", "not been found", "no records were found", "no record", "not enrolled", "error"])

def test_failure_path_guardrail_confirmation_cycle():
    """Test guardrail round-trip: block on first turn, execute only on explicit confirmation."""
    # Turn 1: User requests course registration without confirmation
    state_turn1 = {
        "user_query": "Register student STU-1001 for course CS-301",
        "plan": {
            "decision": "tool_only",
            "tool_name": "register_course",
            "tool_args": {"student_id": "STU-1001", "course_code": "CS-301"}
        },
        "pending_confirmation": None
    }
    res_turn1 = tool_executor_node(state_turn1)
    assert res_turn1.get("pending_confirmation") is not None
    assert res_turn1["pending_confirmation"]["action"] == "register_course"
    assert "confirm" in res_turn1.get("final_answer", "").lower()
    assert len(res_turn1.get("tools_used", [])) == 0  # Tool execution was blocked

    # Turn 2: User explicitly confirms
    state_turn2 = {
        "user_query": "Yes, I confirm, please enroll me",
        "plan": {
            "decision": "tool_only",
            "tool_name": "register_course",
            "tool_args": {}
        },
        "pending_confirmation": res_turn1["pending_confirmation"]
    }
    res_turn2 = tool_executor_node(state_turn2)
    assert res_turn2.get("pending_confirmation") is None
    assert len(res_turn2.get("tool_results", [])) == 1
    assert res_turn2["tool_results"][0]["output"]["enrolled"] is True
    assert "register_course" in res_turn2.get("tools_used", [])
