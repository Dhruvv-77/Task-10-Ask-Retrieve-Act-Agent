import pytest
from agent.nodes.planner import planner_node
from agent.nodes.retriever import retriever_node
from agent.nodes.tool_executor import tool_executor_node
from agent.nodes.responder import responder_node
from agent.nodes.clarify import clarify_node

def test_planner_node_greeting():
    res = planner_node({"user_query": "Hello there! What can you help me with?"})
    assert res["plan"]["decision"] == "answer_directly"

def test_planner_node_university_chained():
    res = planner_node({"user_query": "What is the minimum attendance requirement, and is student STU-1001 eligible for final exams?"})
    assert res["plan"]["decision"] in ("retrieve_and_tool_call", "retrieve_and_tool")
    assert res["plan"]["tool_name"] == "student_lookup"

def test_planner_node_student_tool_only():
    res = planner_node({"user_query": "Lookup student STU-1001"})
    assert res["plan"]["decision"] == "tool_only"
    assert res["plan"]["tool_name"] == "student_lookup"

def test_planner_node_course_tool_only():
    res = planner_node({"user_query": "Check seats in CS-301"})
    assert res["plan"]["decision"] == "tool_only"
    assert res["plan"]["tool_name"] == "course_lookup"

def test_planner_node_policy_only():
    res = planner_node({"user_query": "What are the add/drop deadlines for courses this semester?"})
    assert res["plan"]["decision"] == "retrieve_only"

def test_tool_executor_register_course_guardrail_unconfirmed():
    state = {
        "user_query": "Register student STU-1001 for course CS-301",
        "plan": {
            "decision": "tool_only",
            "tool_name": "register_course",
            "tool_args": {"student_id": "STU-1001", "course_code": "CS-301"}
        },
        "pending_confirmation": None
    }
    res = tool_executor_node(state)
    assert res.get("pending_confirmation") is not None
    assert "confirm" in res.get("final_answer", "").lower()
    assert len(res.get("tools_used", [])) == 0  # Blocked by guardrail until confirmed

def test_tool_executor_register_course_guardrail_confirmed():
    state = {
        "user_query": "Yes, confirm course registration",
        "plan": {
            "decision": "tool_only",
            "tool_name": "register_course",
            "tool_args": {}
        },
        "pending_confirmation": {
            "action": "register_course",
            "payload": {"student_id": "STU-1001", "course_code": "CS-301"}
        }
    }
    res = tool_executor_node(state)
    assert len(res.get("tool_results", [])) == 1
    assert res["tool_results"][0]["output"]["enrolled"] is True
    assert res.get("pending_confirmation") is None

def test_responder_node_university_synthesis():
    state = {
        "user_query": "Attendance eligibility for STU-1001",
        "plan": {"decision": "retrieve_and_tool_call"},
        "retrieved_chunks": [{
            "docId": "policy-002",
            "title": "Attendance Policy",
            "text": "75% minimum attendance required to sit for final semester examinations.",
            "score": 0.85
        }],
        "tool_results": [{
            "tool": "student_lookup",
            "output": {
                "student_id": "STU-1001",
                "name": "Aarav Patel",
                "major": "Computer Science",
                "cumulative_gpa": 3.85,
                "attendance_pct": 88,
                "eligible_for_exams": True
            }
        }],
        "needs_clarification": False
    }
    res = responder_node(state)
    assert "STU-1001" in res["final_answer"] or "Aarav Patel" in res["final_answer"]
    assert "policy-002" in res["sources_used"]
    assert "student_lookup" in res["tools_used"]
