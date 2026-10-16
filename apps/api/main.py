import sys
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Ensure apps/api directory is in sys.path for direct or module execution
API_DIR = str(Path(__file__).resolve().parent)
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

from db.session import init_db
from routes.health import router as health_router
from routes.admin import router as admin_router
from routes.chat import router as chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure PostgreSQL tables are initialized
    logger.info("Starting up FastAPI Capstone Backend...")
    try:
        init_db()
        logger.info("PostgreSQL database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database init warning (will retry on demand): {e}")
    yield
    logger.info("Shutting down FastAPI Capstone Backend...")

app = FastAPI(
    title="Ask, Retrieve, Act — Capstone Backend API",
    version="1.0.0",
    description="FastAPI orchestration service for LangGraph agent, MCP server, and RAG knowledge base.",
    lifespan=lifespan
)

# CORS Configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health_router, tags=["Health"])
app.include_router(admin_router, tags=["Admin"])
app.include_router(chat_router, tags=["Chat"])

@app.get("/")
def root():
    return {
        "project": "Ask, Retrieve, Act — Capstone Agent",
        "docs_url": "/docs",
        "health_url": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
