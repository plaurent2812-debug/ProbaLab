import pandas as pd
from src.config import supabase, logger

def extract_meta_dataset() -> pd.DataFrame:
    """
    Extrait l'historique des prédictions (modèles de base + features IA)
    et les joint aux résultats réels (fixtures) pour l'entraînement du XGBoost.
    Utilise la jointure native Supabase et pd.json_normalize pour aplatir les objets JSON.
    """
    logger.info("📦 Extraction du dataset Meta-Modèle depuis Supabase...")

    # Fetch predictions avec pagination
    predictions = []
    page_size = 1000
    offset = 0
    
    while True:
        res = (supabase.table("predictions")
               .select("fixture_id, proba_home, proba_draw, proba_away, proba_btts, proba_over_15, proba_over_25, "
                       "ai_features, fixtures!inner(home_goals, away_goals, status)")
               .in_("fixtures.status", ["FT", "AET", "PEN"])
               .range(offset, offset + page_size - 1)
               .execute())
        
        data = res.data or []
        predictions.extend(data)
        if len(data) < page_size:
            break
        offset += page_size
        logger.info(f"  ... fetched {len(predictions)} joined predictions so far")
    
    if not predictions:
        logger.warning("Aucune prédiction terminée trouvée.")
        return pd.DataFrame()

    # Aplatit automatiquement le JSON ai_features et les nested fixtures
    df = pd.json_normalize(predictions)
    
    # Transformation de la cible multi-classe (Label) : 2 = Home, 1 = Draw, 0 = Away
    df['target_1x2'] = df.apply(lambda x: 2 if x['fixtures.home_goals'] > x['fixtures.away_goals'] 
                           else (1 if x['fixtures.home_goals'] == x['fixtures.away_goals'] else 0), axis=1)

    # Transformation des cibles binaires
    df['target_btts'] = ((df['fixtures.home_goals'] > 0) & (df['fixtures.away_goals'] > 0)).astype(int)
    df['target_over_15'] = ((df['fixtures.home_goals'] + df['fixtures.away_goals']) > 1).astype(int)
    df['target_over_25'] = ((df['fixtures.home_goals'] + df['fixtures.away_goals']) > 2).astype(int)

    # Renommage des colonnes issues de json_normalize pour correspondre 
    # au script d'entraînement train_meta_1x2.py
    rename_map = {
        'ai_features.motivation_score': 'ai_motivation',
        'ai_features.media_pressure': 'ai_media_pressure',
        'ai_features.injury_tactical_impact': 'ai_injury_impact',
        'ai_features.cohesion_score': 'ai_cohesion',
        'ai_features.style_risk': 'ai_style_risk',
        'fixtures.home_goals': 'home_goals',
        'fixtures.away_goals': 'away_goals',
    }
    
    # S'assurer que les features IA existent même si le JSONB était vide
    for old_col, new_col in rename_map.items():
        if old_col not in df.columns:
            df[old_col] = 0.0

    df = df.rename(columns=rename_map)
    
    # Remplacer les valeurs manquantes par 0 (par sécurité pour XGBoost)
    df.fillna(0, inplace=True)

    logger.info(f"✅ Dataset extrait: {len(df)} lignes, {len(df.columns)} colonnes.")
    return df

if __name__ == "__main__":
    df = extract_meta_dataset()
    if not df.empty:
        # Sauvegarde temporaire CSV pour inspection et entraînement
        df.to_csv("meta_dataset.csv", index=False)
        logger.info("Dataset sauvegardé sous meta_dataset.csv pour inspection.")
        print(df[['fixture_id', 'target_1x2', 'target_btts', 'proba_home', 'ai_motivation']].head())
