import pytest

from tradingagents.metrics.cost_tracker import CostTracker


def test_cost_tracker_aggregates_by_model_and_section():
    tracker = CostTracker(
        {
            "model-a": {
                "input_cost_per_1k_tokens": 0.01,
                "output_cost_per_1k_tokens": 0.03,
            },
            "model-b": {
                "input_cost_per_1k_tokens": 0.02,
                "output_cost_per_1k_tokens": 0.04,
            },
        }
    )

    with tracker.section("Macro Economist"):
        tracker.record_usage(
            model_name="model-a",
            input_tokens=1000,
            output_tokens=500,
        )

    with tracker.section("Risk Team"):
        tracker.record_usage(
            model_name="model-a",
            input_tokens=0,
            output_tokens=250,
        )
        tracker.record_usage(
            model_name="model-b",
            input_tokens=2000,
            output_tokens=1000,
        )

    summary = tracker.summary()

    assert summary["total_cost"] == pytest.approx(0.1125, rel=1e-5)

    model_a = summary["models"]["model-a"]
    assert model_a["calls"] == 2
    assert model_a["input_tokens"] == 1000
    assert model_a["output_tokens"] == 750
    assert model_a["cost"] == pytest.approx(0.0325, rel=1e-5)

    model_b = summary["models"]["model-b"]
    assert model_b["cost"] == pytest.approx(0.08, rel=1e-5)
    assert model_b["calls"] == 1

    macro_section = summary["sections"]["Macro Economist"]
    assert macro_section["calls"] == 1
    assert macro_section["cost"] == pytest.approx(0.025, rel=1e-5)

    risk_section = summary["sections"]["Risk Team"]
    assert risk_section["calls"] == 2
    assert risk_section["cost"] == pytest.approx(0.0875, rel=1e-5)


def test_cost_tracker_reset_clears_prior_stats():
    tracker = CostTracker(
        {
            "model-c": {
                "input_cost_per_1k_tokens": 0.05,
                "output_cost_per_1k_tokens": 0.05,
            }
        }
    )

    tracker.record_usage("model-c", input_tokens=1000, output_tokens=1000)
    assert tracker.summary()["total_cost"] == pytest.approx(0.1, rel=1e-5)

    tracker.reset()
    summary_after_reset = tracker.summary()
    assert summary_after_reset["total_cost"] == 0
    assert summary_after_reset["models"] == {}
    assert summary_after_reset["sections"] == {}
