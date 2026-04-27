from pathlib import Path

MIGRATION = Path(__file__).resolve().parents[1] / "migrations" / "060_mlops_model_registry.sql"


def _sql() -> str:
    assert MIGRATION.exists(), "060_mlops_model_registry.sql migration is required"
    return " ".join(MIGRATION.read_text(encoding="utf-8").lower().split())


def test_mlops_migration_creates_training_runs_registry():
    sql = _sql()

    assert "create table if not exists model_training_runs" in sql
    assert "status text not null check" in sql
    assert "'running','success','failed','rejected','promoted'" in sql
    assert "trigger_reason text not null check" in sql
    assert "'scheduled','drift','manual','new_data'" in sql
    assert "sport text not null check" in sql
    assert "'football','nhl'" in sql
    assert "create index if not exists idx_model_training_runs_sport_market" in sql


def test_mlops_migration_creates_versioned_model_registry():
    sql = _sql()

    assert "create table if not exists model_versions" in sql
    assert "model_version text not null" in sql
    assert "metrics jsonb not null default '{}'::jsonb" in sql
    assert "unique(model_name, model_version)" in sql
    assert "create unique index if not exists idx_model_versions_one_active" in sql
    assert "where is_active = true" in sql


def test_mlops_migration_creates_performance_snapshots():
    sql = _sql()

    assert "create table if not exists model_performance_snapshots" in sql
    assert "window_days integer not null check" in sql
    assert "window_days in (1,7,30,90)" in sql
    for metric in ("accuracy", "brier", "log_loss", "ece", "roi", "clv_mean", "fallback_rate"):
        assert f"{metric} numeric" in sql
    assert "create index if not exists idx_model_perf_snapshots_lookup" in sql


def test_mlops_migration_creates_promotion_decisions():
    sql = _sql()

    assert "create table if not exists model_promotion_decisions" in sql
    assert "decision text not null check" in sql
    assert "'promote','reject','manual_review'" in sql
    assert "candidate_metrics jsonb not null default '{}'::jsonb" in sql
    assert "active_metrics jsonb not null default '{}'::jsonb" in sql


def test_mlops_migration_enables_rls_service_role_only():
    sql = _sql()

    for table in (
        "model_training_runs",
        "model_versions",
        "model_performance_snapshots",
        "model_promotion_decisions",
    ):
        assert f"alter table {table} enable row level security" in sql
        assert f"on {table} for all" in sql

    assert "using (auth.role() = 'service_role')" in sql
    assert "with check (auth.role() = 'service_role')" in sql
