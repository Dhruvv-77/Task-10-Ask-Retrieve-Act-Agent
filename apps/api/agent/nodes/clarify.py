import logging
from typing import Dict, Any

logger = logging.getLogger("agent.clarify")

def clarify_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Clarify node."""
    user_query = state.get("user_query", "")
    existing_question = state.get("clarification_question")

    if not existing_question:
        existing_question = f"Your query '{user_query}' requires additional details. Could you please specify either the order number (e.g. 4521) or the specific company policy document you want to review?"

    logger.info(f"Clarify node triggered: {existing_question}")
    return {
        "needs_clarification": True,
        "clarification_question": existing_question,
        "final_answer": existing_question
    }
