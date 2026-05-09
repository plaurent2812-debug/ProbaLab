-- 061_provider_health_log.sql
-- Master plan Phase 2.1 : provider health logging.
-- Tracks every fetch attempt to API-Football, The Odds API, NHL API, etc.
-- so the admin /api/admin/data-health endpoint can surface failures BEFORE
-- the UI is empty.

create table if not exists provider_health_log (
    id bigserial primary key,
    recorded_at timestamptz not null default now(),
    provider text not null,                  -- e.g. 'api_football', 'the_odds_api', 'nhl_api'
    sport text,                              -- 'football' | 'nhl' | null when N/A
    endpoint text not null,                  -- request path (sanitized, no secret)
    status_code integer,                     -- HTTP status; null on transport error
    row_count integer,                       -- normalized payload row count when available
    latency_ms integer,                      -- end-to-end latency
    quota_remaining integer,                 -- when the provider exposes it
    plan_label text,                         -- 'the_odds_api_30_usd' | 'api_football_pro' | …
    error text,                              -- short error code/message; null on success
    is_success boolean not null default true -- explicit so HTTP 200 with empty payload can be flagged
);

create index if not exists idx_provider_health_log_recorded_at
    on provider_health_log(recorded_at desc);
create index if not exists idx_provider_health_log_provider_date
    on provider_health_log(provider, recorded_at desc);
create index if not exists idx_provider_health_log_failures
    on provider_health_log(recorded_at desc) where is_success = false;

-- RLS : seul le service_role peut écrire/lire (lecture admin via API).
alter table provider_health_log enable row level security;

create policy "service_role_all_provider_health_log"
    on provider_health_log for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');
