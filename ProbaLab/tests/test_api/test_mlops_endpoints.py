from unittest.mock import patch


def test_mlops_evaluate_requires_internal_auth(client):
    res = client.post("/api/trigger/mlops/evaluate")

    assert res.status_code == 401


def test_mlops_evaluate_runs_performance_snapshots(client, auth_headers):
    with patch(
        "api.routers.mlops.persist_daily_performance_snapshots",
        return_value={"inserted": 3, "windows": [1, 7, 30]},
    ) as snapshots:
        res = client.post("/api/trigger/mlops/evaluate", headers=auth_headers)

    assert res.status_code == 200
    assert res.json() == {
        "status": "ok",
        "snapshots": {"inserted": 3, "windows": [1, 7, 30]},
    }
    snapshots.assert_called_once()


def test_mlops_auto_train_returns_skipped_decision_when_policy_blocks(client, auth_headers):
    payload = {
        "sport": "football",
        "market": "1x2",
        "trigger_reason": "scheduled",
        "new_results_count": 20,
        "brier_7d": 0.18,
        "brier_30d": 0.17,
        "clv_7d": 0.01,
        "ece_30d": 0.04,
        "data_completeness_pct": 0.95,
        "hours_since_last_training": 72,
    }

    res = client.post("/api/trigger/mlops/auto-train", json=payload, headers=auth_headers)

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "skipped"
    assert body["decision"]["should_retrain"] is False
    assert body["decision"]["trigger_reason"] == "scheduled"


def test_mlops_auto_train_runs_candidate_cycle_when_policy_allows(client, auth_headers):
    policy = {
        "should_retrain": True,
        "trigger_reason": "scheduled",
        "sport": "football",
        "market": "1x2",
        "reasons": ["enough_new_results"],
        "blocked_by": [],
        "can_auto_promote": True,
    }
    candidate = {
        "id": "version-1",
        "model_name": "xgb_1x2",
        "model_version": "xgb_1x2_20260427120000_abcd1234",
        "sport": "football",
        "market": "1x2",
        "metrics": {
            "holdout_samples": 520,
            "brier": 0.18,
            "log_loss": 0.54,
            "ece": 0.04,
            "clv_mean": 0.012,
        },
    }
    active = {
        "model_name": "xgb_1x2",
        "model_version": "xgb_1x2_old",
        "metrics": {
            "holdout_samples": 500,
            "brier": 0.185,
            "log_loss": 0.55,
            "ece": 0.05,
            "clv_mean": 0.01,
        },
    }
    promotion = {
        "decision": "promote",
        "reason": "quality_gate_passed",
        "candidate_version": candidate["model_version"],
        "active_version": active["model_version"],
        "thresholds": {"min_holdout_samples": 300},
    }

    with (
        patch("api.routers.mlops.should_retrain", return_value=policy),
        patch(
            "api.routers.mlops.run_candidate_training",
            return_value={"status": "success", "run": {"id": "run-1"}, "candidate": candidate},
            create=True,
        ) as train_candidate,
        patch(
            "api.routers.mlops._latest_active_model_version",
            return_value=active,
            create=True,
        ) as active_lookup,
        patch(
            "api.routers.mlops.decide_promotion",
            return_value=promotion,
            create=True,
        ) as decide,
        patch(
            "api.routers.mlops.apply_promotion_decision",
            return_value={"status": "applied", "decision": promotion},
            create=True,
        ) as apply_decision,
    ):
        res = client.post(
            "/api/trigger/mlops/auto-train",
            json={
                "sport": "football",
                "market": "1x2",
                "trigger_reason": "scheduled",
                "new_results_count": 140,
            },
            headers=auth_headers,
        )

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "completed"
    assert body["decision"] == policy
    assert body["training"]["status"] == "success"
    assert body["promotion"]["decision"] == "promote"
    train_candidate.assert_called_once()
    active_lookup.assert_called_once_with("xgb_1x2")
    decide.assert_called_once_with(candidate, active)
    apply_decision.assert_called_once_with(
        candidate=candidate,
        active=active,
        promotion=promotion,
        can_auto_promote=True,
    )


def test_mlops_health_requires_internal_auth(client):
    res = client.get("/api/admin/mlops/health")

    assert res.status_code == 401


def test_mlops_health_returns_latest_sections(client, auth_headers, mock_supabase):
    mock_supabase.table.return_value.execute.return_value.data = [{"id": "run-1"}]

    res = client.get("/api/admin/mlops/health", headers=auth_headers)

    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"runs", "models", "performance", "decisions"}
