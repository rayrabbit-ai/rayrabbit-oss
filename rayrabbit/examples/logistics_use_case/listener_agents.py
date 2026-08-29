"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
# rayrabbit/examples/logistics_use_case/listener_agents.py
"""Agentes Listener para el Caso de Uso de Logística."""

import json
from rayrabbit.core.agent import Agent
from rayrabbit.communication.message import Message, MessageType
from rayrabbit.utils.logger import get_logger

logger = get_logger(__name__)

class A2UIListenerAgent(Agent):
    """Base class for listeners that need to notify the A2UI Manager."""
    
    async def notify_ui(self, title: str, description: str, correlation_id: str):
        """Sends a UI update command directly to the sovereign A2UI node."""
        import httpx
        payload = {
            "sender_id": self.id,
            "correlation_id": correlation_id,
            "content": {
                "action": "ui_update",
                "title": title,
                "description": description
            }
        }
        try:
            print(f"📡 [TELEMETRY] Enviando update a A2UI: {title} (CID: {correlation_id})")
            async with httpx.AsyncClient() as client:
                await client.post("http://127.0.0.1:8006/telemetry", json=payload, timeout=2.0)
        except Exception as e:
            logger.warning(f"Fallo envío directo de telemetría a A2UI: {e}")

class LangChainResponseListenerAgent(A2UIListenerAgent):
    """Escucha la respuesta de LangChain con las entidades extraídas y la enruta a CrewAI."""
    def __init__(self, agent_id: str = "langchain_response_listener", name: str = "LangChain Response Listener"):
        super().__init__(agent_id, name)
        self.register_message_handler(MessageType.RESPONSE, self.handle_langchain_response)

    async def handle_langchain_response(self, message: Message):
        """Recibe la respuesta de LangChain."""
        if message.sender_id in ["crewai_bridge", "crewai_service_bridge"]:
            return

        logger.info(f"[LangChainResponseListener] Respuesta recibida (CorrID: {message.correlation_id}).")
        
        content = message.content
        if isinstance(content, dict) and (content.get("task") == "investigate_delivery"):
            logger.info(f"-> [LangChainResponseListener] Enrutando a CrewAI.")
            
            # Notificar A2UI
            await self.notify_ui("Análisis Estructural", "Entidades extraídas. Iniciando orquestación con CrewAI.", message.correlation_id)

            crewai_task = Message(
                sender_id=self.id,
                sender_name=self.name,
                recipient_id="crewai_service_bridge",
                message_type=MessageType.REQUEST,
                correlation_id=message.correlation_id,
                content={
                    "operation": "run_crew",
                    "task": content.get("task"),
                    "package_id": content.get("package_id"),
                    "priority": content.get("priority"),
                    "client_message": content.get("client_message"),
                    "correlation_id": message.correlation_id
                }
            )
            await self.message_bus.publish(crewai_task)
        else:
            logger.info(f"-> [LangChainResponseListener] Enrutando a FinalCustomerResponseListener.")
            final_msg = Message(
                sender_id=self.id,
                sender_name=self.name,
                recipient_id="final_customer_response_listener",
                message_type=MessageType.RESPONSE,
                correlation_id=message.correlation_id,
                content=content
            )
            await self.message_bus.publish(final_msg)

class CrewAIWorkflowListenerAgent(A2UIListenerAgent):
    """Escucha el mensaje de CrewAI para iniciar un workflow en AutoGen."""
    def __init__(self, agent_id: str = "crewai_workflow_listener", name: str = "CrewAI Workflow Listener"):
        super().__init__(agent_id, name)
        self.register_message_handler(MessageType.REQUEST, self.handle_workflow_request)

    async def handle_workflow_request(self, message: Message):
        logger.info(f"[CrewAIWorkflowListener] Enrutando a AutoGen...")
        
        # Notificar A2UI
        await self.notify_ui("Estrategia de Investigación", "CrewAI ha diseñado el plan de acción. Iniciando agentes de campo (AutoGen).", message.correlation_id)

        autogen_task = Message(
            sender_id=self.id,
            sender_name=self.name,
            recipient_id="autogen_service_bridge",
            message_type=MessageType.REQUEST,
            correlation_id=message.correlation_id,
            content={
                "operation": "run_autogen_chat",
                "workflow_id": message.correlation_id,
                "task_ref": message.correlation_id,
                "actions": [{"type": message.content.get("task", "unknown"), "package_id": message.content.get("package_id", "N/A")}],
                "callback_topic": "autogen_update_listener"
            }
        )
        await self.message_bus.publish(autogen_task)

class CrewAIFinalDecisionListenerAgent(A2UIListenerAgent):
    """Escucha la decisión final de CrewAI y la enruta a LangChain."""
    def __init__(self, agent_id: str = "crewai_final_decision_listener", name: str = "CrewAI Final Decision Listener"):
        super().__init__(agent_id, name)
        self.register_message_handler(MessageType.RESPONSE, self.handle_final_decision)

    async def handle_final_decision(self, message: Message):
        if message.sender_id == "langchain_service_bridge":
            return

        logger.info(f"[CrewAIFinalDecisionListener] Enrutando a LangChain...")
        
        # Notificar A2UI
        await self.notify_ui("Síntesis de Resolución", "Investigación completada. Generando narrativa final para el cliente.", message.correlation_id)

        langchain_task = Message(
            sender_id=self.id,
            sender_name=self.name,
            recipient_id="langchain_service_bridge",
            message_type=MessageType.REQUEST,
            correlation_id=message.correlation_id,
            content={
                "operation": "invoke_chain",
                "prompt_template": (
                    "Eres un agente de atención al cliente amable. Informa sobre el paquete {package_id}. "
                    "Resultado: {outcome}. Detalles: {details}. Escribe una respuesta final cortés."
                ),
                "input_variables": {
                    "package_id": message.content.get("package_id"),
                    "outcome": message.content.get("outcome"),
                    "details": message.content.get("details")
                }
            }
        )
        await self.message_bus.publish(langchain_task)

class AutoGenUpdateListenerAgent(A2UIListenerAgent):
    """Escucha las actualizaciones de progreso de AutoGen."""
    def __init__(self, agent_id: str = "autogen_update_listener", name: str = "AutoGen Update Listener"):
        super().__init__(agent_id, name)
        self.register_message_handler(MessageType.EVENT, self.handle_autogen_update)
        self.register_message_handler(MessageType.RESPONSE, self.handle_autogen_update)

    async def handle_autogen_update(self, message: Message):
        status = message.content.get("status")
        detail = message.content.get("detail", {})
        
        logger.info(f"[AutoGenUpdateListener] Estado: {status}")

        # Notificar A2UI del progreso técnico
        description = detail.get("final_summary") or detail.get("message") or "Procesando tarea..."
        await self.notify_ui("Investigación en Almacén", f"Estado: {status}. {description}", message.correlation_id)

        if status == "completed":
            final_decision_message = Message(
                sender_id=self.id,
                sender_name=self.name,
                recipient_id="crewai_final_decision_listener",
                message_type=MessageType.RESPONSE,
                correlation_id=message.correlation_id,
                content={
                    "outcome": "autogen_workflow_completed",
                    "details": detail.get("final_summary"),
                    "package_id": detail.get("package_id") or message.correlation_id
                }
            )
            await self.message_bus.publish(final_decision_message)

class FinalCustomerResponseListenerAgent(A2UIListenerAgent):
    """Escucha la respuesta final y la muestra en la UI."""
    def __init__(self, agent_id: str = "final_customer_response_listener", name: str = "Final Customer Response Listener"):
        super().__init__(agent_id, name)
        self.register_message_handler(MessageType.RESPONSE, self.handle_final_response)

    async def handle_final_response(self, message: Message):
        content = message.content.get('content') or message.content.get('text', 'No hay contenido.')
        logger.info(f"--- RESPUESTA FINAL AL CLIENTE ---")
        
        # Notificar A2UI - Esta es la narrativa final
        ui_msg = Message(
            sender_id=self.id,
            sender_name=self.name,
            recipient_id="logistics_ui_manager",
            message_type=MessageType.COMMAND,
            correlation_id=message.correlation_id,
            content={
                "action": "final_narrative",
                "text": content
            }
        )
        await self.publish_message(ui_msg)
