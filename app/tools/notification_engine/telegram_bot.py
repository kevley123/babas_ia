"""
Babas V1 - Telegram Bot (Notification Engine).

Actúa como una extremidad de Babas. Se conecta a Telegram de forma
asíncrona. Cuando recibe un mensaje, hace POST al endpoint /chat.
También expone métodos para que Babas envíe notificaciones proactivas.
"""

import logging
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from app.config import get_settings

logger = logging.getLogger(__name__)


class TelegramEngine:
    """Motor de notificaciones vía Telegram."""

    def __init__(self, token: str, allowed_chat_id: str):
        self._token = token
        self._chat_id = allowed_chat_id
        self._app = None
        self._is_running = False

    async def start(self):
        """Inicia el bot en el event loop actual."""
        if not self._token or not self._chat_id:
            logger.warning("Faltan credenciales de Telegram. Bot desactivado.")
            return

        self._app = Application.builder().token(self._token).build()
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

        logger.info("Iniciando Telegram Bot...")
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()
        self._is_running = True
        
        # Enviar un mensaje de bienvenida/despertar
        await self.send_message("Hola, soy Babas 🥺, soy asistente de Rodrigo, qué te ayudo?")
    async def stop(self):
        """Detiene el bot limpiamente."""
        if self._is_running and self._app:
            logger.info("Deteniendo Telegram Bot...")
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
            self._is_running = False

    async def send_message(self, text: str):
        """Envía un mensaje proactivo al chat autorizado."""
        if not self._is_running or not self._app:
            return
            
        try:
            await self._app.bot.send_message(chat_id=self._chat_id, text=text)
            logger.info("Mensaje enviado por Telegram: %s", text[:50])
        except Exception as e:
            logger.error("Error enviando mensaje por Telegram: %s", e)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes entrantes."""
        if not update.message or not update.message.text:
            return

        # Solo responder al usuario autorizado
        if str(update.message.chat_id) != self._chat_id:
            logger.warning("Acceso denegado de chat_id: %s", update.message.chat_id)
            return

        user_text = update.message.text
        logger.info("Recibido por Telegram: '%s'", user_text)

        # Mostrar estado de "escribiendo" (aislado para evitar que un timeout bloquee el flujo)
        try:
            await update.message.chat.send_action("typing")
        except Exception as e:
            logger.warning("No se pudo enviar estado 'typing' a Telegram: %s", e)

        # Llamar a la API del Cerebro (de manera local)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://localhost:8000/chat",
                    json={"message": user_text},
                    timeout=60.0
                )
                resp.raise_for_status()
                data = resp.json()
                
                # Enviar respuesta del cerebro al usuario
                bot_reply = data.get("message", "Error de comunicación con el cerebro.")
                await update.message.reply_text(bot_reply)
                
                # Si el cerebro ejecutó un ToolCall en el proceso, opcionalmente podríamos notificarlo
                # pero el cerebro debería haber puesto confirmación en 'message'.
                
        except Exception as e:
            logger.error("Error contactando a Babas API: %s", e)
            await update.message.reply_text("Ups, el cerebro de Babas está desconectado o tuvo un error.")
