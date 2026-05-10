-- 063_predictions_proba_precision.sql
-- Master plan : précision des probabilités ML.
-- Avant : proba_home, proba_draw, proba_away, proba_btts, proba_over_15,
-- proba_over_2_5, proba_over_35 stockées en entier (round(p * 100)).
-- Après : numeric(7,4) qui peut représenter 0.0000..100.0000 avec 4
-- décimales — assez fin pour Brier/ECE/CLV sans perdre l'échelle 0..100
-- déjà comprise par les 328 consumers du repo.
--
-- Idempotent : USING ... ::numeric tolère un type source entier OU
-- numeric ; ne perd jamais d'information dans le sens int → numeric.
--
-- À appliquer manuellement via Supabase Studio (le MCP n'a pas accès
-- à ce projet). Voir docs/runbooks/prod-readiness.md.

do $$
declare
  col text;
  cols text[] := array[
    'proba_home',
    'proba_draw',
    'proba_away',
    'proba_btts',
    'proba_over_15',
    'proba_over_2_5',
    'proba_over_35'
  ];
begin
  foreach col in array cols loop
    -- alter_column is a no-op if the column is already numeric(7,4).
    execute format(
      'alter table predictions alter column %I type numeric(7,4) using %I::numeric',
      col, col
    );
  end loop;
end$$;
