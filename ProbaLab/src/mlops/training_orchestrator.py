import hashlib
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from src.config import supabase


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_hash(parts: list[str]) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:8]


def _client(supabase_client=None):
    return supabase_client or supabase


def start_training_run(
    *,
    sport: str,
    market: str,
    trigger_reason: str,
    supabase_client=None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a running MLOps training-run record."""
    payload = {
        "status": "running",
        "trigger_reason": trigger_reason,
        "sport": sport,
        "market": market,
        "metadata": metadata or {},
    }
    result = _client(supabase_client).table("model_training_runs").insert(payload).execute()
    return (result.data or [payload])[0]


def mark_training_run_failed(
    *,
    training_run_id: str,
    error_message: str,
    supabase_client=None,
) -> dict[str, Any]:
    """Close a training run as failed with an explicit error."""
    payload = {
        "status": "failed",
        "finished_at": _now_iso(),
        "error_message": error_message,
    }
    result = (
        _client(supabase_client)
        .table("model_training_runs")
        .update(payload)
        .eq("id", training_run_id)
        .execute()
    )
    return (result.data or [payload])[0]


def mark_training_run_success(
    *,
    training_run_id: str,
    training_samples: int = 0,
    holdout_samples: int = 0,
    supabase_client=None,
) -> dict[str, Any]:
    """Close a training run as successful after candidate creation."""
    payload = {
        "status": "success",
        "finished_at": _now_iso(),
        "training_samples": training_samples,
        "holdout_samples": holdout_samples,
    }
    result = (
        _client(supabase_client)
        .table("model_training_runs")
        .update(payload)
        .eq("id", training_run_id)
        .execute()
    )
    return (result.data or [payload])[0]


def build_model_version(model_name: str, feature_names: list[str] | None = None) -> str:
    """Build a unique, sortable candidate version identifier."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    feature_hash = _short_hash([model_name, *(feature_names or []), timestamp])
    return f"{model_name}_{timestamp}_{feature_hash}"


def register_candidate_version(
    *,
    training_run_id: str,
    model_name: str,
    sport: str,
    market: str,
    model_type: str,
    artifact_ref: str,
    supabase_client=None,
    feature_names: list[str] | None = None,
    metrics: dict[str, Any] | None = None,
    model_version: str | None = None,
    artifact_table: str = "ml_models",
    train_window: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Register a candidate model version without activating it."""
    feature_names = feature_names or []
    version = model_version or build_model_version(model_name, feature_names)
    payload = {
        "training_run_id": training_run_id,
        "model_name": model_name,
        "model_version": version,
        "sport": sport,
        "market": market,
        "model_type": model_type,
        "artifact_table": artifact_table,
        "artifact_ref": artifact_ref,
        "feature_names": feature_names,
        "feature_hash": _short_hash(feature_names),
        "train_window": train_window or {},
        "metrics": metrics or {},
        "is_active": False,
    }
    result = _client(supabase_client).table("model_versions").insert(payload).execute()
    return (result.data or [payload])[0]


def train_candidate_for_run(run: dict[str, Any], *, supabase_client=None) -> dict[str, Any]:
    """Train and store one candidate artifact for a supported sport/market."""
    sport = str(run.get("sport", "")).lower()
    market = str(run.get("market", "")).lower()
    if sport != "football":
        raise RuntimeError(f"unsupported_auto_training_sport:{sport}")

    market_config = {
        "1x2": ("xgb_1x2", "result", 3),
        "btts": ("xgb_btts", "btts", 2),
        "over_25": ("xgb_over25", "over_25", 2),
    }.get(market)
    if market_config is None:
        raise RuntimeError(f"unsupported_auto_training_market:{sport}:{market}")

    from src.training import train as football_train

    data = football_train.load_data()
    if not data:
        raise RuntimeError("no_training_data_available")

    model_name, target_name, n_classes = market_config
    features, _imputer = football_train.prepare_features(data)
    target = football_train.prepare_target_classification(data, target_name)
    artifact = football_train.train_classifier(
        features,
        target,
        model_name,
        target_name,
        n_classes=n_classes,
    )
    if artifact is None:
        raise RuntimeError("candidate_training_returned_no_model")

    feature_names = list(artifact.get("feature_names") or [])
    model_version = build_model_version(model_name, feature_names)
    artifact_model_name = f"{model_name}__{model_version}"
    artifact_row = {**artifact, "model_name": artifact_model_name, "is_active": False}
    _client(supabase_client).table("ml_models").insert(artifact_row).execute()

    training_samples = int(artifact.get("training_samples") or 0)
    return {
        "model_name": model_name,
        "model_version": model_version,
        "model_type": artifact.get("model_type") or "xgboost",
        "artifact_ref": f"ml_models:{artifact_model_name}",
        "feature_names": feature_names,
        "training_samples": training_samples,
        "holdout_samples": 0,
        "metrics": {
            "training_samples": training_samples,
            "holdout_samples": 0,
            "accuracy": artifact.get("accuracy"),
            "brier": artifact.get("brier_score"),
            "log_loss": artifact.get("log_loss_val"),
            "f1_score": artifact.get("f1_score"),
        },
    }


def run_candidate_training(
    *,
    sport: str,
    market: str,
    trigger_reason: str,
    trainer: Callable[[dict[str, Any]], dict[str, Any]],
    supabase_client=None,
) -> dict[str, Any]:
    """Run one candidate training lifecycle and preserve failure state."""
    db = _client(supabase_client)
    run = start_training_run(
        supabase_client=db,
        sport=sport,
        market=market,
        trigger_reason=trigger_reason,
    )
    try:
        candidate = trainer(run)
        version = register_candidate_version(
            supabase_client=db,
            training_run_id=run["id"],
            model_name=candidate["model_name"],
            sport=sport,
            market=market,
            model_type=candidate["model_type"],
            artifact_ref=candidate["artifact_ref"],
            feature_names=candidate.get("feature_names") or [],
            metrics=candidate.get("metrics") or {},
        )
        mark_training_run_success(
            supabase_client=db,
            training_run_id=run["id"],
            training_samples=int(candidate.get("training_samples") or 0),
            holdout_samples=int(candidate.get("holdout_samples") or 0),
        )
        return {"status": "success", "run": run, "candidate": version}
    except Exception as exc:
        failed = mark_training_run_failed(
            supabase_client=db,
            training_run_id=run["id"],
            error_message=str(exc),
        )
        return {"status": "failed", "run": failed, "error_message": str(exc)}
