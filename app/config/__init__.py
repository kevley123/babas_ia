"""
Jarvis V1 - Config package.

Expone get_settings() como singleton para inyección de dependencias.
"""

from functools import lru_cache

from app.config.settings import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna una instancia singleton de Settings."""
    return Settings()
