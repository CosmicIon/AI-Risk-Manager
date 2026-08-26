import asyncio
import sys
import os
import asyncpg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import settings

async def check():
    conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))
    rows = await conn.fetch("SELECT * FROM pg_policies WHERE tablename = 'risk_cases'")
    for row in rows:
        print(dict(row))
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check())

if __name__ == "__main__":
    asyncio.run(check())
