"""
FastAPI Application Entry Point

Lifecycle:
  - On startup: initialises PostgreSQL tables + seeds ChromaDB
  - Registers all API routes
"""
import sys
import os

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import init_db
from backend.api.routes import router
from backend.api.auth_routes import router as auth_router
from backend.config import FASTAPI_HOST, FASTAPI_PORT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle manager."""
    print("[App] Starting Healthcare Planning Assistant Agent...")

    # 1. Initialise PostgreSQL tables (Required for Auth)
    try:
        await init_db()
        print("[App] PostgreSQL tables ready.")
    except Exception as e:
        print(f"[App] WARNING: PostgreSQL init failed: {e}")

    # 2. Seed ChromaDB (Background task - may take time to download model)
    def bg_init_chroma():
        try:
            print("[App] ChromaDB background initialization started...")
            from backend.chroma.chroma_setup import initialize_chroma
            initialize_chroma()
            print("[App] ChromaDB background initialization complete.")
        except Exception as e:
            print(f"[App] WARNING: ChromaDB background init failed: {e}")

    import threading
    threading.Thread(target=bg_init_chroma, daemon=True).start()

    yield  # Application starts listening HERE immediately

    print("[App] Shutting down Healthcare Planning Assistant Agent.")

    print("[App] Shutting down Healthcare Planning Assistant Agent.")


# ── FastAPI Application ───────────────────────────────────────────────────────
app = FastAPI(
    title="Healthcare Planning Assistant Agent",
    description=(
        "A multi-agent AI system for goal-driven healthcare treatment planning. "
        "Powered by Google Gemini, FastAPI, PostgreSQL, and ChromaDB."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routes ───────────────────────────────────────────────────────────
app.include_router(router)
app.include_router(auth_router)


# ── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=True)
