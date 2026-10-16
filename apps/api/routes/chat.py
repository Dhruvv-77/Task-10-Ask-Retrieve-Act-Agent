import json
import logging
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from db.session import (
    ensure_conversation,
    save_message,
    save_audit_log,
    get_conversation_history
)
from agent.graph import agent_app
from agent.state import AgentState

logger = logging.getLogger("routes.chat")
router = APIRouter()

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str

async def chat_event_stream(conv_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """Execute LangGraph and stream intermediate step events via SSE."""
    # 1. Persist User Message
    user_msg_id = save_message(conv_id, "user", user_message)

    # 2. Prepare AgentState
    history = get_conversation_history(conv_id, limit=6)
    initial_state: AgentState = {
        "conversation_id": conv_id,
        "user_query": user_message,
        "chat_history": history,
        "plan": None,
        "retrieved_chunks": None,
        "tool_results": None,
        "final_answer": None,
        "needs_clarification": False,
        "clarification_question": None,
        "pending_confirmation": None,
        "sources_used": [],
        "tools_used": []
    }

    # Helper function to format SSE messages
    def sse(event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    # 3. Stream graph execution steps
    final_content = ""
    sources_used = []
    tools_used = []
    assistant_msg_id = None

    try:
        # Stream intermediate graph outputs
        accumulated_state = dict(initial_state)

        for event in agent_app.stream(initial_state):
            for node_name, node_output in event.items():
                accumulated_state.update(node_output)

                # Emit Step Events
                if node_name == "planner" and "plan" in node_output:
                    plan_data = node_output["plan"]
                    yield sse("step", {
                        "type": "step",
                        "step": "plan",
                        "detail": {
                            "decision": plan_data.get("decision"),
                            "reasoning": plan_data.get("reasoning")
                        }
                    })

                elif node_name == "retriever" and "retrieved_chunks" in node_output:
                    chunks = node_output.get("retrieved_chunks", [])
                    yield sse("step", {
                        "type": "step",
                        "step": "retrieval",
                        "detail": {
                            "query": user_message,
                            "chunks": [
                                {"docId": c.get("docId"), "text": c.get("text")[:200], "score": c.get("score")}
                                for c in chunks
                            ]
                        }
                    })

                elif node_name == "tool_executor" and "tool_results" in node_output:
                    results = node_output.get("tool_results", [])
                    for t_res in results:
                        yield sse("step", {
                            "type": "step",
                            "step": "tool_call",
                            "detail": {
                                "tool": t_res.get("tool"),
                                "input": t_res.get("input"),
                                "output": t_res.get("output")
                            }
                        })

                elif node_name == "clarify" and "clarification_question" in node_output:
                    yield sse("step", {
                        "type": "step",
                        "step": "clarify",
                        "detail": {
                            "reason": "clarification_needed",
                            "question_asked": node_output.get("clarification_question")
                        }
                    })

        final_content = accumulated_state.get("final_answer") or "I could not formulate an answer for this query."
        sources_used = accumulated_state.get("sources_used") or []
        tools_used = accumulated_state.get("tools_used") or []
        needs_clarification = accumulated_state.get("needs_clarification", False)

        # 4. Persist Assistant Message
        assistant_msg_id = save_message(conv_id, "assistant", final_content)

        # 5. Persist Full AuditLog Trail into PostgreSQL
        if accumulated_state.get("plan"):
            save_audit_log(assistant_msg_id, "plan", {
                "decision": accumulated_state["plan"].get("decision"),
                "reasoning": accumulated_state["plan"].get("reasoning")
            })

        if accumulated_state.get("retrieved_chunks") is not None or (accumulated_state.get("plan") and "retrieve" in str(accumulated_state["plan"].get("decision", ""))):
            chunks_to_log = accumulated_state.get("retrieved_chunks") or []
            save_audit_log(assistant_msg_id, "retrieval", {
                "query": user_message,
                "chunks": [
                    {"docId": c.get("docId"), "text": c.get("text", "")[:200], "score": c.get("score")}
                    for c in chunks_to_log
                ]
            })

        if accumulated_state.get("tool_results"):
            for t_res in accumulated_state["tool_results"]:
                save_audit_log(assistant_msg_id, "tool_call", {
                    "tool": t_res.get("tool"),
                    "input": t_res.get("input"),
                    "output": t_res.get("output")
                })

        if needs_clarification:
            save_audit_log(assistant_msg_id, "clarify", {
                "reason": "missing_or_low_confidence_context",
                "question_asked": accumulated_state.get("clarification_question", final_content)
            })

        save_audit_log(assistant_msg_id, "final_answer", {
            "sources_used": sources_used,
            "tools_used": tools_used
        })

        # 6. Emit Final Event
        yield sse("final", {
            "type": "final",
            "content": final_content,
            "sources_used": sources_used,
            "tools_used": tools_used,
            "conversation_id": conv_id,
            "message_id": assistant_msg_id,
            "needs_clarification": needs_clarification
        })

    except Exception as e:
        logger.error(f"Error in chat stream: {e}", exc_info=True)
        yield sse("error", {"type": "error", "detail": str(e)})

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    POST /chat endpoint supporting real-time SSE streaming of agent step events
    and final answer.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Field 'message' cannot be empty.")

    conv_id = ensure_conversation(req.conversation_id)
    return StreamingResponse(
        chat_event_stream(conv_id, req.message.strip()),
        media_type="text/event-stream"
    )
