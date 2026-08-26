import asyncio
import uuid
import os
import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.session import AsyncSessionLocal
from src.db.models.tenant import Tenant
from src.db.models.user import User
from src.db.models.case import Case
from src.db.models.chargeback import ChargebackRecord
from src.db.models.evaluation_run import EvaluationRun

async def main():
    async with AsyncSessionLocal() as session:
        # Create a mock Tenant
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            name="Mock Enterprise Corp",
            api_key_hash="mock_hash_123",
            fp_cost_per_unit=Decimal("500.00"),
            fn_cost_per_unit=Decimal("2000.00"),
            policy_config={"allowed_networks": ["VISA", "MASTERCARD"]}
        )
        session.add(tenant)
        await session.flush()
        
        # Create an Admin User
        user = User(
            tenant_id=tenant.id,
            email="admin@mockcorp.com",
            password_hash="hashed_password",
            role="admin"
        )
        session.add(user)
        
        # Create a Case
        deadline = datetime.now(timezone.utc) + timedelta(days=7)
        case = Case(
            tenant_id=tenant.id,
            source="chargeback",
            source_id="CB-2023-0001",
            status="OPEN",
            priority=1,
            deadline=deadline,
            assigned_to=user.id,
            metadata_data={"amount": 499.99}
        )
        session.add(case)
        await session.flush()
        
        # Create ChargebackRecord
        chargeback = ChargebackRecord(
            case_id=case.id,
            tenant_id=tenant.id,
            network="VISA",
            arn="ARN12345678901234567890123",
            reason_code="10.4",
            transaction_id="TXN-999888",
            transaction_date=datetime.now(timezone.utc) - timedelta(days=15),
            transaction_amount=Decimal("499.99"),
            win_probability=0.85
        )
        session.add(chargeback)
        
        # Create EvaluationRun
        eval_run = EvaluationRun(
            model_name="fraud_defense_v2",
            model_version="v2.1.0",
            holdout_set_version="ds_2023_Q3",
            holdout_set_hash="sha256:abcd1234efgh5678",
            metrics={"roc_auc": 0.94, "cost_weighted_loss": 125000},
            threshold=0.72,
            is_champion=True,
            report_url="http://langfuse.local/reports/fraud_defense_v2_1_0"
        )
        session.add(eval_run)
        
        await session.commit()
        print(f"✅ Successfully seeded database!")
        print(f"Tenant ID: {tenant.id}")
        print(f"User ID: {user.id}")
        print(f"Case ID: {case.id}")

if __name__ == "__main__":
    asyncio.run(main())
