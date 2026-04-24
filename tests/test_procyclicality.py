from clearrisk.analytics import compute_basic_metrics
from clearrisk.config import SimulationResult


def test_procyclicality_metric_key_exists() -> None:
    result = SimulationResult(metrics={"im_procyclicality_score": 0.25})
    metrics = compute_basic_metrics(result)
    assert "im_procyclicality_score" in metrics

