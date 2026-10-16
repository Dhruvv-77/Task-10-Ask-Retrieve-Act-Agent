from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    conversation_id: str
    user_query: str
    chat_history: Optional[List[Dict[str, str]]]
    plan: Optional[Dict[str, Any]]                # {"decision": str, "reasoning": str, "tool_args": Optional[dict]}
    retrieved_chunks: Optional[List[Dict[str, Any]]] # [{"docId": str, "title": str, "text": str, "score": float}]
    tool_results: Optional[List[Dict[str, Any]]]     # [{"tool": str, "input": dict, "output": dict}]
    final_answer: Optional[str]
    needs_clarification: bool
    clarification_question: Optional[str]
    pending_confirmation: Optional[Dict[str, Any]] # For destructive/state-mutating actions (register_course)
    sources_used: Optional[List[str]]
    tools_used: Optional[List[str]]
