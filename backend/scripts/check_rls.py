import asyncio
import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db.session import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = 'risk_cases'"))
        row = result.fetchone()
        print(row)

if __name__ == "__main__":
    asyncio.run(check())
