import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("agent.responder")

def responder_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Responder node synthesizing retrieved chunks and tool results."""
    # If final answer was already set (e.g. by guardrail confirmation prompt)
    if state.get("final_answer"):
        return {}

    user_query = state.get("user_query", "")
    plan = state.get("plan", {})
    retrieved_chunks = state.get("retrieved_chunks") or []
    tool_results = state.get("tool_results") or []
    needs_clarification = state.get("needs_clarification", False)

    sources_used = list(dict.fromkeys([c.get("docId") for c in retrieved_chunks if c.get("docId")]))
    tools_used = list(dict.fromkeys([t.get("tool") for t in tool_results if t.get("tool")]))

    # If already flagged for clarification
    if needs_clarification and not tool_results:
        return {
            "sources_used": sources_used,
            "tools_used": tools_used
        }

    # Answer directly case (pleasantries, greetings, capabilities)
    if plan.get("decision") == "answer_directly":
        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
        try:
            import httpx
            resp = httpx.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": ollama_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a friendly, knowledgeable University Campus & Academic Affairs AI Assistant. "
                                "Respond warmly and concisely to greetings or questions about your capabilities. "
                                "Explain that you assist students and staff with university academic policies, grading scales, "
                                "exam eligibility, attendance rules, course catalog lookup, and student records."
                            )
                        },
                        {"role": "user", "content": user_query}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.4}
                },
                timeout=12.0
            )
            if resp.status_code == 200:
                answer = resp.json().get("message", {}).get("content", "").strip()
                if answer:
                    return {
                        "final_answer": answer,
                        "sources_used": [],
                        "tools_used": []
                    }
        except Exception as e:
            logger.info(f"Ollama direct answer fallback: {e}")

        return {
            "final_answer": "Hello! I am your University Campus AI Assistant. I can help you with university policies, attendance rules, grading and GPA questions, course catalog information, and student record lookups. How can I assist you today?",
            "sources_used": [],
            "tools_used": []
        }

    # Synthesize answer using Ollama if available
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    
    context_text = ""
    if tool_results:
        context_text += f"\nOperational University Tool Results:\n{json.dumps(tool_results, indent=2)}\n"
    if retrieved_chunks:
        context_text += f"\nRetrieved University Policy Chunks:\n" + "\n---\n".join([f"[{c.get('docId', 'policy')}] {c.get('text', '')}" for c in retrieved_chunks[:3]])

    if context_text:
        try:
            import httpx
            prompt = (
                f"User Query: {user_query}\n\n"
                f"Context Information:\n{context_text}\n\n"
                f"Task: Synthesize a professional, direct, and helpful answer for the university student/faculty based strictly on the provided context. "
                f"If citing university policies, cite the exact policy document ID (e.g. policy-001, policy-002)."
            )
            resp = httpx.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": ollama_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful and accurate University Campus & Academic Affairs AI Assistant. Answer concisely and factually based strictly on the provided context."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2}
                },
                timeout=20.0
            )
            if resp.status_code == 200:
                answer = resp.json().get("message", {}).get("content", "").strip()
                if answer:
                    return {
                        "final_answer": answer,
                        "sources_used": sources_used,
                        "tools_used": tools_used
                    }
        except Exception as e:
            logger.warning(f"Ollama responder synthesis failed ({e}). Falling back to template synthesis.")

    # Fallback Template Synthesis
    paragraphs = []

    # Handle Tool Results
    for res in tool_results:
        tool_name = res.get("tool")
        tool_out = res.get("output", {})
        
        if "error" in tool_out:
            paragraphs.append(f"Regarding your inquiry: {tool_out['error']}")
        elif tool_name == "student_lookup":
            s_id = tool_out.get("student_id", "N/A")
            name = tool_out.get("name", "Student")
            major = tool_out.get("major", "Undeclared")
            year = tool_out.get("year", "")
            gpa = tool_out.get("cumulative_gpa", 0.0)
            att = tool_out.get("attendance_pct", 0)
            standing = tool_out.get("academic_standing", "Good")
            exam_elig = "Eligible" if tool_out.get("eligible_for_exams", True) else "Debarred (Attendance < 75%)"
            holds = tool_out.get("holds", [])
            holds_str = ", ".join(holds) if holds else "None"
            paragraphs.append(
                f"Academic Record for {name} ({s_id}):\n"
                f"• Major: {major} ({year})\n"
                f"• Cumulative GPA: {gpa}\n"
                f"• Documented Attendance: {att}% ({exam_elig})\n"
                f"• Academic Standing: {standing}\n"
                f"• Active Account Holds: {holds_str}"
            )
        elif tool_name == "course_lookup":
            code = tool_out.get("course_code", "N/A")
            title = tool_out.get("title", "Course")
            instructor = tool_out.get("instructor", "Faculty")
            credits = tool_out.get("credits", 3)
            seats = tool_out.get("seats_available", 0)
            sched = tool_out.get("schedule", "TBA")
            loc = tool_out.get("location", "Campus")
            status = tool_out.get("status", "Open")
            paragraphs.append(
                f"Course Details for {code} — {title}:\n"
                f"• Instructor: {instructor} ({credits} credits)\n"
                f"• Schedule: {sched} ({loc})\n"
                f"• Enrollment Status: {status} ({seats} seats available)"
            )
        elif tool_name == "register_course":
            reg_id = tool_out.get("registration_id", "REG-SUCCESS")
            s_id = tool_out.get("student_id", "")
            c_code = tool_out.get("course_code", "")
            paragraphs.append(
                f"Course Registration Successful! Student {s_id} is officially enrolled in {c_code} (Registration Reference: {reg_id})."
            )

    # Handle Retrieved Chunks
    if retrieved_chunks:
        top_chunk = retrieved_chunks[0]
        paragraphs.append(
            f"According to University Policy {top_chunk.get('docId', 'policy')} ({top_chunk.get('title', 'Academic Regulations')}):\n"
            f"{top_chunk.get('text', '')[:350]}..."
        )

    final_content = "\n\n".join(paragraphs) if paragraphs else "I processed your inquiry, but found no matching university records or policy documents."

    logger.info(f"Responder synthesized answer. Sources: {sources_used}, Tools: {tools_used}")
    return {
        "final_answer": final_content,
        "sources_used": sources_used,
        "tools_used": tools_used
    }
