"""
Babas V1 - Time Engine.

Provee el contexto temporal estricto para todo el sistema, garantizando
que nunca haya confusión de zonas horarias.
"""

import logging
from datetime import datetime, date, timedelta
import pytz

logger = logging.getLogger(__name__)

# Zona horaria estricta del sistema
SYSTEM_TIMEZONE = pytz.timezone("America/La_Paz")


class TimeEngine:
    """Motor temporal centralizado."""

    @staticmethod
    def now() -> datetime:
        """Devuelve la fecha y hora actual en la zona horaria del sistema."""
        return datetime.now(SYSTEM_TIMEZONE)

    @staticmethod
    def today() -> date:
        """Devuelve la fecha de hoy en la zona horaria del sistema."""
        return TimeEngine.now().date()

    @staticmethod
    def get_context_string() -> str:
        """
        Devuelve un string legible con la hora y fecha para inyectar al prompt.
        """
        current = TimeEngine.now()
        # Nombres de días en español
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        dia_semana = dias[current.weekday()]
        mes = meses[current.month - 1]
        
        return f"Hoy es {dia_semana}, {current.day} de {mes} de {current.year}. La hora actual es {current.strftime('%H:%M')} (America/La_Paz)."
