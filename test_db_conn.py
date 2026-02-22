import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from backend.config import DATABASE_URL

async def test_db():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        engine = create_async_engine(DATABASE_URL)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"Success! Result: {result.scalar()}")
        await engine.dispose()
    except Exception as e:
        print(f"DB Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
