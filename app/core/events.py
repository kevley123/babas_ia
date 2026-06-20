"""
Babas V1 - Event Bus.

Implementa el patrón pub/sub para desacoplar los diferentes motores
(TaskEngine, TimeEngine, NotificationEngine, Brain).
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

# Tipado para callbacks de eventos (toman un payload dict y devuelven nada)
EventCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]

class EventBus:
    """Bus de eventos centralizado."""

    def __init__(self):
        # Mapea un nombre de evento a una lista de callbacks
        self._subscribers: dict[str, list[EventCallback]] = {}

    def subscribe(self, event_name: str, callback: EventCallback):
        """Registra un callback para escuchar un evento específico."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)
        logger.debug("Suscrito a evento: '%s'", event_name)

    async def emit(self, event_name: str, payload: dict[str, Any] | None = None):
        """Emite un evento de manera asíncrona a todos sus suscriptores."""
        payload = payload or {}
        logger.info("Emitiendo evento: '%s' | payload=%s", event_name, payload)
        
        if event_name not in self._subscribers:
            return

        # Lanzar todas las corrutinas suscritas concurrentemente pero sin bloquear al emisor
        callbacks = self._subscribers[event_name]
        tasks = [callback(payload) for callback in callbacks]
        
        # Ejecutar en segundo plano para no bloquear a quien emite el evento
        # Podría usarse asyncio.gather, pero create_task es mejor para 'fire-and-forget'
        for task in tasks:
            asyncio.create_task(self._safe_execute(event_name, task))

    async def _safe_execute(self, event_name: str, coro: Coroutine):
        """Ejecuta un callback capturando excepciones."""
        try:
            await coro
        except Exception as e:
            logger.error("Error procesando evento '%s': %s", event_name, e, exc_info=True)


# Instancia global del bus de eventos
event_bus = EventBus()

# Constantes de Eventos
EVENT_SYSTEM_STARTUP = "SYSTEM_STARTUP"
EVENT_SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
EVENT_DAILY_REPORT_TRIGGER = "DAILY_REPORT_TRIGGER"
EVENT_TELEGRAM_MESSAGE = "TELEGRAM_MESSAGE"
EVENT_TELEGRAM_MESSAGE_SEND = "TELEGRAM_MESSAGE_SEND"
