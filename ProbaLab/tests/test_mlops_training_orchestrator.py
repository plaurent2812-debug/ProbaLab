from unittest.mock import patch

from src.mlops.training_orchestrator import (
    mark_training_run_failed,
    register_candidate_version,
    run_candidate_training,
    start_training_run,
    train_candidate_for_run,
)


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
            row = {**self.payload}
            row.setdefault("id", f"{self.name}-1")
            self.db.inserts.append((self.name, row))
            return ExecuteResult([row])
        if self.operation == "update":
            self.db.updates.append((self.name, self.payload, self.filters))
            return ExecuteResult([{**self.payload, "id": self.filters[0][1]}])
        raise AssertionError(f"Unexpected operation for {self.name}: {self.operation}")


class FakeSupabase:
    def __init__(self):
        self.inserts = []
        self.updates = []

    def table(self, name):
        return TableRecorder(name, self)


def test_start_training_run_inserts_running_record():
    db = FakeSupabase()

    run = start_training_run(
        supabase_client=db,
        sport="football",
        market="1x2",
        trigger_reason="scheduled",
    )

    assert run["status"] == "running"
    assert db.inserts[0][0] == "model_training_runs"
    assert db.inserts[0][1]["sport"] == "football"
    assert db.inserts[0][1]["market"] == "1x2"
    assert db.inserts[0][1]["trigger_reason"] == "scheduled"


def test_mark_training_run_failed_closes_run_with_error_message():
    db = FakeSupabase()

    result = mark_training_run_failed(
        supabase_client=db,
        training_run_id="run-1",
        error_message="training crashed",
    )

    assert result["status"] == "failed"
    table, payload, filters = db.updates[0]
    assert table == "model_training_runs"
    assert payload["status"] == "failed"
    assert payload["error_message"] == "training crashed"
    assert ("id", "run-1") in filters


def test_register_candidate_version_never_marks_candidate_active():
    db = FakeSupabase()

    version = register_candidate_version(
        supabase_client=db,
        training_run_id="run-1",
        model_name="xgb_1x2",
        sport="football",
        market="1x2",
        model_type="xgboost",
        artifact_ref="ml_models:xgb_1x2_candidate",
        feature_names=["elo_diff", "form_diff"],
        metrics={"brier": 0.18},
    )

    assert version["is_active"] is False
    assert version["model_version"].startswith("xgb_1x2_")
    table, payload = db.inserts[0]
    assert table == "model_versions"
    assert payload["training_run_id"] == "run-1"
    assert payload["metrics"] == {"brier": 0.18}


def test_run_candidate_training_marks_failed_when_trainer_raises():
    db = FakeSupabase()

    def trainer(_run):
        raise RuntimeError("boom")

    result = run_candidate_training(
        supabase_client=db,
        sport="football",
        market="1x2",
        trigger_reason="manual",
        trainer=trainer,
    )

    assert result["status"] == "failed"
    assert db.updates[0][0] == "model_training_runs"
    assert db.updates[0][1]["error_message"] == "boom"


def test_train_candidate_for_run_stores_inactive_versioned_artifact():
    db = FakeSupabase()
    artifact = {
        "model_name": "xgb_1x2",
        "model_type": "xgboost",
        "accuracy": 0.56,
        "brier_score": 0.18,
        "log_loss_val": 0.54,
        "f1_score": 0.55,
        "feature_names": ["elo_diff", "form_diff"],
        "training_samples": 600,
        "model_weights": "encoded",
        "is_active": True,
    }

    with (
        patch("src.training.train.load_data", return_value=[{"id": 1}]),
        patch("src.training.train.prepare_features", return_value=([[1.0, 2.0]], object())),
        patch("src.training.train.prepare_target_classification", return_value=["H"]),
        patch("src.training.train.train_classifier", return_value=artifact),
    ):
        candidate = train_candidate_for_run(
            {"sport": "football", "market": "1x2"},
            supabase_client=db,
        )

    assert candidate["model_name"] == "xgb_1x2"
    assert candidate["model_version"].startswith("xgb_1x2_")
    assert candidate["artifact_ref"].startswith("ml_models:xgb_1x2__xgb_1x2_")
    assert candidate["metrics"]["training_samples"] == 600
    assert candidate["metrics"]["holdout_samples"] == 0
    table, payload = db.inserts[0]
    assert table == "ml_models"
    assert payload["model_name"].startswith("xgb_1x2__xgb_1x2_")
    assert payload["is_active"] is False
