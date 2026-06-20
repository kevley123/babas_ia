"""
Babas V1 - Scheduler Engine.

Reloj interno que dispara eventos programados usando APScheduler.
"""

import logging
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.core.events import event_bus, EVENT_DAILY_REPORT_TRIGGER
from app.tools.time_engine.service import SYSTEM_TIMEZONE

logger = logging.getLogger(__name__)

DB_PATH = "sqlite:///data/scheduler.sqlite"

async def execute_scheduled_action(action_type: str, payload: dict):
    """Manejador genérico de alarmas asíncronas."""
    logger.info("Ejecutando acción programada: %s", action_type)
    if action_type == "telegram":
        from app.core.events import EVENT_TELEGRAM_MESSAGE_SEND
        await event_bus.emit(EVENT_TELEGRAM_MESSAGE_SEND, {"message": payload.get("message", "Recordatorio automático")})

async def trigger_daily_report():
    """Callback del cron que emite el evento de reporte diario."""
    logger.info("CronJob Triggered: DAILY_REPORT")
    await event_bus.emit(EVENT_DAILY_REPORT_TRIGGER, payload={"reason": "cron"})

class SchedulerEngine:
    """Motor de automatizaciones temporales."""

    def __init__(self):
        jobstores = {
            'default': SQLAlchemyJobStore(url=DB_PATH)
        }
        self._scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=SYSTEM_TIMEZONE)

    def start(self):
        """Inicia el scheduler y programa los trabajos."""
        if self._scheduler.running:
            return

        os.makedirs("data", exist_ok=True)
        self._setup_jobs()
        self._scheduler.start()
        logger.info("SchedulerEngine iniciado (Timezone: %s) con persistencia SQLite", SYSTEM_TIMEZONE.zone)

    def stop(self):
        """Detiene el scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("SchedulerEngine detenido")

    def schedule_action(self, run_date: datetime, action_type: str, payload: dict):
        """Programa una acción para ejecutarse en el futuro."""
        job_id = f"action_{action_type}_{run_date.timestamp()}"
        self._scheduler.add_job(
            execute_scheduled_action,
            DateTrigger(run_date=run_date, timezone=SYSTEM_TIMEZONE),
            args=[action_type, payload],
            id=job_id,
            replace_existing=True,
            name=f"Scheduled {action_type}"
        )
        logger.info("Programada acción %s para %s", action_type, run_date)

    def _setup_jobs(self):
        """Configura todos los cron jobs del sistema."""
        # 1. Reporte Diario (Ej: Lunes a Viernes a las 08:00 AM)
        self._scheduler.add_job(
            trigger_daily_report,
            CronTrigger(day_of_week="mon-fri", hour=8, minute=0, timezone=SYSTEM_TIMEZONE),
            id="daily_report_job",
            replace_existing=True,
            name="Disparador de Reporte Diario Matutino"
        )
        logger.debug("Trabajos programados configurados.")

