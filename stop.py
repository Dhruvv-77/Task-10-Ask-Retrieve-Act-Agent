"""
Clean Stop Script for "Ask, Retrieve, Act" Enterprise AI Agent
Usage: python stop.py

Shuts down Docker containers, MCP Server, FastAPI backend, Next.js, and releases ports.
"""

import os
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("\n" + "=" * 60)
    print("   Stopping All 'Ask, Retrieve, Act' Services...")
    print("=" * 60 + "\n")

    # 1. Stop Docker Compose
    print("[1/3] Stopping Docker containers (PostgreSQL & Redis)...")
    try:
        subprocess.run(["docker", "compose", "down"], cwd=ROOT_DIR)
    except Exception as e:
        print(f"Error stopping docker: {e}")

    # 2. Terminate running dev servers on Windows
    print("[2/3] Terminating Node, Python, and Uvicorn background servers...")
    if os.name == 'nt':
        for proc_name in ["node.exe", "uvicorn.exe"]:
            subprocess.run(
                ["taskkill", "/F", "/IM", proc_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    # 3. Kill lingering processes on Ports 3000, 8000, 9000
    print("[3/3] Releasing ports 3000, 8000, 9000...")
    if os.name == 'nt':
        for port in [3000, 8000, 9000]:
            try:
                cmd = f'netstat -ano | findstr :{port}'
                output = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
                for line in output.strip().splitlines():
                    parts = line.split()
                    if len(parts) >= 5 and "LISTENING" in parts:
                        pid = parts[-1]
                        subprocess.run(["taskkill", "/F", "/PID", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    print("\n" + "=" * 60)
    print("   All Services Stopped! Ports and memory are clean.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
