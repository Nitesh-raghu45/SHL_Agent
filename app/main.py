"""FastAPI application — SHL Assessment Recommendation Agent."""
from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables before anything else
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — preload models and index."""
    print("[STARTUP] Loading FAISS index and embedding model...")
    from app.rag.vector_store import load_index
    load_index()  # Preload and cache
    print("[STARTUP] Ready to serve requests!")
    yield
    print("[SHUTDOWN] Cleaning up...")


app = FastAPI(
    title="SHL Assessment Recommendation Agent",
    description=(
        "An AI-powered agent that recommends SHL assessments based on "
        "hiring requirements. Supports clarification, recommendation, "
        "comparison, and refinement workflows."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for the assignment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.health import router as health_router
from app.api.chat import router as chat_router

app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    """Root endpoint — service info."""
    return {
        "service": "SHL Assessment Recommendation Agent",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "chat": "POST /chat",
        },
    }
