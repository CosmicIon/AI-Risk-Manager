import asyncio
import os
import sys
import asyncpg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import settings

async def check():
    conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))
    
    # Create non-superuser role
    try:
        await conn.execute("CREATE ROLE test_rls_user WITH LOGIN PASSWORD 'password'")
    except Exception as e:
        print("Role might exist:", e)
        
    await conn.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_rls_user")
    await conn.execute("ALTER TABLE risk_cases FORCE ROW LEVEL SECURITY")
    await conn.close()
    
    print("Connecting as non-superuser...")
    user_conn_string = settings.DATABASE_URL.replace('+asyncpg', '').replace('postgres:postgres', 'test_rls_user:password')
    conn2 = await asyncpg.connect(user_conn_string)
    
    cases = await conn2.fetch("SELECT id, tenant_id FROM risk_cases")
    if not cases:
        print("No cases visible initially (expected because app.current_tenant is not set or policy throws error)")
    else:
        print(f"ERROR: Visible cases initially: {len(cases)}")
        
    # Get a tenant ID from superuser
    conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))
    cases_super = await conn.fetch("SELECT id, tenant_id FROM risk_cases LIMIT 1")
    first_tenant = cases_super[0]['tenant_id']
    await conn.close()
    
    print(f"\nSetting tenant to {first_tenant}")
    await conn2.execute(f"SET app.current_tenant = '{first_tenant}'")
    
    rls_cases = await conn2.fetch("SELECT id, tenant_id FROM risk_cases")
    print("Cases visible to test_user:")
    for c in rls_cases:
        print(dict(c))
        
    await conn2.close()

if __name__ == "__main__":
    asyncio.run(check())
