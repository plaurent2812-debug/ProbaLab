"""
worker.py — Cron worker pour Railway (service séparé du web).

Tâches planifiées :
  - Toutes les 5 min  : live scores + events (football + NHL)
  - Toutes les 15 min : màj résultats FT
  - Toutes les heures : fetch nouveaux fixtures
  - Tous les jours 6h : pipeline IA complet (brain)

Usage :
  python worker.py
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("worker")


def job_live() -> None:
    """Toutes les 5 min — scores + events live football + NHL."""
    try:
        from src.fetchers.live import run
        run()
    except Exception:
        logger.exception("[job_live] Error")


def job_results() -> None:
    """Toutes les 15 min — mise à jour scores FT."""
    try:
        from src.fetchers.results import fetch_and_update_results
        fetch_and_update_results()
    except Exception:
        logger.exception("[job_results] Error")


def job_matches() -> None:
    """Toutes les heures — fetch nouveaux fixtures."""
    try:
        from src.fetchers.matches import fetch_and_store
        fetch_and_store()
    except Exception:
        logger.exception("[job_matches] Error")


def job_brain() -> None:
    """Tous les jours à 6h — pipeline IA complet."""
    try:
        from src.brain import run_brain
        run_brain()
    except Exception:
        logger.exception("[job_brain] Error")


def job_nhl_evaluation() -> None:
    """Tous les jours à 8h — scores NHL + évaluation complète."""
    try:
        from src.fetchers.fetch_nhl_results import evaluate_nhl_predictions
        evaluate_nhl_predictions(days_back=3)
    except Exception:
        logger.exception("[job_nhl_eval] Error")


def job_football_evaluation() -> None:
    """Tous les jours à 8h30 — évaluation foot + recalibration + draw factor audit."""
    try:
        from src.models.calibrate import recalibrate_draw_factors, run_calibration
        from src.training.evaluate import run_evaluation
        run_evaluation()
        run_calibration()
        recalibrate_draw_factors(months=6)
    except Exception:
        logger.exception("[job_football_eval] Error")


def job_drift_check() -> None:
    """Tous les jours à 9h00 — detection drift Brier 7j vs 30j."""
    try:
        from src.monitoring.drift_detector import check_drift
        result = check_drift()
        if result.get("drifted"):
            logger.warning(
                "[job_drift_check] Drift detecte — Brier 7j=%s, 30j=%s, delta=%s",
                result["brier_7d"], result["brier_30d"], result["delta"],
            )
        else:
            logger.info(
                "[job_drift_check] Pas de drift — Brier 7j=%s, 30j=%s",
                result["brier_7d"], result["brier_30d"],
            )
    except Exception:
        logger.exception("[job_drift_check] Error")


def job_football_picks() -> None:
    """Tous les jours à 14h — génération pronos football (singles + double + fun)."""
    try:
        from src.ticket_generator import generate_football_picks
        result = generate_football_picks()
        logger.info(
            "[job_football_picks] %s: %d singles, %d double, %d fun",
            result["date"], result["singles"], result["double"], result["fun"],
        )
    except Exception:
        logger.exception("[job_football_picks] Error")


def job_nhl_picks() -> None:
    """Tous les jours à 22h — génération pronos NHL (singles + double + fun)."""
    try:
        from src.ticket_generator import generate_nhl_picks
        result = generate_nhl_picks()
        logger.info(
            "[job_nhl_picks] %s: %d singles, %d double, %d fun",
            result["date"], result["singles"], result["double"], result["fun"],
        )
    except Exception:
        logger.exception("[job_nhl_picks] Error")


def job_weekly_retrain() -> None:
    """Chaque dimanche à 3h00 — retraining complet des modeles ML."""
    try:
        from src.training.build_data import run as build_data_run
        from src.training.evaluate import run_evaluation
        from src.training.train import run as train_run

        logger.info("[job_weekly_retrain] Etape 1/3 — rebuild features...")
        build_data_run(rebuild=False)

        logger.info("[job_weekly_retrain] Etape 2/3 — entrainement des modeles...")
        train_run()

        logger.info("[job_weekly_retrain] Etape 3/3 — evaluation post-entrainement...")
        run_evaluation()

        logger.info("[job_weekly_retrain] Retraining hebdomadaire termine.")
    except Exception:
        logger.exception("[job_weekly_retrain] Error")


def main() -> None:
    scheduler = BlockingScheduler(timezone="Europe/Paris")

    # Toutes les 5 min
    scheduler.add_job(job_live, CronTrigger(minute="*/5"), id="live", max_instances=1, coalesce=True)

    # Toutes les 15 min
    scheduler.add_job(job_results, CronTrigger(minute="*/15"), id="results", max_instances=1, coalesce=True)

    # Toutes les heures (à la minute 30)
    scheduler.add_job(job_matches, CronTrigger(minute=30), id="matches", max_instances=1, coalesce=True)

    # Tous les jours à 6h00
    scheduler.add_job(job_brain, CronTrigger(hour=6, minute=0), id="brain", max_instances=1, coalesce=True)

    # Tous les jours à 8h00 — évaluation NHL (après matchs de nuit US)
    scheduler.add_job(job_nhl_evaluation, CronTrigger(hour=8, minute=0), id="nhl_eval", max_instances=1, coalesce=True)

    # Tous les jours à 8h30 — évaluation foot + recalibration
    scheduler.add_job(job_football_evaluation, CronTrigger(hour=8, minute=30), id="football_eval", max_instances=1, coalesce=True)

    # Tous les jours à 9h00 — drift detection Brier 7j vs 30j
    scheduler.add_job(job_drift_check, CronTrigger(hour=9, minute=0), id="drift_check", max_instances=1, coalesce=True)

    # Tous les jours à 14h00 — pronos football quotidiens
    scheduler.add_job(job_football_picks, CronTrigger(hour=14, minute=0), id="football_picks", max_instances=1, coalesce=True)

    # Tous les jours à 22h00 — pronos NHL quotidiens
    scheduler.add_job(job_nhl_picks, CronTrigger(hour=22, minute=0), id="nhl_picks", max_instances=1, coalesce=True)

    # Chaque dimanche à 3h00 — retraining hebdomadaire complet
    scheduler.add_job(job_weekly_retrain, CronTrigger(day_of_week="sun", hour=3, minute=0), id="weekly_retrain", max_instances=1, coalesce=True)

    logger.info("=" * 50)
    logger.info("  ⚙️  Worker démarré")
    logger.info("  - Live scores    : */5 min")
    logger.info("  - Résultats FT   : */15 min")
    logger.info("  - Fixtures       : toutes les heures")
    logger.info("  - Pipeline brain : 6h00 quotidien")
    logger.info("  - NHL évaluation : 8h00 quotidien")
    logger.info("  - Foot éval+calib: 8h30 quotidien")
    logger.info("  - Drift check    : 9h00 quotidien")
    logger.info("  - Picks football : 14h00 quotidien")
    logger.info("  - Picks NHL      : 22h00 quotidien")
    logger.info("  - ML retrain     : dimanche 3h00")
    logger.info("=" * 50)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker arrêté.")


if __name__ == "__main__":
    main()
