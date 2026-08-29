"""
Tests para ProgressiveStageDelegator y StageGatingPlan en RayRabbit.
Verifica la divulgación progresiva de herramientas y el avance de fases agénticas sin saltos prematuros.
"""

import pytest
from rayrabbit.utils.delegate_tool import ProgressiveStageDelegator

@pytest.fixture
def sample_catalog():
    return [
        {
            "name": "execute_crew_task",
            "category": "cognitive",
            "description": "Ejecuta cuadrilla agéntica de CrewAI para diagnóstico y análisis en SAP TM",
            "input_schema": {"properties": {"user_prompt": {"type": "string"}}}
        },
        {
            "name": "start_autogen_chat",
            "category": "cognitive",
            "description": "Ejecuta conversación agéntica multi-agente en AutoGen para reasignación logística",
            "input_schema": {"properties": {"user_prompt": {"type": "string"}}}
        },
        {
            "name": "run_lcel_chain",
            "category": "cognitive",
            "description": "Ejecuta una cadena LangChain LCEL para resumir, analizar o consolidar datos finales",
            "input_schema": {"properties": {"prompt_or_task": {"type": "string"}}}
        },
        {
            "name": "read_session_memory",
            "category": "memory",
            "description": "Lee hechos estructurados de la memoria soberana L3",
            "input_schema": {"properties": {"session_id": {"type": "string"}}}
        },
        {
            "name": "save_memory_fact",
            "category": "memory",
            "description": "Persiste un hecho en la memoria soberana L3",
            "input_schema": {"properties": {"session_id": {"type": "string"}}}
        }
    ]

def test_progressive_stage_disclosure(sample_catalog):
    goal = "Ejecuta el pipeline trilateral para el pedido ORD-2025-002: Diagnostico CrewAI en SAP TM, Reasignacion logistica AutoGen, Resumen ejecutivo LangChain."
    delegator = ProgressiveStageDelegator(sample_catalog)

    # Turno 1: Ninguna herramienta ejecutada
    plan_t1 = delegator.resolve_stage_plan(goal, executed_tools=[])
    assert plan_t1.current_stage_index == 0
    assert not plan_t1.is_completed
    tools_t1 = delegator.get_scoped_tools_for_active_stage(goal, executed_tools=[])
    tool_names_t1 = [t["name"] for t in tools_t1]
    assert "execute_crew_task" in tool_names_t1
    assert "start_autogen_chat" not in tool_names_t1
    assert "run_lcel_chain" not in tool_names_t1

    # Turno 2: CrewAI ya ejecutado
    plan_t2 = delegator.resolve_stage_plan(goal, executed_tools=["execute_crew_task"])
    assert plan_t2.current_stage_index == 1
    assert not plan_t2.is_completed
    tools_t2 = delegator.get_scoped_tools_for_active_stage(goal, executed_tools=["execute_crew_task"])
    tool_names_t2 = [t["name"] for t in tools_t2]
    assert "start_autogen_chat" in tool_names_t2
    assert "execute_crew_task" not in tool_names_t2
    assert "run_lcel_chain" not in tool_names_t2

    # Turno 3: CrewAI y AutoGen ya ejecutados
    plan_t3 = delegator.resolve_stage_plan(goal, executed_tools=["execute_crew_task", "start_autogen_chat"])
    assert plan_t3.current_stage_index == 2
    assert not plan_t3.is_completed
    tools_t3 = delegator.get_scoped_tools_for_active_stage(goal, executed_tools=["execute_crew_task", "start_autogen_chat"])
    tool_names_t3 = [t["name"] for t in tools_t3]
    assert "run_lcel_chain" in tool_names_t3
    assert "start_autogen_chat" not in tool_names_t3
    assert "execute_crew_task" not in tool_names_t3

    # Turno 4: Las 3 herramientas completadas
    plan_t4 = delegator.resolve_stage_plan(goal, executed_tools=["execute_crew_task", "start_autogen_chat", "run_lcel_chain"])
    assert plan_t4.is_completed
    assert plan_t4.active_tool_name is None
    tools_t4 = delegator.get_scoped_tools_for_active_stage(goal, executed_tools=["execute_crew_task", "start_autogen_chat", "run_lcel_chain"])
    tool_names_t4 = [t["name"] for t in tools_t4]
    assert "execute_crew_task" not in tool_names_t4
    assert "start_autogen_chat" not in tool_names_t4
    assert "run_lcel_chain" not in tool_names_t4
    # Solo herramientas de memoria
    assert "read_session_memory" in tool_names_t4

def test_active_tool_name_resolution(sample_catalog):
    goal = "Pipeline multi-etapa: 1. Diagnostico SAP con CrewAI. 2. Negociacion AutoGen. 3. Resumen LangChain."
    delegator = ProgressiveStageDelegator(sample_catalog)

    # Turno 1
    plan_1 = delegator.resolve_stage_plan(goal, executed_tools=[])
    assert plan_1.active_tool_name == "execute_crew_task"
    assert not plan_1.is_completed

    # Turno 2
    plan_2 = delegator.resolve_stage_plan(goal, executed_tools=["execute_crew_task"])
    assert plan_2.active_tool_name == "start_autogen_chat"
    assert not plan_2.is_completed

    # Turno 3
    plan_3 = delegator.resolve_stage_plan(goal, executed_tools=["execute_crew_task", "start_autogen_chat"])
    assert plan_3.active_tool_name == "run_lcel_chain"
    assert not plan_3.is_completed

    # Turno 4
    plan_4 = delegator.resolve_stage_plan(goal, executed_tools=["execute_crew_task", "start_autogen_chat", "run_lcel_chain"])
    assert plan_4.is_completed
    assert plan_4.active_tool_name is None

def test_n_stage_custom_pipeline():
    custom_catalog = [
        {
            "name": "custom_fraud_analyzer",
            "category": "cognitive",
            "description": "Analiza patrones de fraude financiero y riesgo crediticio",
            "input_schema": {"properties": {"account_id": {"type": "string"}}}
        },
        {
            "name": "custom_compliance_checker",
            "category": "cognitive",
            "description": "Verifica normativas y regulaciones de cumplimiento bancario",
            "input_schema": {"properties": {"report": {"type": "string"}}}
        },
        {
            "name": "read_session_memory",
            "category": "memory",
            "description": "Lee memoria L3",
            "input_schema": {}
        }
    ]
    goal = "Auditoria Financiera: Analisis de fraude de cuenta, y verificacion de normativas de cumplimiento."
    delegator = ProgressiveStageDelegator(custom_catalog)

    # Fase 1: Fraude
    plan_1 = delegator.resolve_stage_plan(goal, executed_tools=[])
    assert plan_1.active_tool_name == "custom_fraud_analyzer"
    assert not plan_1.is_completed

    # Fase 2: Cumplimiento
    plan_2 = delegator.resolve_stage_plan(goal, executed_tools=["custom_fraud_analyzer"])
    assert plan_2.active_tool_name == "custom_compliance_checker"
    assert not plan_2.is_completed

    # Fase 3: Concluido
    plan_3 = delegator.resolve_stage_plan(goal, executed_tools=["custom_fraud_analyzer", "custom_compliance_checker"])
    assert plan_3.is_completed

def test_combinations_from_spec(sample_catalog):
    # Combinación 2: LangChain -> CrewAI
    g2 = "Ejecuta una cadena LCEL con LangChain para obtener las especificaciones del producto. Luego, utiliza CrewAI para verificar si nuestra flota dispone de capacidad."
    d2 = ProgressiveStageDelegator(sample_catalog)
    p2_1 = d2.resolve_stage_plan(g2, [])
    assert p2_1.active_tool_name == "run_lcel_chain"
    p2_2 = d2.resolve_stage_plan(g2, ["run_lcel_chain"])
    assert p2_2.active_tool_name == "execute_crew_task"
    p2_3 = d2.resolve_stage_plan(g2, ["run_lcel_chain", "execute_crew_task"])
    assert p2_3.is_completed

    # Combinación 4: AutoGen -> CrewAI
    g4 = "Inicia un debate en AutoGen para analizar el spread. Acto seguido, ejecuta una tarea de CrewAI que determine si se aprueba la orden."
    d4 = ProgressiveStageDelegator(sample_catalog)
    p4_1 = d4.resolve_stage_plan(g4, [])
    assert p4_1.active_tool_name == "start_autogen_chat"
    p4_2 = d4.resolve_stage_plan(g4, ["start_autogen_chat"])
    assert p4_2.active_tool_name == "execute_crew_task"
    p4_3 = d4.resolve_stage_plan(g4, ["start_autogen_chat", "execute_crew_task"])
    assert p4_3.is_completed

def test_atomic_domain_query_direct_resolution():
    catalog_with_domain = [
        {"name": "get_crypto_price", "category": "crypto", "description": "Obtiene cotizacion Bitcoin BTC en Binance", "input_schema": {}},
        {"name": "execute_crew_task", "category": "cognitive", "description": "CrewAI diagnostico SAP", "input_schema": {}},
        {"name": "read_session_memory", "category": "memory", "description": "Lee memoria", "input_schema": {}}
    ]
    delegator = ProgressiveStageDelegator(catalog_with_domain)
    goal = "Dame el precio del BTC/USDT en tiempo real"
    plan = delegator.resolve_stage_plan(goal, [])
    assert plan.active_tool_name == "get_crypto_price"
    scoped = delegator.get_scoped_tools_for_active_stage(goal, [])
    scoped_names = [t["name"] for t in scoped]
    assert "get_crypto_price" in scoped_names
    assert "read_session_memory" in scoped_names
    assert "execute_crew_task" not in scoped_names



