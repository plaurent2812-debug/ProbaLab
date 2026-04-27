from src.mlops.retrain_policy import should_retrain

BASE_CONTEXT = {
    "sport": "football",
    "market": "1x2",
    "trigger_reason": "scheduled",
    "new_results_count": 140,
    "brier_7d": 0.18,
    "brier_30d": 0.17,
    "clv_7d": 0.01,
    "ece_30d": 0.04,
    "data_completeness_pct": 0.95,
    "hours_since_last_training": 72,
}


def test_scheduled_retrain_runs_when_enough_new_football_results():
    decision = should_retrain(BASE_CONTEXT)

    assert decision["should_retrain"] is True
    assert decision["trigger_reason"] == "scheduled"
    assert "enough_new_results" in decision["reasons"]


def test_scheduled_retrain_blocks_when_new_data_is_too_small():
    context = {**BASE_CONTEXT, "new_results_count": 20}

    decision = should_retrain(context)

    assert decision["should_retrain"] is False
    assert "insufficient_new_results" in decision["blocked_by"]


def test_drift_retrain_runs_when_brier_degrades_enough():
    context = {
        **BASE_CONTEXT,
        "trigger_reason": "drift",
        "new_results_count": 40,
        "brier_7d": 0.205,
        "brier_30d": 0.18,
    }

    decision = should_retrain(context)

    assert decision["should_retrain"] is True
    assert "brier_drift" in decision["reasons"]


def test_retrain_blocks_when_data_completeness_is_low():
    context = {**BASE_CONTEXT, "data_completeness_pct": 0.72}

    decision = should_retrain(context)

    assert decision["should_retrain"] is False
    assert "low_data_completeness" in decision["blocked_by"]


def test_retrain_blocks_when_cooldown_is_active():
    context = {**BASE_CONTEXT, "hours_since_last_training": 10}

    decision = should_retrain(context)

    assert decision["should_retrain"] is False
    assert "cooldown_active" in decision["blocked_by"]


def test_manual_can_create_candidate_but_not_force_promotion():
    context = {
        **BASE_CONTEXT,
        "trigger_reason": "manual",
        "new_results_count": 0,
        "hours_since_last_training": 1,
    }

    decision = should_retrain(context)

    assert decision["should_retrain"] is True
    assert decision["trigger_reason"] == "manual"
    assert "manual_candidate" in decision["reasons"]
    assert decision["can_auto_promote"] is False
