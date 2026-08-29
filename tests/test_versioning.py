"""
Tests automatizados para verificar la consistencia del versionado semántico (SemVer)
en todo el ecosistema de RayRabbit OSS.
"""

import json
from pathlib import Path
import subprocess
import sys
import pytest

import rayrabbit
from rayrabbit.version import get_version, __version__
from api.server import app


def test_core_version():
    """Verifica que __version__ en rayrabbit y rayrabbit.version sea 0.1.0."""
    assert __version__ == "0.1.0"
    assert rayrabbit.__version__ == "0.1.0"
    assert get_version() == "0.1.0"


def test_fastapi_hub_version():
    """Verifica que la app FastAPI del Hub tenga version=0.1.0."""
    assert app.version == "0.1.0"


def test_cli_version_flag():
    """Verifica que el CLI rayrabbit responda a -v y --version con la versión unificada."""
    result = subprocess.run(
        [sys.executable, "-m", "rayrabbit.cli.main", "--version"],
        capture_output=True,
        text=True,
        check=True
    )
    output = result.stdout.strip() or result.stderr.strip()
    assert "RayRabbit CLI v0.1.0" in output


def test_plugin_manifests_version():
    """Verifica que los manifiestos de plugin tengan version=0.1.0."""
    root = Path(__file__).resolve().parent.parent
    agent_plugin = root / ".agent" / "plugins" / "antigravity" / "plugin.json"
    client_plugin = root / "clients" / "antigravity" / "plugin.json"

    for plugin_path in [agent_plugin, client_plugin]:
        assert plugin_path.is_file(), f"No se encontró el plugin en {plugin_path}"
        data = json.loads(plugin_path.read_text(encoding="utf-8"))
        assert data.get("version") == "0.1.0", f"Versión incorrecta en {plugin_path}: {data.get('version')}"


def test_javascript_packages_version():
    """Verifica que los package.json de los SDKs JS tengan version=0.1.0."""
    root = Path(__file__).resolve().parent.parent
    js_packages = [
        root / "clients" / "javascript" / "package.json",
        root / "clients" / "javascript" / "@rayrabbit-client" / "package.json",
        root / "clients" / "javascript" / "@rayrabbit-a2ui" / "package.json",
        root / "clients" / "javascript" / "apps" / "sdk-a2ui" / "package.json",
    ]
    for pkg in js_packages:
        assert pkg.is_file(), f"No se encontró {pkg}"
        data = json.loads(pkg.read_text(encoding="utf-8"))
        assert data.get("version") == "0.1.0", f"Versión incorrecta en {pkg}: {data.get('version')}"
