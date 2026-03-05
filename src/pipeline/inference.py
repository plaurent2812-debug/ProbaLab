import os
import pandas as pd
from src.models.meta_learner import XGBMetaLearner
from src.config import logger

# Singleton pour garder le modèle en RAM
_META_1X2_MODEL = None

def get_meta_1x2_model():
    global _META_1X2_MODEL
    if _META_1X2_MODEL is None:
        model_path = "models/football/meta_1x2_model.ubj"
        if not os.path.exists(model_path):
            return None
        
        try:
            # Note: We need to instantiate with default params just to hold the core model
            _META_1X2_MODEL = XGBMetaLearner()
            _META_1X2_MODEL.model.load_model(model_path)
            logger.info("✅ Meta-Modèle 1X2 chargé en mémoire avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du Meta-Modèle: {e}")
            return None
            
    return _META_1X2_MODEL

def predict_meta_1x2(stats_result: dict, ai_features: dict) -> dict | None:
    """
    Prend les prédictions de base (stats) et les features IA,
    et utilise le Meta-Modèle XGBoost pour prédire de nouvelles probabilités (Home, Draw, Away).
    """
    model = get_meta_1x2_model()
    if not model:
        return None
        
    # Construire le vecteur de features exactement comme dans l'entraînement
    try:
        row = {
            "proba_home": stats_result.get("proba_home", 0.33),
            "proba_draw": stats_result.get("proba_draw", 0.33),
            "proba_away": stats_result.get("proba_away", 0.33),
            "proba_btts": stats_result.get("proba_btts", 0.5),
            "proba_over_15": stats_result.get("proba_over_15", 0.5),
            "proba_over_25": stats_result.get("proba_over_25", 0.5),
            
            "ai_motivation": ai_features.get("motivation_score", 0.0),
            "ai_media_pressure": ai_features.get("media_pressure", 0.0),
            "ai_injury_impact": ai_features.get("injury_tactical_impact", 0.0),
            "ai_cohesion": ai_features.get("cohesion_score", 0.0),
            "ai_style_risk": ai_features.get("style_risk", 0.0),
        }
        
        df = pd.DataFrame([row])
        # Remplacer d'éventuels nans
        df.fillna(0, inplace=True)
        
        # Inférence
        preds = model.predict(df)
        
        # preds est de dimension (1, 3) où [0] = Away, [1] = Draw, [2] = Home
        # comme défini lors de 'target_1x2 = 2 if home > away else...'
        return {
            "proba_away_meta": round(float(preds[0][0]) * 100),
            "proba_draw_meta": round(float(preds[0][1]) * 100),
            "proba_home_meta": round(float(preds[0][2]) * 100)
        }
        
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'inférence Meta-Modèle: {e}")
        return None
