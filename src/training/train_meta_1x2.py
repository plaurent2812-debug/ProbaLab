import os
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, brier_score_loss, accuracy_score
from src.models.meta_learner import XGBMetaLearner
from src.config import logger

def train_meta_1x2(dataset_path: str = "meta_dataset.csv", model_dir: str = "models/football"):
    """
    Entraîne le Meta-Modèle XGBoost pour prédire le résultat 1X2 (0=Away, 1=Draw, 2=Home).
    Utilise une validation croisée temporelle (Time Series Split).
    """
    logger.info("🚀 Démarrage de l'entraînement du Meta-Modèle 1X2...")

    if not os.path.exists(dataset_path):
        logger.error(f"Fichier dataset introuvable: {dataset_path}")
        return

    df = pd.read_csv(dataset_path)
    if df.empty:
        logger.error("Dataset vide.")
        return

    # 1. Sélection des features et de la target
    feature_cols = [
        "proba_home", "proba_draw", "proba_away", 
        "proba_btts", "proba_over_15", "proba_over_25",
        "ai_motivation", "ai_media_pressure", "ai_injury_impact", "ai_cohesion", "ai_style_risk"
    ]
    target_col = "target_1x2"

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # On s'assure qu'il n'y a pas de NaNs dans les probas de base
    X.fillna(0, inplace=True)
    
    logger.info(f"Dataset chargé: {len(X)} échantillons, {len(feature_cols)} features.")

    # 2. Time Series Split pour évaluer sans fuite du futur vers le passé
    tscv = TimeSeriesSplit(n_splits=5)
    
    # Paramètres choisis pour un blending léger: max_depth faible, fort subsample, objective multi-class
    params = {
        'n_estimators': 150,
        'max_depth': 3,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'objective': 'multi:softprob', # Retourne une proba par classe
        'num_class': 3,
        'eval_metric': 'mlogloss',
        'random_state': 42
    }

    log_losses = []
    accuracies = []

    for fold, (train_index, test_index) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        model = XGBMetaLearner(params=params)
        model.fit(X_train, y_train)
        
        # Predict retourne des shape (n_samples, n_classes) avec objective multi:softprob
        y_pred_proba = model.predict(X_test)
        
        # OOF Log Loss
        loss = log_loss(y_test, y_pred_proba, labels=[0, 1, 2])
        log_losses.append(loss)
        
        # OOF Accuracy
        y_pred_class = np.argmax(y_pred_proba, axis=1)
        acc = accuracy_score(y_test, y_pred_class)
        accuracies.append(acc)

        logger.info(f"  Fold {fold+1}: Log Loss = {loss:.4f}, Accuracy = {acc:.4f}")

    logger.info("="*50)
    logger.info(f"🔹 Mean Log Loss: {np.mean(log_losses):.4f} (std: {np.std(log_losses):.4f})")
    logger.info(f"🔹 Mean Accuracy: {np.mean(accuracies):.4f} (std: {np.std(accuracies):.4f})")
    logger.info("="*50)

    # 3. Entraînement final sur TOUT le dataset
    logger.info("Entraînement final sur tout le dataset historique...")
    final_model = XGBMetaLearner(params=params)
    final_model.fit(X, y)

    # 4. Sauvegarde du modèle
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "meta_1x2_model.ubj")
    final_model.save_model(model_path)
    logger.info(f"✅ Meta-Modèle sauvegardé dans {model_path}")

if __name__ == "__main__":
    train_meta_1x2()
