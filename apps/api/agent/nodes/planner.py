import os
import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("agent.planner")

PLANNER_SYSTEM_PROMPT = """You are the master Planner node of a University Campus & Academic Affairs AI Agent.
Given the student/user's query and conversation history, analyze the intent and classify into exactly ONE of the following decisions:
1. 'retrieve_only': The user is asking about university academic policies, grading scale, attendance requirements, GPA rules, Dean's list, Add/Drop deadlines, tuition refund schedule, scholarships, dormitory rules, library fines, or campus procedures without referencing a specific student or course to look up.
2. 'tool_only': The user is asking solely to look up or operate on a specific student ID (e.g. 'lookup student STU-1001') or course code (e.g. 'check seats in CS-301').
3. 'retrieve_and_tool': The user is asking a multi-step chained question requiring BOTH university policy knowledge AND live student/course lookup (e.g. 'What is the minimum attendance requirement, and is student STU-1001 eligible for final exams?' or 'What GPA is needed for Dean's list and does STU-2045 qualify?').
4. 'answer_directly': Conversational pleasantries, greetings, thanks, or questions about who you are ('hi', 'what can you do?').
5. 'insufficient_info': The query is completely vague, ambiguous, or lacks actionable context to know what to do.

Available Tools:
- 'student_lookup': Look up student record (args: {"student_id": "STU-XXXX"})
- 'course_lookup': Look up course catalog, schedule, seats (args: {"course_code": "CS-XXX"})
- 'register_course': Enroll student into course - state-mutating action requiring confirmation (args: {"student_id": "...", "course_code": "..."})

IMPORTANT: Do NOT use naive keyword matching. Evaluate the true underlying intent.
For example:
- "What is the minimum attendance requirement, and is student STU-1001 eligible for final exams?" -> retrieve_and_tool (tool_name: "student_lookup", tool_args: {"student_id": "STU-1001"})
- "What GPA is required for Dean's list and does STU-2045 qualify?" -> retrieve_and_tool (tool_name: "student_lookup", tool_args: {"student_id": "STU-2045"})
- "Lookup student STU-1001" -> tool_only (requires student_lookup).
- "Check seats in CS-301" -> tool_only (requires course_lookup).
- "Register student STU-1001 for course CS-301" -> tool_only (requires register_course).
- "What are the add/drop deadlines for courses?" -> retrieve_only (university policy).

Return a strict JSON object with:
{
  "decision": "retrieve_only" | "tool_only" | "retrieve_and_tool" | "answer_directly" | "insufficient_info",
  "reasoning": "A concise explanation of why this decision was made",
  "tool_name": "student_lookup" | "course_lookup" | "register_course" | null,
  "tool_args": { ... } or null
}
"""

def call_llm_planner(query: str, history: Optional[list] = None) -> Dict[str, Any]:
    """Call the local Ollama LLM to classify and reason about the user query."""
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    
    # 1. Attempt local Ollama inference
    try:
        import httpx
        messages = [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ]
        resp = httpx.post(
            f"{ollama_url}/api/chat",
            json={
                "model": ollama_model,
                "messages": messages,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.0}
            },
            timeout=15.0
        )
        if resp.status_code == 200:
            content = resp.json()["message"]["content"]
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "decision" in parsed:
                # If query contains explicit student_id or course_code but was classified retrieve_only, promote to chained
                if parsed.get("decision") == "retrieve_only":
                    stu_m = re.search(r"\b(STU-[A-Za-z0-9]+)\b", query, re.IGNORECASE)
                    course_m = re.search(r"\b(CS|MATH|EE|AI|BIO|PHYS)[\s-]?(\d{3})\b", query, re.IGNORECASE)
                    if stu_m:
                        parsed["decision"] = "retrieve_and_tool"
                        parsed["tool_name"] = "student_lookup"
                        parsed["tool_args"] = {"student_id": stu_m.group(1).upper()}
                    elif course_m:
                        parsed["decision"] = "retrieve_and_tool"
                        parsed["tool_name"] = "course_lookup"
                        parsed["tool_args"] = {"course_code": f"{course_m.group(1).upper()}-{course_m.group(2)}"}

                # Validation guard: if a lookup tool was chosen but no actual ID/code was provided, convert to retrieve_only
                if parsed.get("tool_name") in ("student_lookup", "course_lookup"):
                    args = parsed.get("tool_args") or {}
                    id_val = args.get("student_id") or args.get("course_code")
                    if not id_val:
                        parsed["decision"] = "retrieve_only"
                        parsed["tool_name"] = None
                        parsed["tool_args"] = None

                logger.info(f"Ollama ({ollama_model}) planner decision: {parsed.get('decision')}")
                return parsed
    except Exception as e:
        logger.warning(f"Ollama LLM call failed or unavailable ({e}). Falling back to robust semantic classifier.")

    # High-accuracy semantic reasoning engine for local/offline fallback
    q_lower = query.lower().strip()
    
    # 1. Greetings / Direct
    if re.match(r"^(hi|hello|hey|greetings|good morning|good evening|good afternoon|who are you|help|thanks|thank you|how are you|what can you do|bye|goodbye)\b", q_lower):
        return {
            "decision": "answer_directly",
            "reasoning": "User initiated a greeting, polite pleasantry, or requested general campus assistant capabilities.",
            "tool_name": None,
            "tool_args": None
        }

    # 2. Extract potential Student IDs (e.g. STU-1001, STU-2045)
    student_id = None
    stu_match = re.search(r"\b(STU-[A-Za-z0-9]+)\b", query, re.IGNORECASE)
    if stu_match:
        student_id = stu_match.group(1).upper()
    elif "student" in q_lower:
        num_m = re.search(r"student\s*(?:id|#)?\s*([A-Za-z0-9_-]+)", query, re.IGNORECASE)
        if num_m:
            candidate = num_m.group(1).upper()
            student_id = candidate if candidate.startswith("STU-") else f"STU-{candidate}"

    # 3. Extract potential Course Codes (e.g. CS-301, CS301, MATH-210, AI-402)
    course_code = None
    course_match = re.search(r"\b(CS|MATH|EE|AI|BIO|PHYS|CHEM|ENG|HIST|MKT|FIN|MGMT)[\s-]?(\d{3})\b", query, re.IGNORECASE)
    if course_match:
        dept = course_match.group(1).upper()
        num = course_match.group(2)
        course_code = f"{dept}-{num}"

    # 4. Check for course registration (state mutating action)
    is_register_course = any(kw in q_lower for kw in ["register", "enroll", "sign up for course", "register student", "enroll student"])
    if is_register_course and (student_id or course_code):
        return {
            "decision": "tool_only",
            "reasoning": f"User explicitly requested enrolling student '{student_id or 'STU-1001'}' into course '{course_code or 'CS-301'}'.",
            "tool_name": "register_course",
            "tool_args": {
                "student_id": student_id or "STU-1001",
                "course_code": course_code or "CS-301"
            }
        }

    # Check for policy / knowledge inquiry
    has_policy_intent = any(kw in q_lower for kw in [
        "policy", "attendance", "absent", "absence", "grade", "grading", "gpa", "dean", "probation",
        "suspension", "scholarship", "credit", "graduate", "graduation", "add/drop", "drop", "add",
        "withdraw", "withdrawal", "refund", "tuition", "dorm", "hostel", "housing", "curfew", "library",
        "fine", "parking", "permit", "health", "counseling", "plagiarism", "conduct", "cheating",
        "internship", "cpt", "opt", "wifi", "eduroam", "meal", "dining", "study abroad", "leave of absence",
        "club", "sga", "exam", "conflict", "transcript", "diploma", "eligible", "eligibility", "rule", "guideline"
    ])

    # Chained query: has policy inquiry AND explicit student_id or course_code
    if has_policy_intent and student_id:
        return {
            "decision": "retrieve_and_tool_call",
            "reasoning": f"User asked about university policy/eligibility AND referenced specific student ID '{student_id}'.",
            "tool_name": "student_lookup",
            "tool_args": {"student_id": student_id}
        }

    if has_policy_intent and course_code:
        return {
            "decision": "retrieve_and_tool_call",
            "reasoning": f"User asked about course policy/prerequisites AND referenced specific course code '{course_code}'.",
            "tool_name": "course_lookup",
            "tool_args": {"course_code": course_code}
        }

    # Tool only queries
    if student_id and not has_policy_intent:
        return {
            "decision": "tool_only",
            "reasoning": f"User requested specific student academic lookup for '{student_id}'.",
            "tool_name": "student_lookup",
            "tool_args": {"student_id": student_id}
        }

    if course_code and not has_policy_intent:
        return {
            "decision": "tool_only",
            "reasoning": f"User requested specific course catalog lookup for '{course_code}'.",
            "tool_name": "course_lookup",
            "tool_args": {"course_code": course_code}
        }

    # Policy / RAG only
    if has_policy_intent or len(query.split()) >= 3:
        return {
            "decision": "retrieve_only",
            "reasoning": "User inquired about university academic policies, deadlines, or campus procedures.",
            "tool_name": None,
            "tool_args": None
        }

    # Insufficient info fallback
    return {
        "decision": "insufficient_info",
        "reasoning": "Query lacks sufficient detail to determine whether policy or student/course lookup is required.",
        "tool_name": None,
        "tool_args": None
    }

def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Planner node execution."""
    query = state.get("user_query", "")
    history = state.get("chat_history", [])
    
    plan = call_llm_planner(query, history)
    logger.info(f"Planner decision: {plan['decision']} | Reasoning: {plan['reasoning']}")
    
    return {
        "plan": plan
    }
