"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Pruebas Unitarias para BM25ToolIndex y Selección Dinámica de Herramientas (tool_search_engine.py).
"""

import pytest
from rayrabbit.utils.tool_search_engine import BM25ToolIndex, match_top_k_tools
from rayrabbit.utils.tool_result_storage import maybe_persist_tool_result

MOCK_HUB_TOOLS = [
    {
        "name": "analyze_order",
        "category": "logistics_ui_manager",
        "description": "Consulta y analiza el estado logístico de un pedido en la base de datos de SAP TM.",
        "input_schema": {"properties": {"order_id": {"type": "string"}}}
    },
    {
        "name": "track_package",
        "category": "logistics_ui_manager",
        "description": "Rastrea la ubicación en tiempo real de un paquete o envío.",
        "input_schema": {"properties": {"tracking_code": {"type": "string"}}}
    },
    {
        "name": "get_crypto_price",
        "category": "crypto_trader_agent",
        "description": "Obtiene la cotización en vivo de criptomonedas como BTC o ETH desde Binance.",
        "input_schema": {"properties": {"symbol": {"type": "string"}}}
    },
    {
        "name": "place_crypto_order",
        "category": "crypto_trader_agent",
        "description": "Ejecuta una orden de compra o venta de activos digitales.",
        "input_schema": {"properties": {"symbol": {"type": "string"}, "amount": {"type": "number"}}}
    },
    {
        "name": "save_memory_fact",
        "category": "sovereign_memory_node",
        "description": "Guarda un hecho declarativo en la memoria compartida de la sesión.",
        "input_schema": {"properties": {"session_id": {"type": "string"}, "fact_key": {"type": "string"}, "fact_value": {"type": "string"}}}
    },
    {
        "name": "read_session_memory",
        "category": "sovereign_memory_node",
        "description": "Lee los hechos declarativos almacenados en la memoria de la sesión.",
        "input_schema": {"properties": {"session_id": {"type": "string"}}}
    }
]

def test_bm25_search_logistics():
    prompt = "Necesito analizar el estado del pedido ORD-2025-001 en SAP TM"
    matched = match_top_k_tools(prompt, MOCK_HUB_TOOLS, top_k=2)
    matched_names = [t["name"] for t in matched]

    # Debe incluir herramientas de memoria obligatorias
    assert "save_memory_fact" in matched_names
    assert "read_session_memory" in matched_names
    # Debe clasificar analyze_order como la herramienta de dominio más relevante
    assert "analyze_order" in matched_names
    # NO debe incluir herramientas irrelevantes como criptomonedas
    assert "get_crypto_price" not in matched_names

def test_bm25_search_crypto():
    prompt = "Consultar precio de Bitcoin BTC en Binance"
    matched = match_top_k_tools(prompt, MOCK_HUB_TOOLS, top_k=2)
    matched_names = [t["name"] for t in matched]

    assert "get_crypto_price" in matched_names
    assert "analyze_order" not in matched_names

def test_explicit_target_tools():
    prompt = "Cualquier prompt"
    matched = match_top_k_tools(prompt, MOCK_HUB_TOOLS, target_tools="analyze_order")
    matched_names = [t["name"] for t in matched]

    assert "analyze_order" in matched_names
    assert "save_memory_fact" in matched_names
    assert "get_crypto_price" not in matched_names

def test_orchestrator_empty_query_search():
    orchestrator_catalog = [
        {"name": "execute_crew_task", "category": "cognitive", "description": "CrewAI diagnostico SAP TM", "input_schema": {}},
        {"name": "start_autogen_chat", "category": "cognitive", "description": "AutoGen reasignacion logistica", "input_schema": {}},
        {"name": "read_session_memory", "category": "memory", "description": "Lee memoria", "input_schema": {}}
    ]
    matched = match_top_k_tools("", orchestrator_catalog, top_k=10, agent_role="orchestrator")
    matched_names = [t["name"] for t in matched]
    assert "read_session_memory" in matched_names
    assert "execute_crew_task" in matched_names
    assert "start_autogen_chat" in matched_names

def test_orchestrator_finds_domain_tools_natural_language():
    prompt = "Dame el precio del BTC/USDT en tiempo real"
    matched = match_top_k_tools(prompt, MOCK_HUB_TOOLS, top_k=2, agent_role="orchestrator")
    matched_names = [t["name"] for t in matched]
    assert "get_crypto_price" in matched_names
    assert "save_memory_fact" in matched_names

def test_tool_result_storage():
    short_res = "Resultado corto de 100 caracteres."
    assert maybe_persist_tool_result(short_res, "test_tool") == short_res

    large_res = "x" * 60000
    persisted_res = maybe_persist_tool_result(large_res, "test_tool")
    assert "<persisted-output>" in persisted_res
    assert ".txt" in persisted_res


