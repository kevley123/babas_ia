"""
Babas V1 - Notification Dispatcher.

Escucha eventos del EventBus (ej. reportes diarios, alarmas) y los procesa,
generalmente enviando mensajes vía Telegram o activando al Cerebro.
"""

import logging
import httpx
from typing import Any

from app.core.events import event_bus, EVENT_DAILY_REPORT_TRIGGER, EVENT_TELEGRAM_MESSAGE_SEND
from app.tools.notification_engine.telegram_bot import TelegramEngine

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """Orquesta las notificaciones salientes del sistema."""

    def __init__(self, telegram_engine: TelegramEngine):
        self._telegram = telegram_engine
        
        # Suscribir a eventos
        event_bus.subscribe(EVENT_DAILY_REPORT_TRIGGER, self._on_daily_report)
        event_bus.subscribe(EVENT_TELEGRAM_MESSAGE_SEND, self._on_telegram_send)
        logger.info("NotificationDispatcher inicializado")

    async def _on_telegram_send(self, payload: dict[str, Any]):
        """Manejador para el evento que pide explícitamente enviar un mensaje por Telegram."""
        message = payload.get("message")
        if message:
            await self._telegram.send_message(message)

    async def _on_daily_report(self, payload: dict[str, Any]):
        """Manejador para el evento de reporte diario disparado por el cron."""
        logger.info("Procesando evento DAILY_REPORT_TRIGGER")
        
        # Avisar al usuario que se está generando
        await self._telegram.send_message("☀️ ¡Buenos días! Dame un segundo, estoy recopilando tu reporte de hoy...")
        
        # Aquí, el Dispatcher le "habla" al propio Brain como si fuera el usuario,
        # pero con un prompt especial oculto.
        try:
            async with httpx.AsyncClient() as client:
                prompt_interno = "Genera un resumen diario de mis tareas. Revisa mis tareas de hoy y dame los buenos días."
                resp = await client.post(
                    "http://localhost:8000/chat",
                    json={"message": prompt_interno},
                    timeout=60.0
                )
                resp.raise_for_status()
                data = resp.json()
                
                report = data.get("message", "Tu reporte diario está listo, pero hubo un error formateándolo.")
                await self._telegram.send_message(report)
                
        except Exception as e:
            logger.error("Error generando reporte diario: %s", e)
            await self._telegram.send_message("Hubo un error intentando generar tu reporte diario.")
