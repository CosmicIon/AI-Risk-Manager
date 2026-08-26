"""Evaluation and metrics models for ML pipelines."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CostWeightedMetrics(BaseModel):
    """Metrics incorporating the ₹-denominated cost of False Positives/Negatives."""
    precision: float
    recall: float
    f1: float
    auc_roc: float
    fp_count: int
    fn_count: int
    tp_count: int
    tn_count: int
    fp_cost_per_unit: Decimal
    fn_cost_per_unit: Decimal
    
    @property
    def total_fp_cost(self) -> Decimal:
        return self.fp_cost_per_unit * self.fp_count

    @property
    def total_fn_cost(self) -> Decimal:
        return self.fn_cost_per_unit * self.fn_count

    @property
    def cost_weighted_loss(self) -> float:
        """Compute average cost loss per prediction in the evaluation set."""
        total_samples = self.tp_count + self.tn_count + self.fp_count + self.fn_count
        if total_samples == 0:
            return 0.0
        return float((self.total_fp_cost + self.total_fn_cost) / total_samples)


class EvaluationReport(BaseModel):
    """Result of an ML model evaluation run against a holdout dataset."""
    report_id: UUID
    model_name: str
    model_version: str
    holdout_set_version: str
    holdout_set_hash: str
    metrics: CostWeightedMetrics
    threshold_used: float
    champion_model_version: str | None = None
    is_improvement: bool | None = None
    evaluated_at: datetime
    report_url: str


class DriftReport(BaseModel):
    """Data and Concept Drift monitoring report."""
    feature_name: str
    psi_value: float
    kl_divergence: float
    is_drifted: bool
    requires_retrain: bool
    reference_distribution: dict[str, float]
    current_distribution: dict[str, float]
    computed_at: datetime
