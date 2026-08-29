"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
"""
Define el Proyecto de Orquestación Logística.

Este proyecto orquesta el flujo completo de logística utilizando la infraestructura
federada A2A y MCP de RayRabbit. Integra servicios de LangChain, CrewAI y AutoGen
en un pipeline automático.
"""
import logging
from typing import Any, Dict, Optional

from rayrabbit.core.project import BaseProject
from rayrabbit.agents.orchestrator_agent import OrchestratorAgent, Pipeline
from rayrabbit.communication.message import Message, MessageType
from rayrabbit.utils.exceptions import RayRabbitError
from rayrabbit.utils.logger import get_logger

logger = get_logger("LogisticsOrchestrationProject")

class LogisticsOrchestrationProject(BaseProject):
    """
    Orquesta el flujo federado de logística: Análisis -> Ruta -> Flota.
    """
    
    def __init__(self, project_name: str):
        """Inicializa el proyecto."""
        super().__init__(project_name)
        self.orchestrator: Optional[OrchestratorAgent] = None

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Punto de entrada para la lógica de orquestación del proyecto.
        """
        if not self.framework:
            raise RayRabbitError("La infraestructura no ha sido inyectada en el proyecto.")

        # 1. Crear OrchestratorAgent si no existe
        if not self.orchestrator:
            self.orchestrator = OrchestratorAgent(
                agent_id="logistics_orchestrator",
                name="Logistics Orchestrator",
                description="Orquestador automático del caso logístico federado"
            )
            await self.framework.register_agent(self.orchestrator)
            
            # 2. Descubrir herramientas automáticamente vía A2ARouter (DiscoveryService)
            logger.info("Descubriendo herramientas vía DiscoveryService...")
            await self.orchestrator.discover_from_router("logistics_manager")
            await self.orchestrator.discover_from_router("route_optimizer")
            await self.orchestrator.discover_from_router("fleet_commander")

            # 3. Definir pipeline
            pipeline = Pipeline("logistics_flow", "Pipeline completo de logística")
            pipeline \
                .add_step("logistics_manager", "analyze_order",
                         lambda args: {"order_id": args.get("order_id"), "priority": args.get("priority", "high")}) \
                .add_step("route_optimizer", "optimize_route",
                         lambda prev: {"origin": "MAD", "destination": "BCN"}) \
                .add_step("fleet_commander", "assign_vehicle",
                         lambda prev: {"cargo_type": "fragile", "distance_km": 320})
            
            self.orchestrator.register_pipeline(pipeline)

            # 4. Instanciar Agente A2UI Nativo para Dashboard Logístico
            from rayrabbit.examples.logistics_use_case.logistics_a2ui_agent import LogisticsA2UIAgent
            self.a2ui_agent = LogisticsA2UIAgent(
                agent_id="logistics_ui_manager",
                name="Logistics UI Manager"
            )
            # Inyectar dependencias de seguridad MAESTRO si están disponibles en el framework
            if hasattr(self.framework, 'framework_security'):
                self.a2ui_agent.maestro = self.framework.framework_security

            await self.framework.register_agent(self.a2ui_agent)
            
            # Suscribir el Agente UI a eventos relevantes del pipeline
            self.framework.message_bus.subscribe("logistics_flow_updates", self.a2ui_agent.id)
            logger.info("Agente A2UI Nativo (Logistics UI Manager) registrado y suscrito.")

        # 4. Ejecutar pipeline
        try:
            order_id = payload.get("order_id", "ORD-PROJECT-001")
            priority = payload.get("priority", "high")
            
            logger.info(f"Ejecutando pipeline logístico para pedido {order_id}...")
            
            result = await self.orchestrator.execute_pipeline(
                "logistics_flow",
                initial_args={"order_id": order_id, "priority": priority}
            )
            
            return {
                "status": "success",
                "project": self.project_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error en ejecución del proyecto logístico: {e}")
            return {"status": "error", "message": str(e)}

class LogisticsClassicProject(BaseProject):
    """
    Implementa el flujo clásico de logística basado en Declarative Bridges.
    Envía mensajes iniciales al bridge de LangChain para iniciar la cadena.
    """
    
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el flujo clásico publicando un mensaje al bus.
        """
        if not self.framework:
            raise RayRabbitError("La infraestructura no ha sido inyectada.")

        # Extraer parámetros o usar defaults
        order_info = payload.get("order_info", "Mi paquete #A123 no llegó")
        
        # En el flujo clásico, enviamos un mensaje al bridge coordinado
        message = Message(
            sender_id="customer_service",
            sender_name="Customer Service",
            recipient_id="langchain_service_bridge",
            message_type=MessageType.REQUEST,
            content={
                "operation": "invoke_chain",
                "prompt_template": "Interpreta el mensaje: {topic}",
                "input_variables": {"topic": order_info}
            }
        )
        
        await self.framework.message_bus.publish(message)
        logger.info("Encadenamiento clásico iniciado vía Declarative Bridge.")
        
        return {
            "status": "success",
            "message": "Flujo de logística clásico (Declarative Bridge) iniciado."
        }
