"""
Central configuration loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/healthcare_agent"
)
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./backend/chroma/chroma_store")
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "127.0.0.1")
FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
