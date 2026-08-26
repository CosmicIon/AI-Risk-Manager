from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.db.models.evaluation_run import EvaluationRun

class EvaluationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_evaluation_run(
        self, model_name: str, model_version: str, holdout_set_version: str,
        holdout_set_hash: str, metrics: dict[str, Any], threshold: float,
        report_url: str, is_champion: bool = False
    ) -> EvaluationRun:
        run = EvaluationRun(
            model_name=model_name,
            model_version=model_version,
            holdout_set_version=holdout_set_version,
            holdout_set_hash=holdout_set_hash,
            metrics=metrics,
            threshold=threshold,
            report_url=report_url,
            is_champion=is_champion
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_champion_model(self, model_name: str) -> Optional[EvaluationRun]:
        stmt = (
            select(EvaluationRun)
            .where(EvaluationRun.model_name == model_name, EvaluationRun.is_champion == True)
            .order_by(desc(EvaluationRun.evaluated_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def promote_to_champion(self, run_id: str, model_name: str) -> Optional[EvaluationRun]:
        # Demote current champion
        current_champ = await self.get_champion_model(model_name)
        if current_champ:
            current_champ.is_champion = False

        # Promote new
        stmt = select(EvaluationRun).where(EvaluationRun.id == run_id)
        result = await self.session.execute(stmt)
        new_champ = result.scalar_one_or_none()
        
        if new_champ:
            new_champ.is_champion = True
            
        await self.session.commit()
        
        if new_champ:
            await self.session.refresh(new_champ)
            
        return new_champ
