"""
Babas V1 - Music Tool (Backend).

Maneja el almacenamiento de playlists recibidas por URL.
Nota: La reproducción real la hace el frontend.
"""

import json
import logging
from pathlib import Path
import httpx
import re

logger = logging.getLogger(__name__)


class MusicTool:
    """Herramienta de backend para persistir y buscar playlists."""

    def __init__(self, data_dir: str = "data/music"):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._playlists_file = self._data_dir / "playlists.json"
        
        # Inicializar archivo si no existe
        if not self._playlists_file.exists():
            with open(self._playlists_file, "w", encoding="utf-8") as f:
                json.dump({}, f)
                
        logger.info("MusicTool inicializado. Playlists: %s", self._playlists_file)

    async def add_playlist_from_url(self, url: str, name: str | None = None) -> dict:
        """
        Agrega una playlist desde una URL.
        Intenta deducir el nombre si no se provee.
        """
        # Intentar obtener el título de la página si no hay nombre
        if not name:
            name = await self._fetch_title(url)
            if not name:
                # Fallback, usar un ID corto
                match = re.search(r'list=([a-zA-Z0-9_-]+)', url)
                name = match.group(1) if match else "Playlist_Desconocida"

        # Limpiar sufijos típicos
        name = name.replace(" - YouTube", "").replace(" - YouTube Music", "").strip()

        # Cargar, guardar, escribir
        with open(self._playlists_file, "r", encoding="utf-8") as f:
            playlists = json.load(f)

        playlists[name] = url

        with open(self._playlists_file, "w", encoding="utf-8") as f:
            json.dump(playlists, f, indent=2, ensure_ascii=False)

        logger.info("Playlist guardada: '%s' -> %s", name, url)
        return {"status": "success", "message": f"Playlist '{name}' guardada correctamente.", "name": name, "url": url}

    def get_playlists(self, query: str | None = None) -> list[dict]:
        """Devuelve las playlists guardadas, opcionalmente filtradas."""
        with open(self._playlists_file, "r", encoding="utf-8") as f:
            playlists = json.load(f)
            
        results = []
        for name, url in playlists.items():
            if query and query.lower() not in name.lower():
                continue
            results.append({"name": name, "url": url})
            
        return results
        
    def find_playlist_url(self, name: str) -> str | None:
        """Busca la URL exacta de una playlist por nombre (match parcial)."""
        playlists = self.get_playlists(name)
        if playlists:
            return playlists[0]["url"]
        return None

    async def _fetch_title(self, url: str) -> str | None:
        """Extrae el título de la página web (YouTube)."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # YouTube Music a veces requiere un User-Agent
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    match = re.search(r'<title>(.*?)</title>', resp.text, re.IGNORECASE)
                    if match:
                        return match.group(1)
        except Exception as e:
            logger.warning("Error extrayendo título de %s: %s", url, e)
        return None
