"""
Jarvis V1 - Memoria Procedimental (Skills en YAML).

Almacena procedimientos (cómo hacer algo) como archivos YAML en disco.
No almacena información, almacena instrucciones paso a paso.

Ejemplo de skill (crear_reporte_linkgps.yaml):
    name: crear_reporte_linkgps
    description: Pasos para crear un reporte en LinkGPS
    steps:
      - Abrir el panel de reportes
      - Seleccionar el tipo de reporte
      - ...
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class SkillMemory:
    """Gestiona skills (procedimientos) almacenados como archivos YAML."""

    def __init__(self, skills_dir: Path):
        """
        Args:
            skills_dir: Directorio donde se almacenan los archivos YAML.
        """
        self._skills_dir = skills_dir
        self._skills_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "SkillMemory inicializado: %s (%d skills)",
            skills_dir,
            len(self.list_skills()),
        )

    def list_skills(self) -> list[dict]:
        """Lista todos los skills disponibles."""
        skills = []
        for path in sorted(self._skills_dir.glob("*.yaml")):
            try:
                data = self._load_yaml(path)
                skills.append({
                    "name": path.stem,
                    "description": data.get("description", ""),
                    "file": path.name,
                })
            except Exception as e:
                logger.warning("Error leyendo skill %s: %s", path.name, e)
        return skills

    def get_skill(self, name: str) -> dict | None:
        """
        Carga y retorna un skill por nombre.

        Args:
            name: Nombre del skill (sin extensión .yaml).

        Returns:
            Diccionario con el contenido del skill, o None si no existe.
        """
        path = self._skills_dir / f"{name}.yaml"
        if not path.exists():
            return None

        try:
            return self._load_yaml(path)
        except Exception as e:
            logger.error("Error cargando skill '%s': %s", name, e)
            return None

    def save_skill(self, name: str, data: dict) -> str:
        """
        Guarda un skill como archivo YAML.

        Args:
            name: Nombre del skill (sin extensión).
            data: Contenido del skill (dict con name, description, steps, etc.).

        Returns:
            Nombre del archivo creado.
        """
        path = self._skills_dir / f"{name}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        logger.info("Skill guardado: %s", path.name)
        return path.name

    def delete_skill(self, name: str) -> bool:
        """Elimina un skill por nombre."""
        path = self._skills_dir / f"{name}.yaml"
        if path.exists():
            path.unlink()
            logger.info("Skill eliminado: %s", name)
            return True
        return False

    def search_skills(self, query: str) -> list[dict]:
        """
        Búsqueda simple por nombre y descripción de skills.
        """
        query_lower = query.lower()
        results = []
        for skill in self.list_skills():
            name = skill.get("name", "").lower()
            desc = skill.get("description", "").lower()
            if query_lower in name or query_lower in desc:
                full_skill = self.get_skill(skill["name"])
                if full_skill:
                    results.append(full_skill)
        return results

    def get_context_summary(self, query: str) -> str:
        """
        Genera un resumen de skills relevantes para contexto del LLM.
        """
        skills = self.search_skills(query)
        if not skills:
            all_skills = self.list_skills()
            if not all_skills:
                return ""
            # Si no hay match, listar los skills disponibles
            names = [s["name"] for s in all_skills]
            return f"**Skills disponibles:** {', '.join(names)}"

        lines = ["**Skills relevantes:**"]
        for skill in skills:
            name = skill.get("name", "")
            desc = skill.get("description", "")
            steps = skill.get("steps", [])
            lines.append(f"- **{name}**: {desc}")
            for step in steps[:5]:  # Limitar a 5 pasos
                lines.append(f"  - {step}")

        return "\n".join(lines)

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        """Carga un archivo YAML."""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
