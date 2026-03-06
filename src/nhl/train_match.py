"""
train_match.py — Entraînement XGBoost match-level pour la NHL.

Construit un dataset à partir des matchs terminés dans nhl_fixtures,
entraîne 2 modèles (Win Prediction + Over 5.5), et sauvegarde dans models/nhl/.
"""

from __future__ import annotations

import json
import os
import pickle
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit
    from xgboost import XGBClassifier
except ImportError:
    print("Install: pip install xgboost scikit-learn pandas")
    sys.exit(1)

# ── Ajouter racine au path ──
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import logger, supabase

# ═══════════════════════════════════════════════════════════════
#  FEATURES pour le modèle match-level
# ═══════════════════════════════════════════════════════════════

MATCH_FEATURES = [
    "proba_home",          # Proba heuristique Poisson: home win %
    "proba_away",          # Proba heuristique Poisson: away win %
    "proba_over_55",       # Proba heuristique Poisson: Over 5.5 %
    "ai_home_factor",      # Facteur IA Gemini pour home
    "ai_away_factor",      # Facteur IA Gemini pour away
]

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "nhl"


def build_match_dataset() -> pd.DataFrame:
    """Construit le dataset d'entraînement depuis Supabase."""
    logger.info("📊 Construction du dataset NHL match-level...")

    res = (
        supabase.table("nhl_fixtures")
        .select("id, date, home_team, away_team, home_score, away_score, "
                "proba_home, proba_away, proba_over_55, "
                "predictions_json, ai_home_factor, ai_away_factor, status")
        .in_("status", ["Final", "FINAL", "FT", "OFF"])
        .order("date")
        .execute()
    )

    fixtures = res.data or []
    logger.info(f"  {len(fixtures)} matchs terminés trouvés.")

    rows = []
    for fix in fixtures:
        home_score = fix.get("home_score")
        away_score = fix.get("away_score")
        if home_score is None or away_score is None:
            continue

        # Get probas from top-level columns OR predictions_json fallback
        proba_home = fix.get("proba_home")
        proba_away = fix.get("proba_away")
        proba_over_55 = fix.get("proba_over_55")
        ai_home = fix.get("ai_home_factor")
        ai_away = fix.get("ai_away_factor")

        # Fallback to predictions_json
        pj = fix.get("predictions_json")
        if isinstance(pj, str):
            try:
                pj = json.loads(pj) if pj and pj != "{}" else {}
            except Exception:
                pj = {}

        if proba_home is None and pj:
            proba_home = pj.get("proba_home")
        if proba_away is None and pj:
            proba_away = pj.get("proba_away")
        if proba_over_55 is None and pj:
            proba_over_55 = pj.get("proba_over_55")
        if ai_home is None and pj:
            ai_home = pj.get("ai_home_factor")
        if ai_away is None and pj:
            ai_away = pj.get("ai_away_factor")

        # Skip if we don't have enough features
        if proba_home is None or proba_away is None:
            continue

        total_goals = int(home_score) + int(away_score)
        home_win = 1 if int(home_score) > int(away_score) else 0

        rows.append({
            "date": fix.get("date", ""),
            "home_team": fix.get("home_team", ""),
            "away_team": fix.get("away_team", ""),
            # Features
            "proba_home": float(proba_home),
            "proba_away": float(proba_away),
            "proba_over_55": float(proba_over_55 or 50),
            "ai_home_factor": float(ai_home or 1.0),
            "ai_away_factor": float(ai_away or 1.0),
            # Labels
            "label_home_win": home_win,
            "label_over_55": 1 if total_goals > 5 else 0,
            # Metadata
            "total_goals": total_goals,
        })

    df = pd.DataFrame(rows)
    logger.info(f"  ✅ Dataset: {len(df)} échantillons")
    if not df.empty:
        logger.info(f"     Home wins: {df['label_home_win'].sum()}/{len(df)} "
                     f"({df['label_home_win'].mean():.1%})")
        logger.info(f"     Over 5.5: {df['label_over_55'].sum()}/{len(df)} "
                     f"({df['label_over_55'].mean():.1%})")
    return df


def train_model(df: pd.DataFrame, target: str, model_name: str) -> dict | None:
    """Entraîne un modèle XGBoost pour un target donné."""
    logger.info(f"\n--- Entraînement: {model_name} (target={target}) ---")

    if df.empty or target not in df.columns:
        logger.error(f"❌ Dataset vide ou target {target} manquant")
        return None

    # Clean
    df_clean = df.replace([np.inf, -np.inf], np.nan).fillna(0)

    X = df_clean[MATCH_FEATURES]
    y = df_clean[target]

    positives = int(y.sum())
    if positives == 0 or positives == len(y):
        logger.error("❌ Pas de variance dans la cible")
        return None

    # Time Series Split (chronological)
    n_splits = min(5, len(df) // 10)
    if n_splits < 2:
        logger.warning("⚠️ Trop peu de données pour cross-validation, entraînement direct")
        n_splits = 2

    tscv = TimeSeriesSplit(n_splits=n_splits)

    scale_pos_weight = (len(y) - positives) / max(1, positives)

    params = {
        "n_estimators": 100,
        "max_depth": 3,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "scale_pos_weight": scale_pos_weight,
        "eval_metric": "logloss",
        "random_state": 42,
    }

    briers, accs, aucs = [], [], []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = XGBClassifier(**params)
        model.fit(X_train, y_train, verbose=False)

        preds = model.predict_proba(X_test)[:, 1]
        briers.append(brier_score_loss(y_test, preds))
        accs.append(accuracy_score(y_test, (preds >= 0.5).astype(int)))
        try:
            aucs.append(roc_auc_score(y_test, preds))
        except Exception:
            aucs.append(0.5)

        logger.info(f"  Fold {fold + 1}: Brier={briers[-1]:.4f} Acc={accs[-1]:.1%} AUC={aucs[-1]:.3f}")

    logger.info(f"  📊 Mean Brier: {np.mean(briers):.4f} | Mean Acc: {np.mean(accs):.1%} | Mean AUC: {np.mean(aucs):.3f}")

    # Final training on all data
    final_model = XGBClassifier(**params)
    final_model.fit(X, y, verbose=False)

    # Save
    os.makedirs(MODEL_DIR, exist_ok=True)
    output_path = MODEL_DIR / f"nhl_match_{model_name}.pkl"

    metadata = {
        "model": final_model,
        "feature_names": MATCH_FEATURES,
        "metrics": {
            "brier_score": float(np.mean(briers)),
            "accuracy": float(np.mean(accs)),
            "roc_auc": float(np.mean(aucs)),
            "n_samples": len(df),
        },
        "training_date": datetime.now().isoformat(),
    }

    with open(output_path, "wb") as f:
        pickle.dump(metadata, f)

    logger.info(f"  💾 Modèle sauvegardé: {output_path}")
    return metadata["metrics"]


def train_nhl_match_models() -> dict:
    """Point d'entrée principal: construit le dataset et entraîne les 2 modèles."""
    logger.info("🏒🧠 NHL Match-Level ML Training")
    logger.info("=" * 50)

    df = build_match_dataset()
    if df.empty or len(df) < 20:
        msg = f"Pas assez de données ({len(df)} matchs). Minimum: 20."
        logger.warning(f"⚠️ {msg}")
        return {"success": False, "message": msg, "n_samples": len(df)}

    results = {}

    # 1. Win Prediction
    win_metrics = train_model(df, "label_home_win", "win")
    if win_metrics:
        results["win"] = win_metrics

    # 2. Over 5.5
    over_metrics = train_model(df, "label_over_55", "over55")
    if over_metrics:
        results["over55"] = over_metrics

    logger.info("\n" + "=" * 50)
    logger.info("🎯 Récapitulatif NHL ML:")
    for name, m in results.items():
        logger.info(f"  {name}: Acc={m['accuracy']:.1%} | Brier={m['brier_score']:.4f} | AUC={m['roc_auc']:.3f}")

    return {
        "success": True,
        "models_trained": list(results.keys()),
        "metrics": results,
        "n_samples": len(df),
    }


if __name__ == "__main__":
    train_nhl_match_models()
