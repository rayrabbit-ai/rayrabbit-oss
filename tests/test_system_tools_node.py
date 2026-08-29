"""
RayRabbit OSS — System Tools Sovereign Node Unit Tests
======================================================
Pruebas unitarias para validar la paginación, sanitización pathlib.Path,
redacción de secretos criptográfica y autoría de habilidades (_AUTHORING_STANDARDS)
en SystemToolsNode.

SPDX-License-Identifier: Apache-2.0
"""
import pytest
import asyncio
from pathlib import Path
from examples.nodes.system_tools_node import (
    read_file,
    write_file,
    patch_file,
    search_files,
    skill_manage,
    terminal,
    _redact_secrets,
    _sanitize_path
)


@pytest.mark.asyncio
async def test_write_and_read_file_with_pagination(tmp_path: Path):
    test_file = tmp_path / "test_data.txt"
    lines = [f"Línea {i}" for i in range(1, 100)]
    content = "\n".join(lines)

    # 1. Escritura atómica
    write_res = await write_file(str(test_file), content)
    assert "Éxito" in write_res
    assert test_file.exists()

    # 2. Lectura paginada (Líneas 10 a 20)
    read_res = await read_file(str(test_file), offset=10, limit=10)
    assert "Líneas 10-19 de 99" in read_res
    assert "10 | Línea 10" in read_res
    assert "19 | Línea 19" in read_res


@pytest.mark.asyncio
async def test_secret_redaction(tmp_path: Path):
    test_file = tmp_path / "secrets.env"
    secret_content = "OPENAI_KEY=sk-proj-1234567890abcdef1234567890\nNV_KEY=nvapi-1234567890abcdef1234567890"
    await write_file(str(test_file), secret_content)

    read_res = await read_file(str(test_file))
    assert "sk-proj-1234567890abcdef1234567890" not in read_res
    assert "sk-****[REDACTED_API_KEY]****" in read_res
    assert "nvapi-****[REDACTED_API_KEY]****" in read_res


@pytest.mark.asyncio
async def test_patch_file(tmp_path: Path):
    test_file = tmp_path / "config.json"
    initial = '{"mode": "debug", "port": 8080}'
    await write_file(str(test_file), initial)

    patch_res = await patch_file(str(test_file), '"mode": "debug"', '"mode": "production"')
    assert "Éxito" in patch_res

    read_res = await read_file(str(test_file))
    assert '"mode": "production"' in read_res


@pytest.mark.asyncio
async def test_blocked_device_paths():
    with pytest.raises(PermissionError):
        _sanitize_path("/dev/zero")

    with pytest.raises(PermissionError):
        _sanitize_path("/dev/stdin")


@pytest.mark.asyncio
async def test_skill_authoring_standards(tmp_path: Path):
    # Probar rechazo de descripción > 60 chars
    invalid_desc = "Esta es una descripción extremadamente larga que supera los 60 caracteres requeridos por Hermes."
    res_fail = await skill_manage("create", "test-skill", invalid_desc, "contenido")
    assert "Error de Estándar" in res_fail

    # Probar guardado exitoso con desc <= 60 chars
    valid_desc = "Analiza y limpia archivos de log de SAP TM."
    res_ok = await skill_manage("create", "test-skill-sap", valid_desc, "# Instrucciones para SAP Logs")
    assert "Éxito" in res_ok
    assert (Path(".agent/skills/test-skill-sap") / "SKILL.md").exists()
