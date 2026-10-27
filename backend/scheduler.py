"""Runs the escrow agent on a schedule so expiring authorizations get
reauthorized or voided even when nobody is actively using the app."""

from apscheduler.schedulers.background import BackgroundScheduler

from agents.escrow import run_escrow_checks

_scheduler = None


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(run_escrow_checks, "interval", hours=6, id="escrow_checks")
    _scheduler.start()
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
