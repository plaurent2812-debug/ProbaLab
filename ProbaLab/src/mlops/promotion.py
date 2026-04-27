from datetime import datetime, timezone
from typing import Any

PROMOTION_THRESHOLDS = {
    "football:1x2": {
        "min_holdout_samples": 300,
        "max_brier_regression": 0.002,
        "max_log_loss_regression": 0.005,
        "max_ece": 0.08,
        "min_clv_delta": -0.005,
    },
    "nhl:moneyline": {
        "min_holdout_samples": 150,
        "max_brier_regression": 0.003,
        "max_log_loss_regression": 0.007,
        "max_ece": 0.10,
        "min_clv_delta": -0.007,
    },
}

DEFAULT_THRESHOLDS = PROMOTION_THRESHOLDS["football:1x2"]


def _thresholds(candidate: dict[str, Any]) -> dict[str, float]:
    sport = str(candidate.get("sport", "football")).lower()
    market = str(candidate.get("market", "1x2")).lower()
    return PROMOTION_THRESHOLDS.get(f"{sport}:{market}", DEFAULT_THRESHOLDS)


def _metric(model: dict[str, Any] | None, key: str) -> float | None:
    if not model:
        return None
    value = (model.get("metrics") or {}).get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _version(model: dict[str, Any] | None) -> str | None:
    if not model:
        return None
    version = model.get("model_version")
    return str(version) if version is not None else None


def decide_promotion(candidate: dict[str, Any], active: dict[str, Any] | None) -> dict[str, Any]:
    """Decide whether a candidate model can replace the active model."""
    thresholds = _thresholds(candidate)
    candidate_version = _version(candidate)
    active_version = _version(active)

    holdout_samples = _metric(candidate, "holdout_samples") or 0
    if holdout_samples < thresholds["min_holdout_samples"]:
        return {
            "decision": "manual_review",
            "reason": "insufficient_holdout_samples",
            "candidate_version": candidate_version,
            "active_version": active_version,
            "thresholds": thresholds,
        }

    candidate_ece = _metric(candidate, "ece")
    if candidate_ece is not None and candidate_ece > thresholds["max_ece"]:
        return {
            "decision": "reject",
            "reason": "ece_degraded",
            "candidate_version": candidate_version,
            "active_version": active_version,
            "thresholds": thresholds,
        }

    if active is not None:
        candidate_brier = _metric(candidate, "brier")
        active_brier = _metric(active, "brier")
        if (
            candidate_brier is not None
            and active_brier is not None
            and candidate_brier > active_brier + thresholds["max_brier_regression"]
        ):
            return {
                "decision": "reject",
                "reason": "brier_regression",
                "candidate_version": candidate_version,
                "active_version": active_version,
                "thresholds": thresholds,
            }

        candidate_log_loss = _metric(candidate, "log_loss")
        active_log_loss = _metric(active, "log_loss")
        if (
            candidate_log_loss is not None
            and active_log_loss is not None
            and candidate_log_loss > active_log_loss + thresholds["max_log_loss_regression"]
        ):
            return {
                "decision": "reject",
                "reason": "log_loss_regression",
                "candidate_version": candidate_version,
                "active_version": active_version,
                "thresholds": thresholds,
            }

        candidate_clv = _metric(candidate, "clv_mean")
        active_clv = _metric(active, "clv_mean")
        if (
            candidate_clv is not None
            and active_clv is not None
            and candidate_clv - active_clv < thresholds["min_clv_delta"]
        ):
            return {
                "decision": "reject",
                "reason": "clv_regression",
                "candidate_version": candidate_version,
                "active_version": active_version,
                "thresholds": thresholds,
            }

    return {
        "decision": "promote",
        "reason": "quality_gate_passed",
        "candidate_version": candidate_version,
        "active_version": active_version,
        "thresholds": thresholds,
    }


def _client(supabase_client=None):
    if supabase_client is not None:
        return supabase_client
    from src.config import supabase

    return supabase


def _decision_payload(
    *,
    candidate: dict[str, Any],
    active: dict[str, Any] | None,
    promotion: dict[str, Any],
    decided_by: str,
) -> dict[str, Any]:
    return {
        "training_run_id": candidate.get("training_run_id"),
        "model_name": candidate["model_name"],
        "candidate_version": candidate["model_version"],
        "active_version": _version(active),
        "decision": promotion["decision"],
        "reason": promotion["reason"],
        "candidate_metrics": candidate.get("metrics") or {},
        "active_metrics": (active or {}).get("metrics") or {},
        "thresholds": promotion.get("thresholds") or {},
        "decided_by": decided_by,
    }


def apply_promotion_decision(
    *,
    candidate: dict[str, Any],
    active: dict[str, Any] | None,
    promotion: dict[str, Any],
    can_auto_promote: bool,
    supabase_client=None,
    decided_by: str = "system",
) -> dict[str, Any]:
    """Persist a promotion decision and activate only when policy permits it."""
    client = _client(supabase_client)
    decision = dict(promotion)

    if decision["decision"] == "promote" and not can_auto_promote:
        decision["decision"] = "manual_review"
        decision["reason"] = "manual_candidate_requires_review"

    payload = _decision_payload(
        candidate=candidate,
        active=active,
        promotion=decision,
        decided_by=decided_by,
    )
    client.table("model_promotion_decisions").insert(payload).execute()

    if decision["decision"] != "promote":
        return {"status": "recorded", "decision": decision}

    now_iso = datetime.now(timezone.utc).isoformat()
    (
        client.table("model_versions")
        .update({"is_active": False})
        .eq("model_name", candidate["model_name"])
        .eq("is_active", True)
        .execute()
    )

    activation_query = client.table("model_versions").update(
        {"is_active": True, "promoted_at": now_iso}
    )
    if candidate.get("id"):
        activation_query = activation_query.eq("id", candidate["id"])
    else:
        activation_query = activation_query.eq("model_name", candidate["model_name"]).eq(
            "model_version",
            candidate["model_version"],
        )
    activation_query.execute()

    return {"status": "applied", "decision": decision}
