"""
Jarvis V1 - Configuración centralizada del sistema.

Usa Pydantic Settings para cargar variables de entorno desde .env
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Raíz del proyecto (donde está .env)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Configuración global de Jarvis V1."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── DeepSeek API ──────────────────────────────────────────────
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"

    # ── Embeddings ────────────────────────────────────────────────
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # ── Database Paths ────────────────────────────────────────────
    database_path: str = "data/profile/jarvis.db"
    chroma_episodic_path: str = "data/episodic"
    chroma_knowledge_path: str = "data/knowledge/vectors"
    skills_path: str = "data/skills"
    knowledge_docs_path: str = "data/knowledge/documents"

    # ── Logging ───────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "logs/jarvis.log"

    # ── Server ────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Brain Settings ────────────────────────────────────────────
    max_session_history: int = 10
    context_max_memories: int = 5
    context_max_documents: int = 3

    # ── Integrations ──────────────────────────────────────────────
    todoist_api_token: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # ── Helpers ───────────────────────────────────────────────────

    def resolve_path(self, relative_path: str) -> Path:
        """Resuelve una ruta relativa al proyecto."""
        path = PROJECT_ROOT / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def db_path(self) -> Path:
        return self.resolve_path(self.database_path)

    @property
    def episodic_path(self) -> Path:
        return self.resolve_path(self.chroma_episodic_path)

    @property
    def knowledge_vector_path(self) -> Path:
        return self.resolve_path(self.chroma_knowledge_path)

    @property
    def skills_dir(self) -> Path:
        path = PROJECT_ROOT / self.skills_path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def knowledge_docs_dir(self) -> Path:
        path = PROJECT_ROOT / self.knowledge_docs_path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        return self.resolve_path(self.log_file)
