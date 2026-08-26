import asyncio
import uuid
import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.session import AsyncSessionLocal, get_db_session_with_tenant
from src.db.models.tenant import Tenant
from src.db.models.case import Case

async def test_rls():
    async with AsyncSessionLocal() as session:
        # Create tenants
        t1 = Tenant(name="T1", api_key_hash="hash1")
        t2 = Tenant(name="T2", api_key_hash="hash2")
        session.add_all([t1, t2])
        await session.flush()
        
        # Create cases
        c1 = Case(tenant_id=t1.id, source="test", source_id="1", status="OPEN")
        c2 = Case(tenant_id=t2.id, source="test", source_id="2", status="OPEN")
        session.add_all([c1, c2])
        await session.commit()
        print(f"Created Tenant 1: {t1.id}, Case: {c1.id}")
        print(f"Created Tenant 2: {t2.id}, Case: {c2.id}")
        
        t1_id = t1.id
        t2_id = t2.id

    print("\n--- Testing RLS for Tenant 1 ---")
    gen1 = get_db_session_with_tenant(t1_id)
    session1 = await anext(gen1)
    
    # We must alter table to FORCE ROW LEVEL SECURITY because postgres user is superuser
    await session1.execute(text("ALTER TABLE risk_cases FORCE ROW LEVEL SECURITY"))
    await session1.commit()
    
    result1 = await session1.execute(text("SELECT id FROM risk_cases"))
    cases1 = result1.fetchall()
    print(f"Tenant 1 sees {len(cases1)} cases:")
    for c in cases1:
        print(f" - {c[0]}")
    
    await session1.close()

    print("\n--- Testing RLS for Tenant 2 ---")
    gen2 = get_db_session_with_tenant(t2_id)
    session2 = await anext(gen2)
    result2 = await session2.execute(text("SELECT id FROM risk_cases"))
    cases2 = result2.fetchall()
    print(f"Tenant 2 sees {len(cases2)} cases:")
    for c in cases2:
        print(f" - {c[0]}")
        
    await session2.close()
    
    # Clean up FORCE RLS just in case
    async with AsyncSessionLocal() as session:
        await session.execute(text("ALTER TABLE risk_cases NO FORCE ROW LEVEL SECURITY"))
        await session.commit()

if __name__ == "__main__":
    asyncio.run(test_rls())
