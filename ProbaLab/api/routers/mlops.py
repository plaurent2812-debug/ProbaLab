from typing import Any, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, ConfigDict, Field

from api.auth import verify_internal_auth
from src.config import supabase
from src.mlops.performance_tracker import persist_daily_performance_snapshots
from src.mlops.promotion import apply_promotion_decision, decide_promotion
from src.mlops.retrain_policy import should_retrain
from src.mlops.training_orchestrator import run_candidate_training, train_candidate_for_run

router = APIRouter(prefix="/api", tags=["MLOps"])


class AutoTrainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sport: Literal["football", "nhl"]
    market: str = Field(min_length=1)
    trigger_reason: Literal["scheduled", "drift", "manual", "new_data"] = "scheduled"
    new_results_count: int = Field(default=0, ge=0)
    brier_7d: float | None = None
    brier_30d: float | None = None
    clv_7d: float | None = None
    ece_30d: float | None = None
    data_completeness_pct: float = Field(default=1.0, ge=0.0, le=1.0)
    hours_since_last_training: float | None = Field(default=None, ge=0.0)


def _require_internal(authorization: str | None = Header(default=None)) -> None:
    verify_internal_auth(authorization=authorization)


def _latest(table: str, order_col: str = "recorded_at", limit: int = 20) -> list[dict[str, Any]]:
    try:
        return (
            supabase.table(table)
            .select("*")
            .order(order_col, desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def _latest_active_model_version(model_name: str) -> dict[str, Any] | None:
    rows = (
        supabase.table("model_versions")
        .select("*")
        .eq("model_name", model_name)
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    return rows[0] if rows else None


@router.post("/trigger/mlops/evaluate")
def trigger_mlops_evaluate(authorization: str | None = Header(default=None)):
    """Persist daily model-performance snapshots."""
    _require_internal(authorization)
    snapshots = persist_daily_performance_snapshots()
    return {"status": "ok", "snapshots": snapshots}


@router.post("/trigger/mlops/auto-train")
def trigger_mlops_auto_train(
    body: AutoTrainRequest,
    authorization: str | None = Header(default=None),
):
    """Run one controlled candidate-training cycle when policy allows it."""
    _require_internal(authorization)
    decision = should_retrain(body.model_dump())
    if not decision["should_retrain"]:
        return {"status": "skipped", "decision": decision}

    training = run_candidate_training(
        sport=body.sport,
        market=body.market,
        trigger_reason=body.trigger_reason,
        trainer=train_candidate_for_run,
    )
    if training["status"] != "success":
        return {"status": "training_failed", "decision": decision, "training": training}

    candidate = training["candidate"]
    active = _latest_active_model_version(candidate["model_name"])
    promotion = decide_promotion(candidate, active)
    applied = apply_promotion_decision(
        candidate=candidate,
        active=active,
        promotion=promotion,
        can_auto_promote=decision["can_auto_promote"],
    )
    return {
        "status": "completed",
        "decision": decision,
        "training": training,
        "promotion": applied["decision"],
    }


@router.get("/admin/mlops/health")
def admin_mlops_health(authorization: str | None = Header(default=None)):
    """Read the latest MLOps health slices for the admin dashboard."""
    _require_internal(authorization)
    return {
        "runs": _latest("model_training_runs", "started_at"),
        "models": _latest("model_versions", "created_at"),
        "performance": _latest("model_performance_snapshots", "recorded_at"),
        "decisions": _latest("model_promotion_decisions", "decided_at"),
    }
