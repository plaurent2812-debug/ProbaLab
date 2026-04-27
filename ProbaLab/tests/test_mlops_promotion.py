from src.mlops.promotion import apply_promotion_decision, decide_promotion

ACTIVE = {
    "model_name": "xgb_1x2",
    "model_version": "xgb_1x2_old",
    "sport": "football",
    "market": "1x2",
    "metrics": {
        "holdout_samples": 500,
        "brier": 0.185,
        "log_loss": 0.55,
        "ece": 0.05,
        "clv_mean": 0.01,
    },
}


def test_promotes_candidate_that_improves_core_metrics():
    candidate = {
        **ACTIVE,
        "model_version": "xgb_1x2_new",
        "metrics": {
            "holdout_samples": 520,
            "brier": 0.18,
            "log_loss": 0.54,
            "ece": 0.04,
            "clv_mean": 0.012,
        },
    }

    decision = decide_promotion(candidate, ACTIVE)

    assert decision["decision"] == "promote"
    assert decision["candidate_version"] == "xgb_1x2_new"
    assert decision["active_version"] == "xgb_1x2_old"


def test_rejects_candidate_with_brier_regression():
    candidate = {
        **ACTIVE,
        "model_version": "xgb_1x2_bad",
        "metrics": {
            "holdout_samples": 520,
            "brier": 0.19,
            "log_loss": 0.54,
            "ece": 0.04,
            "clv_mean": 0.012,
        },
    }

    decision = decide_promotion(candidate, ACTIVE)

    assert decision["decision"] == "reject"
    assert "brier_regression" in decision["reason"]


def test_manual_review_when_holdout_sample_is_too_small():
    candidate = {
        **ACTIVE,
        "model_version": "xgb_1x2_small",
        "metrics": {
            "holdout_samples": 50,
            "brier": 0.17,
            "log_loss": 0.50,
            "ece": 0.03,
            "clv_mean": 0.02,
        },
    }

    decision = decide_promotion(candidate, ACTIVE)

    assert decision["decision"] == "manual_review"
    assert "insufficient_holdout_samples" in decision["reason"]


def test_rejects_candidate_with_degraded_clv():
    candidate = {
        **ACTIVE,
        "model_version": "xgb_1x2_clv_bad",
        "metrics": {
            "holdout_samples": 520,
            "brier": 0.18,
            "log_loss": 0.54,
            "ece": 0.04,
            "clv_mean": 0.0,
        },
    }

    decision = decide_promotion(candidate, ACTIVE)

    assert decision["decision"] == "reject"
    assert "clv_regression" in decision["reason"]


def test_first_model_can_be_promoted_when_quality_gate_passes():
    candidate = {
        **ACTIVE,
        "model_version": "xgb_1x2_first",
        "metrics": {
            "holdout_samples": 520,
            "brier": 0.18,
            "log_loss": 0.54,
            "ece": 0.04,
            "clv_mean": 0.01,
        },
    }

    decision = decide_promotion(candidate, None)

    assert decision["decision"] == "promote"
    assert decision["active_version"] is None


class ExecuteResult:
    def __init__(self, data):
        self.data = data


class TableRecorder:
    def __init__(self, name: str, db: "FakeSupabase"):
        self.name = name
        self.db = db
        self.operation = None
        self.payload = None
        self.filters = []

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def execute(self):
        if self.operation == "insert":
            self.db.inserts.append((self.name, self.payload))
            return ExecuteResult([self.payload])
        if self.operation == "update":
            self.db.updates.append((self.name, self.payload, self.filters))
            return ExecuteResult([self.payload])
        raise AssertionError(f"Unexpected operation for {self.name}: {self.operation}")


class FakeSupabase:
    def __init__(self):
        self.inserts = []
        self.updates = []

    def table(self, name):
        return TableRecorder(name, self)


def test_apply_promotion_decision_records_and_activates_candidate():
    db = FakeSupabase()
    candidate = {
        "id": "version-1",
        "training_run_id": "run-1",
        "model_name": "xgb_1x2",
        "model_version": "xgb_1x2_new",
        "metrics": {"brier": 0.18},
    }
    promotion = {
        "decision": "promote",
        "reason": "quality_gate_passed",
        "candidate_version": "xgb_1x2_new",
        "active_version": "xgb_1x2_old",
        "thresholds": {"min_holdout_samples": 300},
    }

    result = apply_promotion_decision(
        supabase_client=db,
        candidate=candidate,
        active=ACTIVE,
        promotion=promotion,
        can_auto_promote=True,
    )

    assert result["status"] == "applied"
    assert db.inserts[0][0] == "model_promotion_decisions"
    assert db.inserts[0][1]["candidate_version"] == "xgb_1x2_new"
    assert db.updates[0][1] == {"is_active": False}
    assert ("model_name", "xgb_1x2") in db.updates[0][2]
    assert db.updates[1][1]["is_active"] is True
    assert ("id", "version-1") in db.updates[1][2]


def test_apply_promotion_decision_downgrades_manual_auto_promote_to_review():
    db = FakeSupabase()
    candidate = {
        "model_name": "xgb_1x2",
        "model_version": "xgb_1x2_manual",
        "metrics": {"brier": 0.18},
    }
    promotion = {
        "decision": "promote",
        "reason": "quality_gate_passed",
        "candidate_version": "xgb_1x2_manual",
        "active_version": "xgb_1x2_old",
        "thresholds": {},
    }

    result = apply_promotion_decision(
        supabase_client=db,
        candidate=candidate,
        active=ACTIVE,
        promotion=promotion,
        can_auto_promote=False,
    )

    assert result["status"] == "recorded"
    assert result["decision"]["decision"] == "manual_review"
    assert result["decision"]["reason"] == "manual_candidate_requires_review"
    assert db.updates == []
