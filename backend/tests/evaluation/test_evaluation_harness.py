import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pandas as pd
import pytest

from src.core.schemas.evaluation import EvaluationReport
from src.db.repositories.evaluation_repo import EvaluationRepository
from src.integrations.minio_client import ObjectStoreClient
from src.ml.evaluation.harness import EvaluationHarness
from src.ml.evaluation.holdout_manager import HoldoutManager
from src.ml.serving.model_registry import ModelRegistry


@pytest.fixture
def mock_registry():
    registry = MagicMock(spec=ModelRegistry)

    # Mock model
    mock_model = MagicMock()
    # 10 rows, predict 0.9 for first 5, 0.1 for last 5
    mock_model.predict.return_value = np.array([0.9, 0.9, 0.9, 0.9, 0.9, 0.1, 0.1, 0.1, 0.1, 0.1])

    registry.get_model.return_value = mock_model
    registry.get_champion_version.return_value = None
    return registry


@pytest.fixture
def mock_holdout_manager():
    manager = MagicMock(spec=HoldoutManager)

    # Return 10 rows dataframe
    data = pd.DataFrame({
        "feature1": range(10),
        "is_abusive": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    })
    manifest = {"hash": "dummy_hash"}

    manager.load_holdout = AsyncMock(return_value=(data, manifest))
    return manager


@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=EvaluationRepository)

    mock_run = MagicMock()
    mock_run.id = uuid.uuid4()
    mock_run.evaluated_at = "2024-01-01T00:00:00Z"

    repo.create_evaluation_run = AsyncMock(return_value=mock_run)
    repo.get_champion_model = AsyncMock(return_value=None)
    repo.promote_to_champion = AsyncMock()

    return repo


@pytest.fixture
def mock_store():
    store = MagicMock(spec=ObjectStoreClient)
    store.upload_file = AsyncMock(return_value="http://s3/reports/report.json")

    # Mock download to raise Exception so harness defaults to extracting all columns
    store.download_file = AsyncMock(side_effect=Exception("Not found"))
    return store


@pytest.mark.asyncio
async def test_evaluate_and_gate_check(mock_registry, mock_holdout_manager, mock_repo, mock_store):
    harness = EvaluationHarness(
        model_registry=mock_registry,
        holdout_manager=mock_holdout_manager,
        evaluation_repo=mock_repo,
        object_store=mock_store
    )

    report = await harness.evaluate(
        model_name="test_model",
        model_version="v1",
        holdout_version="h1",
        fp_cost=Decimal("500"),
        fn_cost=Decimal("2000")
    )

    assert isinstance(report, EvaluationReport)
    assert report.model_name == "test_model"
    assert report.model_version == "v1"
    assert report.metrics.tp_count == 5
    assert report.metrics.tn_count == 5
    assert report.metrics.fp_count == 0
    assert report.metrics.fn_count == 0

    # Gate check
    passes, reason = await harness.gate_check(report)
    assert passes is True

    # Promote
    promoted = await harness.promote_if_better(report)
    assert promoted is True
    mock_repo.promote_to_champion.assert_called_once()
    mock_registry.set_champion.assert_called_once_with("test_model", "v1")
