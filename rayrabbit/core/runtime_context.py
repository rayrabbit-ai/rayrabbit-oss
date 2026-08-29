"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import os
import platform
from pathlib import Path

class RuntimeContext:
    """
    Centraliza la gestión de rutas y contexto de ejecución de RayRabbit de forma agnóstica.
    Elimina la dependencia de PROJECT_ROOT y habilita la soberanía en despliegues reales.
    """

    @staticmethod
    def get_rayrabbit_home() -> Path:
        """
        Calcula la ruta base para datos persistentes (identidades, auditoría, config).
        Se almacena dentro del proyecto en la carpeta .rayrabbit_data de forma auto-contenida.
        """
        env_home = os.getenv("RAYRABBIT_HOME")
        if env_home:
            return Path(env_home).resolve()

        # Encontrar la raíz del proyecto dinámicamente buscando pyproject.toml hacia arriba
        current = Path(__file__).resolve().parent
        for _ in range(10):
            if (current / "pyproject.toml").exists():
                return current / ".rayrabbit_data"
            current = current.parent
        
        # Fallback si no se encuentra pyproject.toml
        return Path.cwd() / ".rayrabbit_data"

    @classmethod
    def get_keystore_dir(cls) -> Path:
        """Ruta para llaves públicas de terceros (federación)."""
        env_keystore = os.getenv("RAYRABBIT_KEYSTORE")
        if env_keystore:
            path = Path(env_keystore).resolve()
        else:
            path = cls.get_rayrabbit_home() / "keystore"
            
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_identity_dir(cls) -> Path:
        """Ruta privada de la propia identidad del agente (private_key)."""
        path = cls.get_rayrabbit_home() / "identity"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_audit_dir(cls) -> Path:
        """Ruta para logs de auditoría SQLite."""
        path = cls.get_rayrabbit_home() / "audit_logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_data_dir(cls) -> Path:
        """Ruta para bases de datos persistentes del sistema."""
        path = cls.get_rayrabbit_home() / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_config_path(cls) -> Path:
        """Ruta del archivo de configuración global."""
        return cls.get_rayrabbit_home() / "config.yaml"

    @classmethod
    def get_agent_data_path(cls, agent_id: str, subfolder: str = "") -> Path:
        """Ruta para datos específicos de un agente (logs, etc)."""
        path = cls.get_rayrabbit_home() / "agents" / agent_id / subfolder
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def resolve_env_path(cls, filename: str = ".env") -> Path:
        """Busca un archivo .env en HOME o en el CWD."""
        home_env = cls.get_rayrabbit_home() / filename
        if home_env.exists():
            return home_env
        return Path.cwd() / filename
