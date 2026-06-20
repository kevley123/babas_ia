"""
Babas V1 - Todoist Connector.

Se encarga EXCLUSIVAMENTE de comunicarse con la API de Todoist.
No contiene lógica de razonamiento ni inteligencia.
"""

import logging
import httpx
from typing import Any

logger = logging.getLogger(__name__)

TODOIST_API_URL = "https://api.todoist.com/api/v1"


class TodoistConnector:
    """Cliente HTTP asíncrono para la API de Todoist."""

    def __init__(self, token: str):
        self._token = token
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

    async def get_active_tasks(self) -> list[dict[str, Any]]:
        """Obtiene todas las tareas activas."""
        if not self._token:
            logger.warning("TODOIST_API_TOKEN no está configurado.")
            return []
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{TODOIST_API_URL}/tasks",
                    headers=self._headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict) and "results" in data:
                    return data.get("results", [])
                elif isinstance(data, list):
                    return data
                return []
            except Exception as e:
                logger.error("Error obteniendo tareas de Todoist: %s", e)
                return []

    async def get_projects(self) -> list[dict]:
        """Obtiene todos los proyectos."""
        if not self._token: return []
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{TODOIST_API_URL}/projects", headers=self._headers, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and "results" in data: return data.get("results", [])
                elif isinstance(data, list): return data
                return []
            except Exception as e:
                logger.error("Error obteniendo proyectos de Todoist: %s", e)
                return []

    async def get_sections(self) -> list[dict]:
        """Obtiene todas las secciones."""
        if not self._token: return []
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{TODOIST_API_URL}/sections", headers=self._headers, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and "results" in data: return data.get("results", [])
                elif isinstance(data, list): return data
                return []
            except Exception as e:
                logger.error("Error obteniendo secciones de Todoist: %s", e)
                return []

    async def create_task(self, content: str, due_string: str | None = None, priority: int = 1, project_id: str | None = None, section_id: str | None = None, duration_minutes: int | None = None) -> dict[str, Any] | None:
        """
        Crea una nueva tarea.
        `due_string` puede ser lenguaje natural (ej. "tomorrow at 12:00").
        `priority` es de 1 (normal) a 4 (urgente).
        """
        if not self._token:
            logger.warning("TODOIST_API_TOKEN no está configurado.")
            return None

        payload = {"content": content, "priority": priority}
        if due_string: payload["due_string"] = due_string
        if project_id: payload["project_id"] = project_id
        if section_id: payload["section_id"] = section_id
        if duration_minutes: payload["duration"] = {"amount": duration_minutes, "unit": "minute"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{TODOIST_API_URL}/tasks",
                    json=payload,
                    headers=self._headers,
                    timeout=10.0
                )
                if response.status_code == 400 and "ITEM_DURATION_INVALID" in response.text:
                    logger.warning("Todoist rechazó la duración (cuenta gratuita). Reintentando sin duración.")
                    if "duration" in payload:
                        del payload["duration"]
                    payload["content"] = f"{payload['content']} [⏱ {duration_minutes}m]"
                    response = await client.post(
                        f"{TODOIST_API_URL}/tasks",
                        json=payload,
                        headers=self._headers,
                        timeout=10.0
                    )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Error creando tarea en Todoist: %s", e)
                return None
                
    async def update_task(self, task_id: str, content: str | None = None, due_string: str | None = None, priority: int | None = None, project_id: str | None = None, section_id: str | None = None, duration_minutes: int | None = None) -> bool:
        """Actualiza una tarea existente."""
        if not self._token:
            return False
            
        payload = {}
        if content is not None: payload["content"] = content
        if due_string is not None: payload["due_string"] = due_string
        if priority is not None: payload["priority"] = priority
        if project_id is not None: payload["project_id"] = project_id
        if section_id is not None: payload["section_id"] = section_id
        if duration_minutes is not None: payload["duration"] = {"amount": duration_minutes, "unit": "minute"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{TODOIST_API_URL}/tasks/{task_id}",
                    json=payload,
                    headers=self._headers,
                    timeout=10.0
                )
                if response.status_code == 400 and "ITEM_DURATION_INVALID" in response.text:
                    logger.warning("Todoist rechazó la duración (cuenta gratuita). Reintentando actualización sin duración.")
                    if "duration" in payload:
                        del payload["duration"]
                    if content is not None:
                        payload["content"] = f"{content} [⏱ {duration_minutes}m]"
                    else:
                        payload["content"] = f"Tarea [⏱ {duration_minutes}m]" # Fallback simple
                    response = await client.post(
                        f"{TODOIST_API_URL}/tasks/{task_id}",
                        json=payload,
                        headers=self._headers,
                        timeout=10.0
                    )
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error("Error actualizando tarea %s en Todoist: %s", task_id, e)
                return False

    async def close_task(self, task_id: str) -> bool:
        """Marca una tarea como completada."""
        if not self._token:
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{TODOIST_API_URL}/tasks/{task_id}/close",
                    headers=self._headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error("Error cerrando tarea %s en Todoist: %s", task_id, e)
                return False
