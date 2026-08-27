import uuid
import json
from decimal import Decimal
import pandas as pd

from src.core.schemas.evaluation import EvaluationReport
from src.ml.serving.model_registry import ModelRegistry
from src.ml.evaluation.holdout_manager import HoldoutManager
from src.db.repositories.evaluation_repo import EvaluationRepository
from src.integrations.minio_client import ObjectStoreClient
from src.ml.evaluation.metrics import (
    compute_calibration_curve, 
    compute_threshold_curve, 
    find_optimal_threshold
)

class EvaluationHarness:
    def __init__(
        self, 
        model_registry: ModelRegistry, 
        holdout_manager: HoldoutManager, 
        evaluation_repo: EvaluationRepository, 
        object_store: ObjectStoreClient
    ):
        self.model_registry = model_registry
        self.holdout_manager = holdout_manager
        self.evaluation_repo = evaluation_repo
        self.object_store = object_store
        
    async def evaluate(
        self, 
        model_name: str, 
        model_version: str, 
        holdout_version: str, 
        fp_cost: Decimal, 
        fn_cost: Decimal, 
        target_col: str = "is_abusive"
    ) -> EvaluationReport:
        # 1. Load holdout set
        data, manifest = await self.holdout_manager.load_holdout(holdout_version)
        
        # 2. Load model
        model = self.model_registry.get_model(model_name, model_version)
        
        # 3. Extract features
        try:
            meta_bytes = await self.object_store.download_file("models", f"{model_name}/{model_version}/metadata.json")
            metadata = json.loads(meta_bytes.decode('utf-8'))
            feature_names = metadata.get("feature_names", [])
        except Exception:
            feature_names = [c for c in data.columns if c != target_col and not c.endswith("_id")]
            
        if feature_names:
            X = data[feature_names].values
        else:
            X = data.drop(columns=[target_col]).values
            
        y_true = data[target_col].values
        
        # 4. Run inference
        y_prob = model.predict(X)
        if len(y_prob.shape) > 1 and y_prob.shape[1] > 1:
            y_prob = y_prob[:, 1]
        elif len(y_prob.shape) > 1:
            y_prob = y_prob.ravel()
            
        # 5 & 6. Compute metrics and find optimal threshold
        best_threshold, best_metrics = find_optimal_threshold(y_true, y_prob, fp_cost, fn_cost)
        
        # 7. Compare against champion model
        champ_version = self.model_registry.get_champion_version(model_name)
        is_improvement = None
        if champ_version:
            try:
                champ_model = self.model_registry.get_model(model_name, champ_version)
                champ_prob = champ_model.predict(X)
                if len(champ_prob.shape) > 1 and champ_prob.shape[1] > 1:
                    champ_prob = champ_prob[:, 1]
                elif len(champ_prob.shape) > 1:
                    champ_prob = champ_prob.ravel()
                
                _, champ_metrics = find_optimal_threshold(y_true, champ_prob, fp_cost, fn_cost)
                is_improvement = best_metrics.cost_weighted_loss < champ_metrics.cost_weighted_loss
            except Exception:
                pass
                
        # 8. Generate full report
        calib_curve = compute_calibration_curve(y_true, y_prob)
        thresh_curve = compute_threshold_curve(y_true, y_prob, fp_cost, fn_cost)
        
        report_data = {
            "metrics": best_metrics.model_dump(mode='json'),
            "threshold_used": best_threshold,
            "calibration_curve": calib_curve,
            "threshold_curve": thresh_curve,
            "is_improvement": is_improvement
        }
        
        # 9. Upload report to S3
        report_id = uuid.uuid4()
        report_key = f"{model_name}/{model_version}/report_{report_id}.json"
        report_url = await self.object_store.upload_file(
            "reports", report_key, json.dumps(report_data).encode('utf-8'), "application/json"
        )
        
        # 10. Persist EvaluationRun
        run = await self.evaluation_repo.create_evaluation_run(
            model_name=model_name,
            model_version=model_version,
            holdout_set_version=holdout_version,
            holdout_set_hash=manifest["hash"],
            metrics=best_metrics.model_dump(mode='json'),
            threshold=best_threshold,
            report_url=report_url,
            is_champion=False
        )
        
        # 11. Return EvaluationReport
        return EvaluationReport(
            report_id=run.id,
            model_name=model_name,
            model_version=model_version,
            holdout_set_version=holdout_version,
            holdout_set_hash=manifest["hash"],
            metrics=best_metrics,
            threshold_used=best_threshold,
            champion_model_version=champ_version if champ_version else None,
            is_improvement=is_improvement,
            evaluated_at=run.evaluated_at,
            report_url=report_url
        )
        
    async def gate_check(
        self, 
        report: EvaluationReport, 
        min_precision: float = 0.7, 
        min_recall: float = 0.5, 
        max_cost_increase_pct: float = 5.0
    ) -> tuple[bool, str]:
        if report.metrics.precision < min_precision:
            return False, f"Precision {report.metrics.precision:.2f} < {min_precision}"
        if report.metrics.recall < min_recall:
            return False, f"Recall {report.metrics.recall:.2f} < {min_recall}"
            
        if report.champion_model_version and report.is_improvement is False:
            champ = await self.evaluation_repo.get_champion_model(report.model_name)
            if champ:
                champ_loss = champ.metrics.get("cost_weighted_loss", 0.0)
                new_loss = report.metrics.cost_weighted_loss
                if champ_loss > 0:
                    increase = ((new_loss - champ_loss) / champ_loss) * 100
                    if increase > max_cost_increase_pct:
                        return False, f"Cost loss increased by {increase:.2f}% (max {max_cost_increase_pct}%)"
                        
        return True, "Passed"
        
    async def promote_if_better(self, report: EvaluationReport) -> bool:
        passes, _ = await self.gate_check(report)
        if passes and (report.is_improvement is True or report.champion_model_version is None):
            await self.evaluation_repo.promote_to_champion(str(report.report_id), report.model_name)
            self.model_registry.set_champion(report.model_name, report.model_version)
            return True
        return False
