-- 060_mlops_model_registry.sql
-- Registry for controlled auto-training, model versioning, performance snapshots,
-- promotion decisions, and rollback-ready model operations.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- 1. model_training_runs
-- ---------------------------------------------------------------------------

create table if not exists model_training_runs (
    id uuid primary key default gen_random_uuid(),
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    status text not null check (status in ('running','success','failed','rejected','promoted')),
    trigger_reason text not null check (trigger_reason in ('scheduled','drift','manual','new_data')),
    sport text not null check (sport in ('football','nhl')),
    market text not null,
    train_from timestamptz,
    train_until timestamptz,
    holdout_from timestamptz,
    holdout_until timestamptz,
    training_samples integer not null default 0,
    holdout_samples integer not null default 0,
    error_message text,
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists idx_model_training_runs_started_at
    on model_training_runs(started_at desc);

create index if not exists idx_model_training_runs_sport_market
    on model_training_runs(sport, market, started_at desc);

-- ---------------------------------------------------------------------------
-- 2. model_versions
-- ---------------------------------------------------------------------------

create table if not exists model_versions (
    id uuid primary key default gen_random_uuid(),
    training_run_id uuid references model_training_runs(id) on delete set null,
    model_name text not null,
    model_version text not null,
    sport text not null check (sport in ('football','nhl')),
    market text not null,
    model_type text not null,
    artifact_table text not null default 'ml_models',
    artifact_ref text not null,
    feature_names text[] not null default '{}',
    feature_hash text,
    train_window jsonb not null default '{}'::jsonb,
    metrics jsonb not null default '{}'::jsonb,
    is_active boolean not null default false,
    promoted_at timestamptz,
    created_at timestamptz not null default now(),
    unique(model_name, model_version)
);

create unique index if not exists idx_model_versions_one_active
    on model_versions(model_name)
    where is_active = true;

create index if not exists idx_model_versions_sport_market
    on model_versions(sport, market, created_at desc);

-- ---------------------------------------------------------------------------
-- 3. model_performance_snapshots
-- ---------------------------------------------------------------------------

create table if not exists model_performance_snapshots (
    id bigserial primary key,
    recorded_at timestamptz not null default now(),
    sport text not null check (sport in ('football','nhl')),
    market text not null,
    model_name text not null,
    model_version text,
    window_days integer not null check (window_days in (1,7,30,90)),
    sample_size integer not null default 0,
    accuracy numeric,
    brier numeric,
    log_loss numeric,
    ece numeric,
    roi numeric,
    clv_mean numeric,
    clv_positive_pct numeric,
    fallback_rate numeric,
    data_completeness_pct numeric,
    metrics jsonb not null default '{}'::jsonb
);

create index if not exists idx_model_perf_snapshots_lookup
    on model_performance_snapshots(sport, market, model_name, window_days, recorded_at desc);

-- ---------------------------------------------------------------------------
-- 4. model_promotion_decisions
-- ---------------------------------------------------------------------------

create table if not exists model_promotion_decisions (
    id bigserial primary key,
    decided_at timestamptz not null default now(),
    training_run_id uuid references model_training_runs(id) on delete set null,
    model_name text not null,
    candidate_version text not null,
    active_version text,
    decision text not null check (decision in ('promote','reject','manual_review')),
    reason text not null,
    candidate_metrics jsonb not null default '{}'::jsonb,
    active_metrics jsonb not null default '{}'::jsonb,
    thresholds jsonb not null default '{}'::jsonb,
    decided_by text not null default 'system'
);

create index if not exists idx_model_promotion_decisions_model
    on model_promotion_decisions(model_name, decided_at desc);

-- ---------------------------------------------------------------------------
-- 5. RLS: backend service role only
-- ---------------------------------------------------------------------------

alter table model_training_runs enable row level security;
alter table model_versions enable row level security;
alter table model_performance_snapshots enable row level security;
alter table model_promotion_decisions enable row level security;

create policy "service_role_all_model_training_runs"
    on model_training_runs for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

create policy "service_role_all_model_versions"
    on model_versions for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

create policy "service_role_all_model_performance_snapshots"
    on model_performance_snapshots for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

create policy "service_role_all_model_promotion_decisions"
    on model_promotion_decisions for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');
