-- ============================================================
-- Migration 020: Enable RLS on ALL public tables
-- ============================================================
-- Context: Backend migrated from anon key to service_role key.
-- service_role bypasses RLS, so backend is unaffected.
-- Frontend uses anon key and needs explicit SELECT policies
-- on the 4 tables it accesses directly.
-- ============================================================

-- ── 1. Enable RLS on every public table ─────────────────────

ALTER TABLE IF EXISTS profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS fixtures ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS prediction_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS best_bets ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS expert_picks ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS ticket_picks ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS players ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS football_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leagues ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS injuries ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS match_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS match_lineups ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS match_team_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS fixture_odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS market_odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS player_season_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS team_elo ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS team_standings ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS h2h_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS referees ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS calibration ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS training_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS ml_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS ai_learnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS football_meta_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS football_momentum_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS live_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS live_match_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS live_match_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS processed_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS push_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nhl_fixtures ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nhl_data_lake ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nhl_odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nhl_suivi_algo_clean ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nhl_player_game_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nhl_daily_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nhl_daily_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS nhl_ml_training_data ENABLE ROW LEVEL SECURITY;

-- ── 2. Frontend policies (anon key access) ──────────────────

-- profiles: authenticated users can read ONLY their own profile
CREATE POLICY "users_read_own_profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

-- fixtures: public read-only (needed for live_alerts join)
CREATE POLICY "public_read_fixtures"
  ON fixtures FOR SELECT
  TO anon, authenticated
  USING (true);

-- nhl_fixtures: public read-only (NHL pages + homepage counter)
CREATE POLICY "public_read_nhl_fixtures"
  ON nhl_fixtures FOR SELECT
  TO anon, authenticated
  USING (true);

-- live_alerts: public read-only (homepage live alert banner)
CREATE POLICY "public_read_live_alerts"
  ON live_alerts FOR SELECT
  TO anon, authenticated
  USING (true);
