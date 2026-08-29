"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""

from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import re

PACKAGE_NAME = "rayrabbit-oss"


def get_version() -> str:
    """
    Obtiene la versión del paquete instalado o la resuelve dinámicamente
    desde pyproject.toml de forma agnóstica al entorno usando pathlib.Path.
    """
    try:
        return version(PACKAGE_NAME)
    except (PackageNotFoundError, Exception):
        try:
            pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
            if pyproject_path.is_file():
                try:
                    import tomllib
                    with open(pyproject_path, "rb") as f:
                        data = tomllib.load(f)
                        val = data.get("project", {}).get("version")
                        if val:
                            return str(val)
                except ImportError:
                    content = pyproject_path.read_text(encoding="utf-8")
                    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        return "0.1.0"


__version__ = get_version()
