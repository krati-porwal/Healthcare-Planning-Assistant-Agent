"""
SQLAlchemy async engine, session factory, and Base declarative model.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


import ssl as _ssl

# Strip any ?ssl / ?sslmode query params from the URL so asyncpg doesn't
# complain, then pass ssl=True via connect_args for cloud databases (Aiven etc.)
_db_url = DATABASE_URL.split("?")[0]
_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE

engine = create_async_engine(
    _db_url,
    echo=False,
    future=True,
    connect_args={"ssl": _ssl_ctx},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] All tables created successfully.")
