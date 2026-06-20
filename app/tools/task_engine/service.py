"""
Babas V1 - Task Engine.

Maneja la lógica de tareas, abstrayendo las APIs externas (Todoist).
Solo retorna la información útil para el cerebro, evitando ruido.
"""

import logging
from app.tools.task_engine.todoist_conn import TodoistConnector
from app.tools.time_engine.service import TimeEngine

logger = logging.getLogger(__name__)


class TaskEngine:
    """Motor inteligente de gestión de tareas."""

    def __init__(self, todoist_token: str):
        self._conn = TodoistConnector(todoist_token)
        self._sections_cache = {}
        self._projects_cache = {}
        self._cache_loaded = False
        logger.info("TaskEngine inicializado")

    async def _ensure_cache(self):
        if not self._cache_loaded:
            projects = await self._conn.get_projects()
            sections = await self._conn.get_sections()
            self._projects_cache = {p.get("name", "").lower(): p["id"] for p in projects if "id" in p}
            self._sections_cache = {s.get("name", "").lower(): s["id"] for s in sections if "id" in s}
            self._cache_loaded = True

    async def get_summary(self, filter_type: str = "all", section_name: str | None = None) -> str:
        """
        Devuelve un resumen en texto de las tareas activas para inyectar al LLM.
        """
        await self._ensure_cache()
        tasks = await self._conn.get_active_tasks()
        if not tasks:
            return "No tienes tareas pendientes en Todoist."

        target_section_id = self._sections_cache.get(section_name.lower()) if section_name else None
        
        today_str = TimeEngine.now().strftime("%Y-%m-%d")
        
        filtered_tasks = []
        for t in tasks:
            due = t.get("due") or {}
            date_str = due.get("date", "")
            is_recurring = due.get("is_recurring", False)
            
            is_overdue = False
            is_today = False
            
            if due and date_str:
                # Todoist devuelve fechas como YYYY-MM-DD o con tiempo. Comparamos los primeros 10 chars
                date_only = date_str[:10]
                if date_only < today_str:
                    is_overdue = True
                if date_only == today_str:
                    is_today = True

            # Filtrar según filter_type
            if filter_type == "overdue":
                # Si piden vencidas, enviamos las de días anteriores Y las de hoy (por si vencieron por hora)
                if not (is_overdue or is_today):
                    continue
            elif filter_type == "today" and not is_today:
                continue
            if filter_type == "unscheduled" and due:
                continue
                
            # Filtrar por sección si se pidió
            if target_section_id and t.get("section_id") != target_section_id:
                continue
                
            filtered_tasks.append((t, is_overdue, due))

        if not filtered_tasks:
            msg = f"No tienes tareas que coincidan con el filtro '{filter_type}'"
            if section_name: msg += f" en la sección '{section_name}'."
            else: msg += "."
            return msg

        # Filtrar y formatear para no enviar el JSON crudo masivo al LLM
        lines = [f"Tus tareas pendientes (filtro: {filter_type}" + (f", sección: {section_name}):" if section_name else "):")]
        for t, is_overdue, due in filtered_tasks:
            content = t.get("content", "Sin título")
            if t.get("parent_id"):
                content = f"↳ [Subtarea] {content}"
            due_string = due.get("string", "Sin fecha") if due else "Sin fecha"
            
            prio = t.get("priority", 1)
            urgency = "🔥 URGENTE" if prio == 4 else "ALTA" if prio == 3 else "Normal"

            status = "[VENCIDA] " if is_overdue else ""
            lines.append(f"- ID: {t['id']} | {status}{content} | Para: {due_string} | Prioridad: {urgency}")

        return "\n".join(lines)

    async def create_task(self, content: str, due_string: str | None = None, priority: int = 1, section_name: str | None = None, duration_minutes: int | None = None) -> str:
        """Crea una tarea y retorna un string de confirmación para el LLM."""
        await self._ensure_cache()
        section_id = self._sections_cache.get(section_name.lower()) if section_name else None
        
        task = await self._conn.create_task(content, due_string, priority, section_id=section_id, duration_minutes=duration_minutes)
        if task:
            return f"Tarea '{content}' creada exitosamente con ID {task['id']}."
        return f"Error: No se pudo crear la tarea '{content}'."
        
    async def update_task(self, task_id: str, content: str | None = None, due_string: str | None = None, priority: int | None = None, section_name: str | None = None, duration_minutes: int | None = None) -> str:
        """Actualiza una tarea y retorna un string de confirmación para el LLM."""
        await self._ensure_cache()
        section_id = self._sections_cache.get(section_name.lower()) if section_name else None
        
        success = await self._conn.update_task(task_id, content, due_string, priority, section_id=section_id, duration_minutes=duration_minutes)
        if success:
            return f"Tarea {task_id} actualizada exitosamente."
        return f"Error: No se pudo actualizar la tarea {task_id}."
        
    async def complete_task(self, task_id: str) -> str:
        """Marca una tarea como completada."""
        success = await self._conn.close_task(task_id)
        if success:
            return f"Tarea {task_id} marcada como completada."
        return f"Error: No se pudo completar la tarea {task_id}."
