"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import asyncio
import httpx
import logging
import os
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from ..communication.message import Message, MessageType
from ..utils.logger import get_logger
from ..security.auditing import AuditManager, AuditEvent
from ..security.auditing import AuditLevel, EventCategory
from ..resilience.function_cooling import FunctionCooler

@dataclass
class AgentCard:
    """Metadata de un agente para descubrimiento y routing."""
    agent_id: str
    name: str
    protocols: List[str] = field(default_factory=list) # ["http", "mcp", "a2a"]
    capabilities: List[str] = field(default_factory=list)
    endpoints: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    organization: Optional[str] = None
    public_key_pem: Optional[str] = None

class A2ARouter:
    """
    Router agnóstico A2A que prioriza routing directo (Peer-to-Peer) con fallback a hub.
    Cumple con la especificación AAIF para interoperabilidad federada.
    """
    
    def __init__(self, message_bus: Any, audit_manager: Optional[AuditManager] = None):
        self.message_bus = message_bus
        self.audit_manager = audit_manager
        self.registry: Dict[str, AgentCard] = {}
        self.logger = get_logger("A2ARouter")
        from ..utils.config import get_config_manager
        config_mgr = get_config_manager()
        p2p_timeout = 600.0
        try:
            p2p_timeout = float(config_mgr.data.custom.get("discovery", {}).get("p2p_timeout", 600.0))
        except Exception:
            pass
        self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(p2p_timeout, connect=15.0, read=p2p_timeout, write=30.0))
        self.coolers: Dict[str, FunctionCooler] = {} # Coolers por endpoint
        self.metrics: Dict[str, int] = {
            "p2p_sent": 0,
            "p2p_received": 0,
            "p2p_errors": 0,
            "hub_fallback": 0
        }

    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Registra un agente en el router local."""
        self.registry[agent_card.agent_id] = agent_card
        self.logger.info(f"Agente '{agent_card.agent_id}' registrado en A2ARouter.")
        return True

    async def discover_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Descubre un agente en el registro local."""
        return self.registry.get(agent_id)

    async def route_message(self, sender_id: str, recipient_id: str, content: Any, message_type: MessageType = MessageType.REQUEST, correlation_id: Optional[str] = None, no_hub_fallback: bool = False) -> Any:
        """
        Enruta un mensaje buscando el camino más eficiente (Directo > Hub).
        Soporta inteligentemente A2A y MCP Nativo.
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        self.logger.info(f"[{correlation_id}] route_message: routing to {recipient_id}")
        agent = await self.discover_agent(recipient_id)
        
        # Identificar si es una llamada MCP Nativa (método tools/call)
        is_mcp = isinstance(content, dict) and content.get("method") == "tools/call"
        
        # 1. Intentar Routing Directo (P2P)
        if agent:
            endpoint = None
            if is_mcp and "mcp_call" in agent.endpoints:
                endpoint = agent.endpoints["mcp_call"]
                protocol_label = "MCP"
            elif "a2a" in agent.protocols and "a2a" in agent.endpoints:
                endpoint = agent.endpoints["a2a"]
                protocol_label = "A2A"

            if endpoint:
                if endpoint not in self.coolers:
                    self.coolers[endpoint] = FunctionCooler(
                        name=f"p2p_{recipient_id}_{protocol_label.lower()}",
                        audit_manager=self.audit_manager
                    )
                
                cooler = self.coolers[endpoint]
                
                try:
                    self.logger.info(f"Intentando routing {protocol_label} DIRECTO a {recipient_id} en {endpoint}")
                    
                    if is_mcp:
                        result = await cooler.call(self._send_direct_mcp, endpoint, content, correlation_id)
                    else:
                        result = await cooler.call(self._send_direct_a2a, endpoint, sender_id, recipient_id, content, message_type, correlation_id)
                    
                    if self.audit_manager:
                        from ..security.auditing import AuditLevel, EventCategory
                        self.audit_manager.log_event(
                            event_type=f"{protocol_label}_P2P_ROUTING_SUCCESS",
                            level=AuditLevel.INFO,
                            category=EventCategory.ACCESS_CONTROL,
                            agent_id=sender_id,
                            correlation_id=correlation_id,
                            action=f"route_{protocol_label.lower()}",
                            result="SUCCESS",
                            details={"recipient_id": recipient_id, "endpoint": endpoint}
                        )
                    self.metrics["p2p_sent"] += 1
                    self.metrics["p2p_received"] += 1
                    return result
                except Exception as e:
                    self.metrics["p2p_errors"] += 1
                    self.logger.warning(f"Fallo routing directo {protocol_label} a {recipient_id}: {e}")
                    self.logger.warning(f"[{correlation_id}] Fallo routing directo {protocol_label} a {recipient_id}: {e}")
                    if no_hub_fallback:
                        raise e

        # 2. Fallback a MessageBus (Hub)
        if no_hub_fallback:
            raise ValueError(f"Agente destinatario '{recipient_id}' no registrado en el router A2A local o su canal directo no esta disponible.")
        return await self._send_via_hub(sender_id, recipient_id, content, message_type, correlation_id=correlation_id)

    async def _send_direct_mcp(self, endpoint: str, payload: Dict[str, Any], correlation_id: str) -> Any:
        """Envía el mensaje usando el protocolo MCP Puro (Anthropic Standard) con JWS."""
        # Propagar Correlation ID en el payload MCP
        payload["id"] = correlation_id
        
        headers = {}
        if hasattr(self.message_bus, 'security_module') and self.message_bus.security_module:
            # Propagar Correlation ID a las cabeceras JWS para trazabilidad de infraestructura
            headers = self.message_bus.security_module.get_jws_headers(payload, correlation_id=correlation_id)
            
        response = await self._http_client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def _send_direct_a2a(self, endpoint: str, sender_id: str, recipient_id: str, content: Any, message_type: MessageType, correlation_id: str) -> Any:
        """Envía el mensaje usando el protocolo A2A oficial (JSON-RPC sobre HTTP) con JWS."""
        # Formato A2A Puro: Los parámetros van en la raíz de 'params'
        params = {
            "agent_id": recipient_id,
            "sender_id": sender_id,
            "correlation_id": correlation_id,
        }
        
        if isinstance(content, dict):
            # Si el contenido ya es un dict, lo fusionamos (soporte para prompts, etc.)
            params.update(content)
        else:
            # Si es un valor simple, lo ponemos en 'input' por compatibilidad mínima
            params["input"] = content

        # Inyectar message_type DESPUÉS del merge para que no sea sobrescrito por claves del content
        params["message_type"] = message_type.value if hasattr(message_type, "value") else str(message_type)

        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/create",
            "params": params,
            "id": correlation_id
        }
        
        headers = {}
        if hasattr(self.message_bus, 'security_module') and self.message_bus.security_module:
            headers = self.message_bus.security_module.get_jws_headers(payload, correlation_id=correlation_id)
            
        response = await self._http_client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def _send_via_hub(self, sender_id: str, recipient_id: str, content: Any, message_type: MessageType, correlation_id: Optional[str] = None) -> Any:
        """Envía el mensaje a través del Hub central (via MessageBus local o HTTP remoto)."""
        self.metrics["hub_fallback"] += 1
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Localización dinámica del HUB
        hub_url = os.getenv("RAYRABBIT_HUB_URL") or os.getenv("RAYRABBIT_API_URL", "http://127.0.0.1:8005")
        
        # Si somos un nodo externo (tenemos hub_url y no es el bus local), usamos relay HTTP
        if hub_url and not self.message_bus.is_running:
            # Asegurar endpoint de publicación
            publish_endpoint = hub_url
            if not publish_endpoint.endswith("/api/publish-message"):
                publish_endpoint = f"{publish_endpoint.rstrip('/')}/api/publish-message"

            self.logger.info(f"Relay vía Hub REMOTO ({publish_endpoint}) para {recipient_id}")
            
            # Formato PublishMessagePayload (FastAPI Hub compatible)
            payload = {
                "sender_id": sender_id,
                "sender_name": f"A2A Router ({sender_id})",
                "recipient_id": recipient_id,
                "message_type": message_type.value if hasattr(message_type, "value") else str(message_type),
                "correlation_id": correlation_id,
                "content": content if isinstance(content, dict) else {"input": content}
            }
            
            headers = {}
            if hasattr(self.message_bus, 'security_module') and self.message_bus.security_module:
                headers = self.message_bus.security_module.get_jws_headers(payload, correlation_id=correlation_id)

            try:
                response = await self._http_client.post(publish_endpoint, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.error(f"Fallo en relay al Hub ({response.status_code}): {response.text}")
                    return {"error": response.text, "status_code": response.status_code}
            except Exception as e:
                self.logger.error(f"Fallo crítico en el relay al Hub: {e}")
                return {"error": str(e)}

        # Fallback a bus local si estamos dentro del mismo proceso que el Hub
        self.logger.info(f"Enviando mensaje a {recipient_id} vía BUSINESS BUS (Hub local).")
        msg = Message(
            sender_id=sender_id,
            sender_name=f"A2A Router ({sender_id})",
            recipient_id=recipient_id,
            content=content,
            message_type=message_type,
            correlation_id=correlation_id
        )
        await self.message_bus.publish(msg)
        return {"status": "sent_via_bus", "correlation_id": msg.correlation_id}

    async def close(self):
        """Cierra el cliente HTTP."""
        await self._http_client.aclose()
