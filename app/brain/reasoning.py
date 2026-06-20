"""
Babas V1 - Motor de Razonamiento.

Orquesta el flujo completo de procesamiento de un mensaje:
    1. Construir contexto personalizado
    2. Armar prompt con historial de sesión
    3. Consultar al LLM (ahora requiriendo JSON estricto)
    4. Extraer memorias del mensaje (async)
    5. Formatear respuesta
    6. Interceptar herramientas de backend (MusicTool)
"""

import asyncio
import logging
import json
from collections import deque

from app.brain.context_builder import ContextBuilder
from app.brain.memory_extractor import MemoryExtractor
from app.brain.response_formatter import ResponseFormatter
from app.brain.prompts import SYSTEM_PROMPT, RESPONSE_FORMAT_HINT
from app.schemas.chat import ChatResponse
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """Motor de razonamiento central de Babas."""

    def __init__(
        self,
        llm_service: LLMService,
        context_builder: ContextBuilder,
        memory_extractor: MemoryExtractor,
        max_session_history: int = 10,
    ):
        self._llm = llm_service
        self._context_builder = context_builder
        self._memory_extractor = memory_extractor
        self._max_history = max_session_history

        # Historial de sesión (en memoria, no persistido)
        self._session_history: deque[dict] = deque(maxlen=max_session_history * 2)

        logger.info(
            "ReasoningEngine inicializado (historial max: %d mensajes)",
            max_session_history,
        )

    async def process_message(self, user_message: str) -> ChatResponse:
        """
        Procesa un mensaje del usuario a través del pipeline completo.
        """
        logger.info("Procesando mensaje: '%s'", user_message[:100])

        try:
            # ── Paso 1: Construir contexto ────────────────────────
            context, memory_types_used = await self._context_builder.build_context(
                user_message
            )

            # ── Paso 2: Armar mensajes para el LLM ───────────────
            messages = self._build_messages(user_message, context)

            # ── Paso 3: Consultar LLM y extraer memorias en paralelo ──
            llm_task = asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._llm.chat_json(messages=messages, max_tokens=2500),
            )
            memory_task = self._memory_extractor.extract_and_store(user_message)

            llm_response_dict, memories_created = await asyncio.gather(
                llm_task, memory_task
            )

            # ── Paso 4: Actualizar historial de sesión ────────────
            self._session_history.append({"role": "user", "content": user_message})
            # Convertimos el dict de vuelta a string para el historial
            self._session_history.append({"role": "assistant", "content": json.dumps(llm_response_dict)})

            # ── Paso 5: Formatear respuesta ───────────────────────
            response = ResponseFormatter.format(
                llm_response=llm_response_dict,
                memory_types_used=memory_types_used,
                memories_created=memories_created,
            )

            # ── Paso 6: Interceptar herramientas del backend ────────
            needs_re_eval = False
            
            if response.type == "tool_call":
                if response.tool.name == "music":
                    await self._handle_music_tool(response)
                elif response.tool.name == "tasks":
                    needs_re_eval = await self._handle_tasks_tool(response)
                elif response.tool.name == "telegram":
                    await self._handle_telegram_tool(response)
                elif response.tool.name == "system":
                    await self._handle_system_tool(response)
                    
            # Si la herramienta devolvió información que el LLM necesita leer (ej. GET_ACTIVE_TASKS)
            if needs_re_eval:
                logger.info("Re-evaluando con resultado de herramienta...")
                tool_result = response.tool.params.get("_internal_result", "")
                # Añadir el resultado al historial como system
                self._session_history.append({"role": "system", "content": f"Resultado de la herramienta {response.tool.intent}:\n{tool_result}\nGenera tu respuesta final para el usuario basada en esto."})
                
                # Volver a armar mensajes y consultar al LLM
                messages = self._build_messages(user_message, context)
                llm_task2 = asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._llm.chat_json(messages=messages, max_tokens=2500),
                )
                llm_response_dict = await llm_task2
                self._session_history.append({"role": "assistant", "content": json.dumps(llm_response_dict)})
                
                response = ResponseFormatter.format(
                    llm_response=llm_response_dict,
                    memory_types_used=memory_types_used,
                    memories_created=memories_created,
                )

            logger.info(
                "Respuesta generada: type=%s, tool=%s:%s, confidence=%.2f",
                response.type,
                response.tool.name,
                response.tool.intent,
                response.confidence,
            )

            return response

        except Exception as e:
            logger.error("Error procesando mensaje: %s", e, exc_info=True)
            return ResponseFormatter.format_error(str(e))

    async def _handle_tasks_tool(self, response: ChatResponse) -> bool:
        """
        Intercepta comandos de tareas. 
        Retorna True si el LLM necesita re-evaluar la respuesta con los datos obtenidos.
        """
        from app.config import get_settings
        from app.tools.task_engine.service import TaskEngine
        
        settings = get_settings()
        engine = TaskEngine(settings.todoist_api_token)
        
        intent = response.tool.intent
        params = response.tool.params
        needs_re_eval = False
        
        if intent == "GET_ACTIVE_TASKS":
            filter_type = params.get("filter", "all")
            section_name = params.get("section_name")
            summary = await engine.get_summary(filter_type, section_name)
            response.tool.params["_internal_result"] = summary
            needs_re_eval = True
            
        elif intent == "CREATE_TASKS":
            tasks = params.get("tasks", [])
            count = 0
            for t in tasks:
                if t.get("content"):
                    await engine.create_task(
                        t.get("content"),
                        t.get("due_string"),
                        t.get("priority", 1),
                        t.get("section_name"),
                        t.get("duration_minutes")
                    )
                    count += 1
            response.message = f"Intenté crear {count} tareas."
                
        elif intent == "UPDATE_TASKS":
            updates = params.get("updates", [])
            count = 0
            for u in updates:
                if u.get("task_id"):
                    await engine.update_task(
                        u.get("task_id"),
                        u.get("content"),
                        u.get("due_string"),
                        u.get("priority"),
                        u.get("section_name"),
                        u.get("duration_minutes")
                    )
                    count += 1
            response.message = f"Actualizadas {count} tareas en lote."
                
        elif intent == "COMPLETE_TASKS":
            task_ids = params.get("task_ids", [])
            for tid in task_ids:
                await engine.complete_task(tid)
            response.message = f"{len(task_ids)} tareas marcadas como completadas."
                
        return needs_re_eval

    async def _handle_telegram_tool(self, response: ChatResponse):
        """Intercepta envíos explícitos a Telegram."""
        from app.core.events import event_bus, EVENT_TELEGRAM_MESSAGE_SEND
        intent = response.tool.intent
        params = response.tool.params
        
        if intent == "SEND_TELEGRAM_MESSAGE":
            msg = params.get("message")
            if msg:
                # Dispara el evento asíncrono para que el Dispatcher envíe el mensaje
                await event_bus.emit(EVENT_TELEGRAM_MESSAGE_SEND, {"message": msg})
                response.message = "Mensaje enviado por Telegram exitosamente."

    async def _handle_system_tool(self, response: ChatResponse):
        """Intercepta comandos de sistema (como tareas programadas)."""
        intent = response.tool.intent
        params = response.tool.params
        
        if intent == "SCHEDULE_ACTION":
            time_str = params.get("time")
            action_type = params.get("action_type")
            payload = params.get("payload", {})
            if time_str and action_type:
                try:
                    from app.tools.time_engine.service import SYSTEM_TIMEZONE
                    from datetime import datetime
                    run_date = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    run_date = SYSTEM_TIMEZONE.localize(run_date)
                    
                    from app.api.dependencies import get_scheduler_engine
                    scheduler = get_scheduler_engine()
                    scheduler.schedule_action(run_date, action_type, payload)
                    response.message = f"Acción '{action_type}' programada exitosamente para {time_str}."
                except Exception as e:
                    logger.error("Error programando accion: %s", e)
                    response.message = "No pude programar la acción: formato de tiempo inválido o error interno."

    async def _handle_music_tool(self, response: ChatResponse):
        """Intercepta comandos de música que requieren acceso a la DB del servidor."""
        from app.tools.music_tool import MusicTool
        music_db = MusicTool()
        
        intent = response.tool.intent
        params = response.tool.params
        
        if intent == "ADD_PLAYLIST_FROM_URL":
            url = params.get("url")
            name = params.get("name") # El LLM podría deducirlo
            if url:
                result = await music_db.add_playlist_from_url(url, name)
                # Opcional: Actualizar el mensaje con la confirmación real
                response.message = result["message"]
                
        elif intent in ["PLAY_PLAYLIST", "GET_PLAYLISTS"]:
            # Buscar el nombre en la base de datos de playlists
            name = params.get("name", "")
            if name:
                url = music_db.find_playlist_url(name)
                if url:
                    # Inyectamos el URL para que el Frontend sepa qué reproducir
                    response.tool.params["url"] = url
                else:
                    response.message = f"Lo siento, no encontré la playlist '{name}' guardada."
                    response.type = "answer" # Abortar reproducción de herramienta
                    response.tool.intent = "NONE"

    def _build_messages(self, user_message: str, context: str) -> list[dict]:
        """
        Construye la lista de mensajes para enviar al LLM.
        """
        from app.tools.time_engine.service import TimeEngine
        time_context = TimeEngine.get_context_string()
        
        messages = []
        system_content = f"{SYSTEM_PROMPT}\n\n[TIEMPO ACTUAL DEL SISTEMA]\n{time_context}\n\n{context}\n\n{RESPONSE_FORMAT_HINT}"
        messages.append({"role": "system", "content": system_content})

        for msg in self._session_history:
            messages.append(msg)

        # Evitar duplicar el mensaje del usuario en las re-evaluaciones
        already_has_user_msg = False
        for msg in reversed(self._session_history):
            if msg["role"] == "user":
                if msg.get("content") == user_message:
                    already_has_user_msg = True
                break
                
        if not already_has_user_msg:
            messages.append({"role": "user", "content": user_message})

        return messages

    def clear_session(self) -> None:
        """Limpia el historial de sesión."""
        self._session_history.clear()
        logger.info("Historial de sesión limpiado")

    @property
    def session_length(self) -> int:
        return len(self._session_history)
