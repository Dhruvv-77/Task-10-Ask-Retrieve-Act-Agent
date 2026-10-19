# 🎓 CampusAgent: Autonomous University AI Assistant

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org/)
[![Local LLM](https://img.shields.io/badge/LLM-Local%20Ollama%20(qwen2.5%3A7b)-8A2BE2.svg)](https://ollama.ai/)
[![Database](https://img.shields.io/badge/Storage-PostgreSQL%20%7C%20Redis%20%7C%20ChromaDB-blueviolet.svg)](https://www.postgresql.org/)
[![Protocol](https://img.shields.io/badge/Tools-Model%20Context%20Protocol%20(MCP)-success.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

An intelligent, local-first autonomous AI agent built for university campus and academic affairs administration. Built with **LangGraph**, **Ollama (`qwen2.5:7b-instruct`)**, **FastAPI**, **Next.js 14**, and the **Model Context Protocol (MCP)**, **CampusAgent** autonomously decides at runtime whether a student query demands institutional knowledge retrieval, live registrar tool execution, chained multi-step reasoning, or human-in-the-loop confirmation.

---

## 🌟 Key Highlights

- **🔒 100% Local-First & Confidential:** Powered entirely by local Ollama (`qwen2.5:7b-instruct`). Zero external cloud LLM API dependencies, zero API costs, and complete student record confidentiality (FERPA-compliant).
- **🧠 Semantic Runtime Planning:** A dedicated LangGraph Planner node dynamically classifies intents (`retrieve_only`, `tool_only`, `retrieve_and_tool`, `clarify`, `greeting`) using semantic reasoning rather than brittle keyword matching.
- **🔗 Chained Multi-Step Execution:** Seamlessly resolves complex multi-hop queries requiring both institutional policy grounding and live student database lookups in a single fluid conversational turn.
- **🛡️ State-Mutating Safety Guardrails:** Critical operations like course enrollments (`register_course`) are intercepted with a two-turn confirmation checkpoint before any database records are modified.
- **📊 Comprehensive PostgreSQL Audit Trail:** Every intermediate reasoning step (`plan`, `retrieval`, `tool_call`, `clarify`, `final_answer`) is permanently stored with structured JSON metadata for compliance and auditability.
- **⚡ Real-Time Streaming & Visual Trace:** Server-Sent Events (SSE) stream the response token-by-token alongside an interactive visual trace of each agent node's internal reasoning.

---

## 🏗️ System Architecture

```
Student / Faculty (Next.js 14 Web UI :3000)
         │
         ▼  Server-Sent Events (SSE: 'step' and 'final' events)
FastAPI Backend (:8000)
   ├── Local Ollama (:11434)     ──▶  qwen2.5:7b-instruct (Planning & Answer Synthesis)
   ├── PostgreSQL 16 (:5432)     ──▶  Conversations, Messages & AuditLog Persistence
   ├── Redis 7 (:6379)           ──▶  RAG Retrieval Cache (TTL: 10 mins)
   ├── ChromaDB (local)          ──▶  20 Institutional Policy Documents (Threshold ≥ 0.65)
   └── LangGraph State Machine
            │
            ├── Planner Node     ──▶  Intent Classification & Semantic Reasoning
            ├── Retriever Node   ──▶  Vector Top-K Search + Redis Cache Check
            ├── Tool Executor    ──▶  Safety Guardrail Check + MCP Client Dispatch
            ├── Responder Node   ──▶  Multi-Context Evidence Synthesis & Citation
            └── Clarify Node     ──▶  Disambiguation & Anti-Hallucination Fallback
                    │
                    ▼
          MCP Tool Server (:9000)
            ├── student_lookup(student_id)
            ├── course_lookup(course_code)
            └── register_course(student_id, course_code) [State-Mutating Guardrail]
```

---

## 🏛️ Engineering Decisions & Design Rationale

### 1. Chunking Strategy & Boundary Preservation
- **Chunk Size:** 350–450 tokens (~1,400–1,800 characters)
- **Overlap:** 15% sliding window (~50–70 tokens / 240 characters)
- **Design Rationale:** Institutional bylaws, academic regulations, and grading rubrics form coherent semantic blocks across 2–3 paragraphs. Chunks smaller than 250 tokens fragment conditional clauses (e.g., separating *"Attendance minimum is 75%"* from *"failing which a student is debarred from final examinations"*). The 15% overlap prevents sentence truncation across chunk boundaries.

### 2. Anti-Hallucination Similarity Threshold
- **Threshold Value:** `0.65` (Cosine similarity)
- **Design Rationale:** Vector metrics often yield low non-zero scores (0.30–0.50) for irrelevant queries due to shared syntactic patterns. Setting a hard threshold of `0.65` ensures only high-confidence policy chunks reach the LLM context. When no chunks meet the threshold, the agent transitions to the `Clarify` node rather than inventing facts.

### 3. Human-in-the-Loop Confirmation Guardrail
- **Protected Action:** `register_course`
- **Design Rationale:** State-mutating actions (official class registrations, course drops, or financial transactions) should never occur on a single unverified model inference. When course registration is detected, `tool_executor` pauses execution, flags `pending_confirmation: true`, and prompts the student:
  > *"I am prepared to register student '{student_id}' into course '{course_code}'. This action permanently updates official university enrollment records — do you confirm?"*
  Execution proceeds only after explicit user affirmation in the subsequent conversational turn.

### 4. Cache Separation Strategy
- **Key Schema:** `rag:cache:<SHA256(normalized_query)>` (TTL: 10 minutes)
- **Design Rationale:** Policy documents are relatively static and benefit from caching during active user sessions. Conversely, operational data (`student_lookup`, `course_lookup`) is strictly **never cached**, ensuring real-time seat counts and academic statuses are always live.

---

## 📁 Repository Structure

```
campus-agent/
├── apps/
│   ├── web/                         # Next.js 14 Frontend Application
│   │   ├── app/
│   │   │   ├── chat/page.tsx        # Interactive Chat Route
│   │   │   ├── layout.tsx           # Global Styling & Fonts
│   │   │   └── page.tsx             # Landing / Redirection
│   │   ├── components/
│   │   │   ├── AgentStepTrace.tsx   # Real-Time Node Execution Timeline
│   │   │   ├── ChatWindow.tsx       # Streaming Chat Interface & Prompt Suggestions
│   │   │   └── MessageBubble.tsx    # Source Badges & Markdown Rendering
│   │   └── lib/api.ts               # SSE Stream Parser & API Client
│   └── api/                         # FastAPI Backend Application
│       ├── main.py                  # Server Lifespan & CORS Configuration
│       ├── routes/
│       │   ├── chat.py              # POST /chat (SSE Streaming Endpoint)
│       │   ├── health.py            # GET /health (Active Dependency Health Checks)
│       │   └── admin.py             # POST /admin/reindex (ChromaDB Re-indexing)
│       ├── agent/
│       │   ├── graph.py             # LangGraph State Machine Definition
│       │   ├── state.py             # AgentState TypedDict Schema
│       │   └── nodes/               # Planner, Retriever, Tool Executor, Responder, Clarify
│       ├── rag/
│       │   ├── ingest.py            # Document Chunking & ChromaDB Ingestion
│       │   ├── embed.py             # Local SentenceTransformer Embedding Abstraction
│       │   └── retrieve.py          # Vector Similarity Search + Redis Caching
│       ├── mcp_client/
│       │   └── client.py            # Model Context Protocol (MCP) JSON-RPC Client
│       ├── db/                      # PostgreSQL Session & Prisma Schema
│       └── tests/                   # Pytest Automated Test Suite (20 Tests)
├── mcp-server/                      # Standalone Model Context Protocol Server (:9000)
│   ├── server.py                    # JSON-RPC & HTTP Tool Server
│   ├── mock_data/                   # students.json, courses.json, registrations.json
│   └── tools/                       # student_lookup, course_lookup, register_course
├── data/
│   └── documents/                   # 20 Official University Policy Documents (Markdown)
├── docs/
│   ├── architecture.md              # Detailed Architectural Specifications
│   └── eval-set.json                # Test Evaluation Suite
├── docker-compose.yml               # PostgreSQL 16 & Redis 7 Infrastructure
├── run.py                           # Unified Live Launcher with Real-Time Log Streaming
├── stop.py                          # Graceful Resource Shutdown Script
└── README.md
```

---

## 🚀 Quickstart Guide

### Prerequisites

Ensure you have the following installed on your machine before running:

| Requirement | Minimum Version | Installation & Download Link |
| :--- | :--- | :--- |
| **Python** | `3.11+` | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js** | `v18+` (npm v9+) | [nodejs.org](https://nodejs.org/) |
| **Docker & Docker Compose** | Docker Desktop 4.x+ | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) *(Ensure Docker Desktop is running)* |
| **Ollama** | Latest | [ollama.com/download](https://ollama.com/download) |

---

### 🧠 Required Local LLM Model

CampusAgent is powered by local **Ollama** so that no external cloud APIs or paid tokens are required.

After installing Ollama, pull the recommended reasoning model:

```bash
# Pull the official high-accuracy reasoning model (~4.7 GB)
ollama pull qwen2.5:7b-instruct
```

> **Model Specifications:**
> - **Model:** `qwen2.5:7b-instruct`
> - **Parameters:** 7.6 Billion (4-bit quantized `Q4_K_M`)
> - **Recommended Hardware:** 8 GB+ RAM or 6 GB+ VRAM GPU
> - **Low-spec Alternative:** If you have limited RAM (under 8 GB), you can pull `ollama pull qwen2.5:3b-instruct` and update `OLLAMA_MODEL=qwen2.5:3b-instruct` in `apps/api/.env`.

---

### 1. Clone the Repository
```bash
git clone https://github.com/Dhruvv-77/Task-10-Ask-Retrieve-Act-Agent.git
cd Task-10-Ask-Retrieve-Act-Agent
```

### 2. Environment Setup
Install Python backend and tool dependencies:
```bash
pip install -r apps/api/requirements.txt
pip install -r mcp-server/requirements.txt
```

Install frontend dependencies:
```bash
cd apps/web
npm install
cd ../..
```

### 3. One-Command Live Python Launch
Launch all services concurrently with live streaming output:
```bash
python run.py
```
This automatically:
- Starts PostgreSQL & Redis containers via Docker (with auto-recovery from stale containers)
- Verifies local Ollama service availability
- Automatically initializes & indexes the 20 university policy documents into ChromaDB (if not already indexed)
- Starts the MCP Tool Server on port `9000`
- Starts the FastAPI Agent Backend on port `8000`
- Starts the Next.js Web UI on port `3000`
- Opens `http://localhost:3000` in your default browser

*(Optional: You can also manually re-index the vector database anytime by running `python apps/api/rag/ingest.py`)*

> **To stop all services and release all ports at any time:**
> ```bash
> python stop.py
> ```

---

## 🧪 Interactive Demo Scenarios

Once the system is running at `http://localhost:3000`, try these test queries:

### 1. Chained Multi-Step Reasoning (Policy + Live Student Lookup)
> **Query:** `What is the minimum attendance requirement, and is student STU-1001 eligible for final exams?`
- **Execution Path:** `Planner` ➔ `Retriever` (fetches `policy-002`, 75% attendance rule) ➔ `Tool Executor` (`student_lookup("STU-1001")`, Aarav Patel, 88% attendance) ➔ `Responder`.
- **Outcome:** The agent synthesizes both sources, citing `policy-002` and confirming Aarav Patel is eligible to sit for final semester examinations.

### 2. Academic Standing & Honors Qualification
> **Query:** `What GPA is required for the Dean's Honor List, and does student STU-1001 make the list?`
- **Execution Path:** `Planner` ➔ `Retriever` (`policy-001`, GPA $\ge 3.75$) ➔ `Tool Executor` (Aarav Patel, GPA 3.85) ➔ `Responder`.
- **Outcome:** Validates that Aarav Patel exceeds the 3.75 GPA requirement and is on the Dean's Honor List.

### 3. Course Catalog Seat Availability
> **Query:** `Check course details and available seats for CS-301`
- **Execution Path:** `Planner` ➔ `Tool Executor` (`course_lookup("CS-301")`) ➔ `Responder`.
- **Outcome:** Displays Database Management Systems taught by Dr. Alan Turing, 4 credits, Mon/Wed schedule, and 7 remaining open seats.

### 4. Human-in-the-Loop Confirmation Guardrail
> **Turn 1 Query:** `Register student STU-1001 for course AI-402`
- **Execution Path:** `Planner` ➔ `Tool Executor` (detects `register_course` ➔ intercepts execution).
- **Agent Interception:** *"I am prepared to register student 'STU-1001' into course 'AI-402'. This action permanently updates official university enrollment records — do you confirm?"*
> **Turn 2 Confirmation:** `Yes, I confirm`
- **Outcome:** Dispatches `register_course` via MCP, generates an official registration ID (`REG-STU-1001-AI-402`), and commits the enrollment.

---

## 🔬 Automated Testing & Verification

The project includes an end-to-end automated test suite covering unit logic, failure modes, adversarial intents, guardrails, and full database audit logging:

```bash
# Ensure Docker services are running:
docker compose up -d

# Run pytest across the entire test suite:
pytest apps/api/tests/ -v
```

### Test Suite Summary (`20 passed in ~55s`):

| Test Module | Coverage Scope | Status |
| :--- | :--- | :---: |
| `test_mcp_tools.py` | Schema validation, invalid arguments, not-found handling for all MCP tools | **Passed** ✅ |
| `test_nodes.py` | Isolated node testing for Planner, Retriever, Tool Executor, and Responder | **Passed** ✅ |
| `test_failure_paths.py` | Anti-hallucination (<0.65 similarity), tool failures, 2-turn confirmation cycles | **Passed** ✅ |
| `test_e2e_chained.py` | End-to-end chained query validation with verified PostgreSQL `AuditLog` records | **Passed** ✅ |

---

## 📊 PostgreSQL AuditLog Schema

Every intermediate step is persisted in the PostgreSQL database for transparency and audit compliance:

```json
{
  "plan": {
    "decision": "retrieve_and_tool",
    "reasoning": "User inquired about attendance policy requirements and exam eligibility for student STU-1001."
  },
  "retrieval": {
    "query": "minimum attendance policy final exams",
    "chunks": [
      {
        "docId": "policy-002",
        "text": "Under University Policy policy-002, students must maintain at least 75% attendance...",
        "score": 0.84
      }
    ]
  },
  "tool_call": {
    "tool": "student_lookup",
    "input": { "student_id": "STU-1001" },
    "output": {
      "student_id": "STU-1001",
      "name": "Aarav Patel",
      "attendance_pct": 88,
      "academic_standing": "Dean's Honor List",
      "eligible_for_exams": true
    }
  },
  "final_answer": {
    "sources_used": ["policy-002"],
    "tools_used": ["student_lookup"]
  }
}
```

---

## 🤝 Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE) — see the LICENSE file for details.
