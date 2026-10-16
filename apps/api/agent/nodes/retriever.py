import logging
from typing import Dict, Any
from rag.retrieve import retrieve_chunks

logger = logging.getLogger("agent.retriever")

def retriever_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Retriever node."""
    query = state.get("user_query", "")
    logger.info(f"Retriever node executing query: '{query}'")
    
    retrieval_result = retrieve_chunks(query)
    chunks = retrieval_result.get("chunks", [])
    is_relevant = retrieval_result.get("is_relevant", False)
    top_score = retrieval_result.get("top_score", 0.0)

    logger.info(f"Retrieved {len(chunks)} chunks. Top score: {top_score} (is_relevant={is_relevant})")

    # If no chunk cleared the relevance threshold (0.65), flag for Clarify
    if not is_relevant or not chunks:
        return {
            "retrieved_chunks": [],
            "needs_clarification": True,
            "clarification_question": f"I couldn't find any policy documentation meeting our confidence threshold for '{query}'. Could you specify which company policy or guideline you are referring to?"
        }

    return {
        "retrieved_chunks": chunks,
        "needs_clarification": False
    }
