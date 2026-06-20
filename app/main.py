"""
Babas V1 - Punto de entrada principal de la aplicación FastAPI.

Configura CORS, logging, lifespan (inicialización de DB/ChromaDB, Scheduler),
e incluye todos los routers de la API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.config.logging import setup_logging
from app.api.error_handlers import register_error_handlers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización y limpieza del ciclo de vida de la app."""
    settings = get_settings()

    # Configurar logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_path,
    )

    logger.info("=" * 60)
    logger.info("Babas V1 iniciando...")
    logger.info("Modelo LLM: %s", settings.deepseek_model)
    logger.info("Modelo Embeddings: %s", settings.embedding_model)
    logger.info("=" * 60)

    # Iniciar Motor de Eventos y Scheduler
    from app.core.events import event_bus, EVENT_SYSTEM_STARTUP, EVENT_SYSTEM_SHUTDOWN
    from app.api.dependencies import get_scheduler_engine
    
    app.state.scheduler = get_scheduler_engine()
    app.state.scheduler.start()
    
    # Iniciar Motor de Notificaciones (Telegram)
    from app.tools.notification_engine.telegram_bot import TelegramEngine
    from app.tools.notification_engine.dispatcher import NotificationDispatcher
    
    app.state.telegram = TelegramEngine(settings.telegram_bot_token, settings.telegram_chat_id)
    app.state.dispatcher = NotificationDispatcher(app.state.telegram)
    await app.state.telegram.start()
    
    await event_bus.emit(EVENT_SYSTEM_STARTUP)

    # Inicializar memoria de perfil (SQLite)
    from app.api.dependencies import get_profile_memory
    profile_memory = get_profile_memory()
    await profile_memory.init_db()
    logger.info("Memoria de perfil (SQLite) inicializada")

    # Pre-cargar servicios para que estén listos
    from app.api.dependencies import get_episodic_memory, get_knowledge_base
    get_episodic_memory()
    logger.info("Memoria episódica (ChromaDB) inicializada")
    get_knowledge_base()
    logger.info("Base de conocimiento inicializada")

    logger.info("Babas V1 listo y operativo 🧠")

    yield

    # Limpieza
    await event_bus.emit(EVENT_SYSTEM_SHUTDOWN)
    app.state.scheduler.stop()
    if hasattr(app.state, "telegram"):
        await app.state.telegram.stop()
    logger.info("Babas V1 apagándose...")


def create_app() -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
    app = FastAPI(
        title="Babas V1",
        description="Sistema Operativo Personal Inteligente - Cerebro V1",
        version="1.0.0",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Para la tablet local
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Error handlers ────────────────────────────────────────────
    register_error_handlers(app)

    # ── Routers ───────────────────────────────────────────────────
    from app.api.health import router as health_router
    from app.api.chat import router as chat_router
    from app.api.profile import router as profile_router
    from app.api.memory import router as memory_router
    from app.api.knowledge import router as knowledge_router

    app.include_router(health_router, tags=["Health"])
    app.include_router(chat_router, prefix="/chat", tags=["Chat"])
    app.include_router(profile_router, prefix="/profile", tags=["Profile"])
    app.include_router(memory_router, prefix="/memory", tags=["Memory"])
    app.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])

    return app


app = create_app()
