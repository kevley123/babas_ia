#!/usr/bin/env python3
"""
Jarvis V1 - Script de arranque.

Uso: python run.py
"""

import uvicorn

from app.config import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
