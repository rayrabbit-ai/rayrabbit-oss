#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests unitarios y de integración para el transporte Realtime MCP SSE de RayRabbit
Copyright © 2024-2026 RayRabbit Labs, Inc.
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from api.server import app, _mcp_sse_sessions
from rayrabbit.core.message_bus import MessageBus

@pytest.fixture(autouse=True)
async def setup_infrastructure():
    """Configura una infraestructura viva en app.state para las pruebas."""
    bus = MessageBus()
    await bus.start()
    
    mock_infra = MagicMock()
    mock_infra.is_running = True
    mock_infra.message_bus = bus
    app.state.infrastructure = mock_infra
    
    # Registrar herramientas de prueba en mcp_protocol
    if bus.mcp_protocol:
        bus.mcp_protocol.register_tool(
            "test_add",
            "test_agent",
            {
                "description": "Herramienta de prueba suma",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"}
                    }
                }
            }
        )
    
    yield mock_infra
    await bus.stop()


@pytest.mark.asyncio
async def test_mcp_messages_initialize_and_ping():
    """Valida los métodos estándar 'initialize' y 'ping' sobre POST /api/mcp/messages."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Initialize
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test_client", "version": "1.0.0"}
            }
        }
        res = await client.post("/api/mcp/messages", json=init_payload)
        assert res.status_code == 200
        data = res.json()
        assert data.get("id") == 1
        assert data.get("result", {}).get("protocolVersion") == "2024-11-05"
        assert "tools" in data.get("result", {}).get("capabilities", {})

        # 2. Ping
        ping_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "ping"
        }
        res_ping = await client.post("/api/mcp/messages", json=ping_payload)
        assert res_ping.status_code == 200
        assert res_ping.json().get("result") == {}


@pytest.mark.asyncio
async def test_mcp_messages_tools_list():
    """Valida la consulta de herramientas disponibles vía POST /api/mcp/messages."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tools_payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {}
        }
        res = await client.post("/api/mcp/messages", json=tools_payload)
        assert res.status_code == 200
        data = res.json()
        assert data.get("id") == 3
        tools = data.get("result", {}).get("tools", [])
        assert len(tools) > 0
        assert any(t["name"] == "test_add" for t in tools)


@pytest.mark.asyncio
async def test_mcp_sse_session_queue_dispatch():
    """Valida la gestión de sesión SSE y la entrega de eventos JSON-RPC sobre la cola reactiva."""
    test_session_id = "test-session-12345"
    queue = asyncio.Queue()
    _mcp_sse_sessions[test_session_id] = queue
    
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ping_payload = {
                "jsonrpc": "2.0",
                "id": 42,
                "method": "ping"
            }
            res = await client.post(f"/api/mcp/messages?session_id={test_session_id}", json=ping_payload)
            assert res.status_code == 200
            
            # Verificar que el evento se haya emitido a la cola SSE de la sesión
            event_raw = await asyncio.wait_for(queue.get(), timeout=2.0)
            assert "event: message" in event_raw
            assert '"id": 42' in event_raw
    finally:
        _mcp_sse_sessions.pop(test_session_id, None)
