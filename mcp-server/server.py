import http.server
import json
import logging
import os
import sys
from typing import Dict, Any

from tools.student_lookup import student_lookup
from tools.course_lookup import course_lookup
from tools.register_course import register_course

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp-server")

TOOLS: Dict[str, Any] = {
    "student_lookup": {
        "function": student_lookup,
        "description": "Lookup student academic standing, cumulative GPA, attendance percentage, holds, and enrolled courses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "The unique student ID (e.g. STU-1001)"}
            },
            "required": ["student_id"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string"},
                "name": {"type": "string"},
                "cumulative_gpa": {"type": "number"},
                "attendance_pct": {"type": "number"},
                "academic_standing": {"type": "string"},
                "eligible_for_exams": {"type": "boolean"}
            }
        }
    },
    "course_lookup": {
        "function": course_lookup,
        "description": "Lookup course catalog information, seats available, schedules, prerequisites, and instructors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "course_code": {"type": "string", "description": "The course code (e.g. CS-301)"}
            },
            "required": ["course_code"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "course_code": {"type": "string"},
                "title": {"type": "string"},
                "seats_available": {"type": "integer"},
                "schedule": {"type": "string"}
            }
        }
    },
    "register_course": {
        "function": register_course,
        "description": "Enroll a student into a university course. Note: Destructive/state-mutating action requiring confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "The student ID"},
                "course_code": {"type": "string", "description": "The course code to enroll in"}
            },
            "required": ["student_id", "course_code"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "registration_id": {"type": "string"},
                "enrolled": {"type": "boolean"}
            }
        }
    }
}

class MCPRequestHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: Any):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "mcp-server"})
        elif self.path in ("/tools", "/v1/tools"):
            tool_list = [
                {
                    "name": name,
                    "description": meta["description"],
                    "inputSchema": meta["input_schema"],
                    "outputSchema": meta["output_schema"]
                }
                for name, meta in TOOLS.items()
            ]
            self._send_json(200, {"tools": tool_list})
        else:
            self._send_json(404, {"error": "Not Found", "path": self.path})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON payload: {str(e)}"})
            return

        # Direct endpoint: /call/<tool_name>
        if self.path.startswith("/call/"):
            tool_name = self.path[len("/call/"):]
            self._execute_tool(tool_name, payload)
            return

        # Generic /call endpoint
        if self.path == "/call":
            tool_name = payload.get("tool") or payload.get("name")
            arguments = payload.get("arguments", payload.get("input", {}))
            self._execute_tool(tool_name, arguments)
            return

        # JSON-RPC 2.0 endpoint (e.g. "/" or "/jsonrpc")
        if "method" in payload:
            method = payload.get("method")
            rpc_id = payload.get("id")
            if method == "tools/list":
                tool_list = [
                    {"name": name, "description": meta["description"], "inputSchema": meta["input_schema"]}
                    for name, meta in TOOLS.items()
                ]
                self._send_json(200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": tool_list}})
            elif method == "tools/call":
                params = payload.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})
                if name not in TOOLS:
                    self._send_json(200, {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {"code": -32601, "message": f"Tool '{name}' not found."}
                    })
                else:
                    result = TOOLS[name]["function"](args)
                    self._send_json(200, {"jsonrpc": "2.0", "id": rpc_id, "result": result})
            else:
                self._send_json(200, {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not recognized."}
                })
            return

        self._send_json(404, {"error": "Endpoint not recognized", "path": self.path})

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
        if tool_name not in TOOLS:
            self._send_json(404, {
                "error": f"Unknown tool '{tool_name}'. Available: {list(TOOLS.keys())}",
                "code": "TOOL_NOT_FOUND"
            })
            return

        tool_fn = TOOLS[tool_name]["function"]
        try:
            result = tool_fn(arguments)
            self._send_json(200, result)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            self._send_json(500, {
                "error": f"Internal execution error: {str(e)}",
                "code": "EXECUTION_ERROR"
            })

    def log_message(self, format, *args):
        logger.info("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))

def run_server(port: int = 9000):
    server_address = ("", port)
    httpd = http.server.ThreadingHTTPServer(server_address, MCPRequestHandler)
    logger.info(f"MCP Server listening on http://0.0.0.0:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping MCP server...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", 9000))
    run_server(port)
