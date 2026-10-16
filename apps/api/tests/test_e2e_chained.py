import pytest
import asyncio
from db.session import init_db, ensure_conversation, get_audit_logs_for_message
from routes.chat import chat_event_stream

@pytest.mark.asyncio
async def test_e2e_chained_query_and_audit_trail():
    """
    Mandatory Graded Requirement (Section 14):
    Execute full multi-step university query: 'What is the minimum attendance requirement, and is student STU-1001 eligible for final exams?'
    Assert that both a retrieval step and a tool-call step appear in the PostgreSQL audit log.
    """
    # 1. Initialize PostgreSQL schema
    init_db()

    # 2. Run chained query through the streaming pipeline
    conv_id = ensure_conversation(None)
    user_query = "What is the minimum attendance requirement, and is student STU-1001 eligible for final exams?"
    
    events = []
    final_message_id = None
    
    async for sse_chunk in chat_event_stream(conv_id, user_query):
        events.append(sse_chunk)
        if "final" in sse_chunk and "message_id" in sse_chunk:
            import json
            for line in sse_chunk.splitlines():
                if line.startswith("data: "):
                    payload = json.loads(line[len("data: "):])
                    final_message_id = payload.get("message_id")

    assert final_message_id is not None, "Final message ID was not emitted in stream."

    # 3. Query PostgreSQL AuditLog table for the generated assistant message
    audit_logs = get_audit_logs_for_message(final_message_id)
    step_types = [log["stepType"] for log in audit_logs]

    print(f"Recorded step types in PostgreSQL AuditLog: {step_types}")

    # Section 14 Assertions
    assert "plan" in step_types, "AuditLog must contain 'plan' step."
    assert "retrieval" in step_types, "AuditLog must contain 'retrieval' step for chained query."
    assert "tool_call" in step_types, "AuditLog must contain 'tool_call' step for student lookup."
    assert "final_answer" in step_types, "AuditLog must contain 'final_answer' step."
