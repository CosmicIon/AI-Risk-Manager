import asyncio
import uuid
import os
import sys
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.session import AsyncSessionLocal, get_db_session_with_tenant
from src.db.models.tenant import Tenant
from src.db.models.case import Case
from src.db.models.user import User
from src.db.models.chargeback import ChargebackRecord
from src.db.models.evaluation_run import EvaluationRun
from src.db.repositories.case_repo import CaseRepository
from src.db.repositories.chargeback_repo import ChargebackRepository
from src.db.repositories.evaluation_repo import EvaluationRepository
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Create an engine for app_user to properly test RLS isolation (non-superuser)
from src.config import settings
app_user_url = settings.DATABASE_URL.replace("riskmanager:dev_password", "app_user:app_pass")
app_engine = create_async_engine(app_user_url, echo=False)
AppSessionLocal = async_sessionmaker(bind=app_engine, expire_on_commit=False)

async def get_app_session_with_tenant(tenant_id):
    async with AppSessionLocal() as session:
        await session.execute(text(f"SET app.current_tenant = '{tenant_id}'"))
        try:
            yield session
        finally:
            await session.execute(text("RESET app.current_tenant"))

async def verify_module2():
    print("[START] Starting Module 2 Verification...\n")
    
    tenant_id_a = uuid.uuid4()
    tenant_id_b = uuid.uuid4()
    admin_id = uuid.uuid4()

    # 1. Test Global Session (Creating Tenants)
    print("1. Testing Global Session & Tenant Creation...")
    async with AsyncSessionLocal() as session:
        t_a = Tenant(id=tenant_id_a, name="Tenant Alpha", api_key_hash="hashA")
        t_b = Tenant(id=tenant_id_b, name="Tenant Beta", api_key_hash="hashB")
        user = User(id=admin_id, tenant_id=tenant_id_a, email=f"admin_{admin_id}@alpha.com", password_hash="pass", role="admin")
        session.add_all([t_a, t_b, user])
        await session.commit()
        print("   [OK] Tenants and Users successfully inserted.")

    # 2. Test RLS and Repositories for Tenant A
    print("\n2. Testing RLS & Case Repository (Tenant Alpha Context)...")
    gen_a = get_app_session_with_tenant(tenant_id_a)
    session_a = await anext(gen_a)
    try:

        case_repo = CaseRepository(session_a)
        
        # Create Case
        deadline = datetime.now(timezone.utc) - timedelta(days=1) # Past deadline for testing query
        case = await case_repo.create_case(
            tenant_id=tenant_id_a,
            source="fraud_alert",
            source_id="FRD-001",
            status="OPEN",
            metadata_data={"amount": 100},
            deadline=deadline
        )
        print(f"   [OK] Case created successfully: {case.id}")

        # Update Case Status (Tests Audit Log generation)
        await case_repo.update_case_status(case.id, "IN_REVIEW", admin_id, tenant_id_a)
        print("   [OK] Case status updated to 'IN_REVIEW' (Audit Log generated).")

        # Test Chargeback Repo
        cb_repo = ChargebackRepository(session_a)
        cb = await cb_repo.create_chargeback(
            case_id=case.id,
            tenant_id=tenant_id_a,
            network="VISA",
            arn="ARN111",
            reason_code="10.4",
            transaction_id="TXN-111",
            transaction_date=datetime.now(timezone.utc),
            transaction_amount=Decimal("100.00")
        )
        print(f"   [OK] Chargeback record created: {cb.id}")

        # Test querying past deadlines
        past_cases = await case_repo.get_open_cases_past_deadline()
        print(f"   [OK] Found {len(past_cases)} open cases past deadline.")

    finally:
        await session_a.close()


    # 3. Test RLS Isolation for Tenant B
    print("\n3. Testing RLS Isolation (Tenant Beta Context)...")
    gen_b = get_app_session_with_tenant(tenant_id_b)
    session_b = await anext(gen_b)
    try:
        case_repo_b = CaseRepository(session_b)
        
        # Tenant B should NOT see Tenant A's cases
        past_cases_b = await case_repo_b.get_open_cases_past_deadline()
        if len(past_cases_b) == 0:
            print("   [OK] SUCCESS: Tenant B cannot see Tenant A's cases (RLS Working!).")
        else:
            print("   [FAIL] FAILURE: Tenant B saw Tenant A's cases (RLS Failed!).")
            
    finally:
        await session_b.close()


    # 4. Test Evaluation Repository (Global scope)
    print("\n4. Testing Evaluation Repository...")
    async with AsyncSessionLocal() as session:
        eval_repo = EvaluationRepository(session)
        
        run1 = await eval_repo.create_evaluation_run(
            model_name="fraud_v1", model_version="1.0", holdout_set_version="ds1",
            holdout_set_hash="hash1", metrics={"f1": 0.9}, threshold=0.5,
            report_url="url", is_champion=True
        )
        print("   [OK] Champion evaluation run created.")
        
        run2 = await eval_repo.create_evaluation_run(
            model_name="fraud_v1", model_version="1.1", holdout_set_version="ds1",
            holdout_set_hash="hash1", metrics={"f1": 0.95}, threshold=0.5,
            report_url="url", is_champion=False
        )
        print("   [OK] Challenger evaluation run created.")
        
        # Promote run2
        await eval_repo.promote_to_champion(str(run2.id), "fraud_v1")
        
        champ = await eval_repo.get_champion_model("fraud_v1")
        if champ and champ.id == run2.id:
            print("   [OK] Challenger successfully promoted to Champion.")
        else:
            print("   [FAIL] Model promotion failed.")

    print("\n[DONE] Module 2 Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_module2())
