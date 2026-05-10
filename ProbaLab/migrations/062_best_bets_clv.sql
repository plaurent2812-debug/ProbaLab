-- 062_best_bets_clv.sql
-- Master plan Phase 4.2 : Closing Line Value (CLV) tracking per recommended pick.
--
-- For each pick that we surface to users, we want to know AFTER the match:
--   - what was the bookmaker's CLOSING odds (more reflective of true probability)
--   - did we beat that closing line?
--
-- The closing line snapshot already exists in `closing_odds` (migration 051);
-- this migration just adds the per-pick columns needed to display CLV in the
-- public track record and admin dashboard without recomputing on every read.

alter table best_bets
  add column if not exists opening_odds       numeric(5,2),
  add column if not exists closing_odds_value numeric(5,2),
  add column if not exists clv_pct            numeric(6,2),
  add column if not exists bookmaker_source   text,
  add column if not exists clv_recorded_at    timestamptz;

-- CLV display index — admin track-record queries scan by date desc.
create index if not exists idx_best_bets_clv_recorded_at
  on best_bets(clv_recorded_at desc) where clv_recorded_at is not null;
