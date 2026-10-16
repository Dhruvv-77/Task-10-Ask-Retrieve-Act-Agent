"""
Live Python Runner for "Ask, Retrieve, Act" Enterprise AI Agent
Usage: python run.py

Runs all services (Docker, Ollama, MCP Server, FastAPI, Next.js) with
live unified log streaming in real time. Press Ctrl+C to stop cleanly.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import urllib.request
import urllib.error
import webbrowser

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# ANSI Colors for terminal output
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
GRAY = "\033[90m"
RED = "\033[91m"

processes = []
running = True


def print_banner(text, color=CYAN):
    print(f"\n{color}{BOLD}{'=' * 68}{RESET}")
    print(f"{color}{BOLD}   {text}{RESET}")
    print(f"{color}{BOLD}{'=' * 68}{RESET}\n")


def stream_logs(proc, prefix, color):
    """Stream stdout/stderr from a subprocess live with colored prefix."""
    try:
        for line in iter(proc.stdout.readline, ''):
            if not running and not line:
                break
            if line:
                print(f"{color}{prefix}{RESET} {line.rstrip()}", flush=True)
    except Exception:
        pass


def check_url(url, timeout=2):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def start_process(cmd, cwd, prefix, color, shell=False):
    """Start a background process and spawn a thread to stream logs live."""
    print(f"{GRAY}[STARTING]{RESET} {prefix} in {cwd} ...")
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=shell,
        encoding="utf-8",
        errors="replace"
    )
    processes.append((prefix, proc))
    t = threading.Thread(target=stream_logs, args=(proc, prefix, color), daemon=True)
    t.start()
    return proc


def cleanup(signum=None, frame=None):
    global running
    if not running:
        return
    running = False
    print_banner("Shutting down all services...", YELLOW)

    for prefix, proc in reversed(processes):
        print(f"{GRAY}[STOPPING]{RESET} {prefix} (PID {proc.pid})...")
        try:
            if os.name == 'nt':
                # Force kill entire process tree on Windows
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                proc.terminate()
        except Exception:
            pass

    print(f"{GRAY}[STOPPING]{RESET} Docker containers (Postgres & Redis)...")
    try:
        subprocess.run(["docker", "compose", "down"], cwd=ROOT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    print_banner("All services stopped cleanly. Ports released.", GREEN)
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print_banner("Ask, Retrieve, Act — Live Python Runner", CYAN)

    # 1. Start Docker containers (PostgreSQL & Redis)
    print(f"{YELLOW}[1/5] Starting Docker infrastructure (PostgreSQL & Redis)...{RESET}")
    res = subprocess.run(["docker", "compose", "up", "-d"], cwd=ROOT_DIR)
    if res.returncode != 0:
        print(f"{RED}Warning: docker compose failed. Please ensure Docker Desktop is running.{RESET}")

    # 2. Check / Start Ollama
    print(f"{YELLOW}[2/5] Checking Ollama daemon (http://localhost:11434)...{RESET}")
    if check_url("http://localhost:11434/api/version"):
        print(f"{GREEN}✓ Ollama is already running with local models.{RESET}")
    else:
        print(f"{GRAY}Starting Ollama in background...{RESET}")
        try:
            if os.name == 'nt':
                subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
        except Exception as e:
            print(f"{RED}Could not start ollama automatically: {e}. Please run 'ollama serve'.{RESET}")

    # 3. Start MCP Tool Server (Port 9000)
    print(f"{YELLOW}[3/5] Starting MCP Tool Server on :9000...{RESET}")
    start_process(
        [sys.executable, "mcp-server/server.py"],
        cwd=ROOT_DIR,
        prefix="[MCP:9000]",
        color=MAGENTA
    )

    # 4. Start FastAPI Agent Backend (Port 8000)
    print(f"{YELLOW}[4/5] Starting FastAPI Agent Backend on :8000...{RESET}")
    api_dir = os.path.join(ROOT_DIR, "apps", "api")
    start_process(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=api_dir,
        prefix="[API:8000]",
        color=CYAN
    )

    # 5. Start Next.js Web UI (Port 3000)
    print(f"{YELLOW}[5/5] Starting Next.js Web UI on :3000...{RESET}")
    web_dir = os.path.join(ROOT_DIR, "apps", "web")
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    start_process(
        [npm_cmd, "run", "dev"],
        cwd=web_dir,
        prefix="[WEB:3000]",
        color=GREEN,
        shell=(os.name == 'nt')
    )

    # Wait for services to become responsive
    print(f"\n{GRAY}Waiting for services to become healthy...{RESET}")
    for _ in range(15):
        mcp_ok = check_url("http://localhost:9000/health")
        api_ok = check_url("http://localhost:8000/health")
        if mcp_ok and api_ok:
            break
        time.sleep(1)

    print_banner("All Services Live & Streaming!", GREEN)
    print(f"  {BOLD}• Web UI:{RESET}     http://localhost:3000")
    print(f"  {BOLD}• API Docs:{RESET}   http://localhost:8000/docs")
    print(f"  {BOLD}• MCP Server:{RESET} http://localhost:9000/health")
    print(f"\n  {YELLOW}Press Ctrl+C at any time to gracefully stop all services.{RESET}\n")

    # Automatically open browser
    try:
        webbrowser.open("http://localhost:3000")
    except Exception:
        pass

    # Keep alive and stream logs
    try:
        while running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
