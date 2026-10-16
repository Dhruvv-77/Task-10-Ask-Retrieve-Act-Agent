import os
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("mcp_client")

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:9000").rstrip("/")

def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call an MCP tool via the HTTP MCP server.
    Falls back to direct tool import if MCP server is temporarily unreachable.
    """
    url = f"{MCP_SERVER_URL}/call/{tool_name}"
    try:
        response = requests.post(url, json=arguments, timeout=5.0)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return response.json()
        else:
            return {
                "error": f"MCP server error: HTTP {response.status_code}",
                "detail": response.text,
                "code": "SERVER_ERROR"
            }
    except requests.exceptions.RequestException as e:
        logger.warning(f"MCP server connection failed at {url} ({e}). Attempting local tool fallback.")
        # Local direct invocation fallback for seamless standalone testing/runtime
        try:
            import sys
            mcp_server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "mcp-server"))
            if mcp_server_dir not in sys.path:
                sys.path.insert(0, mcp_server_dir)
            from tools.student_lookup import student_lookup
            from tools.course_lookup import course_lookup
            from tools.register_course import register_course

            tools_map = {
                "student_lookup": student_lookup,
                "course_lookup": course_lookup,
                "register_course": register_course
            }
            if tool_name in tools_map:
                return tools_map[tool_name](arguments)
            else:
                return {"error": f"Tool '{tool_name}' not found in local tools.", "code": "TOOL_NOT_FOUND"}
        except Exception as local_e:
            logger.error(f"Local fallback also failed: {local_e}")
            return {
                "error": f"Failed to invoke tool '{tool_name}': {str(e)}",
                "code": "CONNECTION_FAILED"
            }

def check_mcp_server_health() -> bool:
    """Check if the MCP server is alive."""
    try:
        r = requests.get(f"{MCP_SERVER_URL}/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False
