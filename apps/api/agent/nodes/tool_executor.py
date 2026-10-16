import logging
from typing import Dict, Any, List
from mcp_client.client import call_mcp_tool

logger = logging.getLogger("agent.tool_executor")

def tool_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Tool-Executor node."""
    plan = state.get("plan", {})
    tool_name = plan.get("tool_name")
    tool_args = plan.get("tool_args") or {}
    user_query = state.get("user_query", "").lower()
    pending = state.get("pending_confirmation")

    if not tool_name:
        return {"tool_results": []}

    logger.info(f"Tool-Executor evaluating tool: '{tool_name}' with args: {tool_args}")

    # Section 13 Deliberate Guardrail: Check for state-mutating course registration
    if tool_name == "register_course":
        # Check if this turn is an explicit confirmation of pending enrollment
        is_confirmed = False
        if pending and pending.get("action") == "register_course":
            if any(affirmative in user_query for affirmative in ["yes", "confirm", "proceed", "go ahead", "do it", "sure"]):
                is_confirmed = True
                tool_args = pending.get("payload", tool_args)

        if not is_confirmed:
            # Guardrail triggers: do NOT call register_course yet.
            logger.info("Guardrail intercepted register_course: requesting user confirmation first.")
            student_id = tool_args.get("student_id", "Student")
            course_code = tool_args.get("course_code", "Course")
            confirm_message = f"I am prepared to register student '{student_id}' into course '{course_code}'. This action permanently updates official university enrollment records — do you confirm?"

            return {
                "needs_clarification": False,
                "pending_confirmation": {
                    "action": "register_course",
                    "payload": tool_args
                },
                "final_answer": confirm_message,
                "tools_used": []
            }

    # Execute MCP tool
    output = call_mcp_tool(tool_name, tool_args)
    tool_result = {
        "tool": tool_name,
        "input": tool_args,
        "output": output
    }
    logger.info(f"Tool-Executor executed {tool_name}. Result: {output}")

    # Clear pending confirmation once executed
    return {
        "tool_results": [tool_result],
        "pending_confirmation": None,
        "tools_used": [tool_name]
    }
