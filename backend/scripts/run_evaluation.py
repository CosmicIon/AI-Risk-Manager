import asyncio
import argparse
import sys
import json
from decimal import Decimal

from src.core.config import settings
from src.db.session import Database
from src.db.repositories.evaluation_repo import EvaluationRepository
from src.ml.serving.model_registry import ModelRegistry
from src.ml.evaluation.holdout_manager import HoldoutManager
from src.integrations.minio_client import ObjectStoreClient
from src.ml.evaluation.harness import EvaluationHarness


async def run_eval(model_name: str, model_version: str, holdout_version: str, fp_cost: str, fn_cost: str):
    db = Database(settings.DATABASE_URL)
    
    object_store = ObjectStoreClient(
        endpoint_url=settings.MINIO_URL,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
    )
    
    registry = ModelRegistry()
    
    # Needs a real model path but in a generic evaluation we might fetch it or have it locally.
    # We will assume it's already downloaded or available at a local path based on version.
    # Or for this script, we'll let registry fail if not loaded, or we could download it.
    model_path = f"models/{model_name}_{model_version}.onnx"
    try:
        # download first
        model_bytes = await object_store.download_file("models", f"{model_name}/{model_version}/model.onnx")
        with open(model_path, "wb") as f:
            f.write(model_bytes)
        registry.load_model(model_name, model_version, model_path)
    except Exception as e:
        print(f"Failed to load model {model_name}:{model_version} from S3: {e}")
        sys.exit(1)

    # We also need to load the champion if we want to compare
    
    holdout_manager = HoldoutManager(object_store)
    
    fp_cost_dec = Decimal(fp_cost)
    fn_cost_dec = Decimal(fn_cost)
    
    async with db.session() as session:
        repo = EvaluationRepository(session)
        
        # Determine champion
        champ = await repo.get_champion_model(model_name)
        if champ:
            registry.set_champion(model_name, champ.model_version)
            try:
                champ_bytes = await object_store.download_file("models", f"{model_name}/{champ.model_version}/model.onnx")
                champ_path = f"models/{model_name}_{champ.model_version}.onnx"
                with open(champ_path, "wb") as f:
                    f.write(champ_bytes)
                registry.load_model(model_name, champ.model_version, champ_path)
            except Exception as e:
                print(f"Warning: Failed to load champion model: {e}")
        
        harness = EvaluationHarness(registry, holdout_manager, repo, object_store)
        
        print(f"Starting evaluation for {model_name}:{model_version} on holdout {holdout_version}...")
        report = await harness.evaluate(model_name, model_version, holdout_version, fp_cost_dec, fn_cost_dec)
        
        passes_gate, reason = await harness.gate_check(report)
        promoted = False
        
        if passes_gate:
            promoted = await harness.promote_if_better(report)
            
        summary = {
            "model_name": model_name,
            "model_version": model_version,
            "metrics": report.metrics.model_dump(mode='json'),
            "passes_gate": passes_gate,
            "gate_reason": reason,
            "promoted": promoted,
            "report_url": report.report_url,
            "is_improvement": report.is_improvement
        }
        
        print("\n=== EVALUATION RESULTS ===")
        print(json.dumps(summary, indent=2))
        
        # Write to github actions output if in CI
        with open("eval_summary.json", "w") as f:
            json.dump(summary, f)
            
        if not passes_gate:
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run ML Model Evaluation")
    parser.add_argument("--model-name", required=True, help="Name of the model (e.g. return_risk)")
    parser.add_argument("--model-version", required=True, help="Version of the model to evaluate")
    parser.add_argument("--holdout-version", required=True, help="Holdout set version to use")
    parser.add_argument("--fp-cost", required=True, help="Cost per False Positive")
    parser.add_argument("--fn-cost", required=True, help="Cost per False Negative")
    
    args = parser.parse_args()
    
    # Ensure models dir exists
    import os
    os.makedirs("models", exist_ok=True)
    
    asyncio.run(run_eval(
        args.model_name,
        args.model_version,
        args.holdout_version,
        args.fp_cost,
        args.fn_cost
    ))


if __name__ == "__main__":
    main()
