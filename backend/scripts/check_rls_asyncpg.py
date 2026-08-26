import asyncio
import os
import sys
import asyncpg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import settings

async def check():
    conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))
    
    # Check all cases
    cases = await conn.fetch("SELECT id, tenant_id FROM risk_cases")
    print("All Cases:")
    for c in cases:
        print(dict(c))
        
    if not cases:
        print("No cases found.")
        return

    first_tenant = cases[0]['tenant_id']
    
    # Try with RLS
    print(f"\nSetting tenant to {first_tenant}")
    await conn.execute(f"SET app.current_tenant = '{first_tenant}'")
    
    rls_cases = await conn.fetch("SELECT id, tenant_id FROM risk_cases")
    print("Cases visible to first tenant:")
    for c in rls_cases:
        print(dict(c))
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
