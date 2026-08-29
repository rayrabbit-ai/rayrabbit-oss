"""
RayRabbit OSS — Sovereign Memory Node Integration Tests
======================================================
Pruebas de integración para validar la persistencia en SQLite,
la herramienta save_memory_fact y el proveedor de recursos rayrabbit://memory/{session_id}.

SPDX-License-Identifier: Apache-2.0
"""
import pytest
import json
import asyncio
from pathlib import Path
from examples.nodes.sovereign_memory_node import (
    save_memory_fact,
    read_session_memory,
    get_memory_resource_content,
    SovereignMemoryStore
)


@pytest.mark.asyncio
async def test_sovereign_memory_store(tmp_path: Path):
    db_file = tmp_path / "test_memory.db"
    test_store = SovereignMemoryStore(db_file)

    session_id = "test_session_123"
    assert test_store.save_fact(session_id, "user_language", "Spanish", "preference")
    assert test_store.save_fact(session_id, "preferred_theme", "dark_mode", "preference")

    facts = test_store.get_facts_for_session(session_id)
    assert len(facts) == 2
    assert facts[0]["fact_key"] == "user_language"
    assert facts[0]["fact_value"] == "Spanish"


@pytest.mark.asyncio
async def test_memory_tools_and_resource_provider(tmp_path: Path):
    session_id = "demo_session_456"

    # 1. Guardar hechos mediante la herramienta MCP
    save_res = await save_memory_fact(session_id, "crypto_favorite", "BTC/USDT", "market")
    assert "Éxito" in save_res

    # 2. Leer hechos mediante la herramienta de lectura
    read_res = await read_session_memory(session_id)
    data = json.loads(read_res)
    assert data["session_id"] == session_id
    assert data["facts_count"] >= 1
    assert data["facts"][0]["fact_key"] == "crypto_favorite"

    # 3. Resolver recurso MCP rayrabbit://memory/{session_id}
    uri = f"rayrabbit://memory/{session_id}"
    resource_payload = get_memory_resource_content(uri)
    res_data = json.loads(resource_payload)
    assert res_data["uri"] == uri
    assert res_data["session_id"] == session_id
    assert len(res_data["facts"]) >= 1
