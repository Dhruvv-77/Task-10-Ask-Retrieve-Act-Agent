import os
import sys
import pytest

# Ensure apps/api and mcp-server are on sys.path
api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
mcp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "mcp-server"))

if api_dir not in sys.path:
    sys.path.insert(0, api_dir)
if mcp_dir not in sys.path:
    sys.path.insert(0, mcp_dir)

# Set test environment flags
os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/capstone")
os.environ["REDIS_URL"] = os.environ.get("REDIS_URL", "redis://localhost:6379")
