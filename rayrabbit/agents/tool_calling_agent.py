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
Tool Calling Agent - Agente con capacidad de descubrir y ejecutar herramientas MCP.

Permite que agentes del core de RayRabbit utilicen herramientas expuestas por
servicios externos vía MCP, manteniendo el agnosticismo del framework.

Este agente implementa el patrón de tool calling bidireccional, donde el core
puede consumir capacidades de servicios externos sin conocer su implementación.
"""
from typing import Dict, Any, List, Optional
import httpx
import logging

from ..core.agent import Agent
from ..core.message_bus import MessageBus
from ..protocols.mcp_fastapi import MCPTool, MCPToolCallRequest

logger = logging.getLogger(__name__)


class ToolCallingAgent(Agent):
    """
    Agente con capacidad de tool calling vía MCP.
    
    Puede descubrir herramientas de servicios externos y ejecutarlas de forma
    transparente, manteniendo el agnosticismo del framework RayRabbit.
    
    Example:
        ```python
        # Crear agente con capacidad de tool calling
        agent = ToolCallingAgent(
            agent_id="orchestrator",
            name="Orchestrator Agent",
            description="Coordina múltiples servicios"
        )
        
        # Registrar en el framework
        await framework.register_agent(agent)
        
        # Descubrir herramientas de un servicio
        await agent.discover_tools(
            service_id="logistics_manager",
            mcp_endpoint="http://127.0.0.1:8002"
        )
        
        # Ejecutar herramienta
        result = await agent.call_tool(
            service_id="logistics_manager",
            tool_name="analyze_order",
            arguments={"order_id": "ORD-123", "priority": "high"}
        )
        ```
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        message_bus: Optional[MessageBus] = None
    ):
        """
        Inicializa el agente con capacidad de tool calling.
        
        Args:
            agent_id: Identificador único del agente
            name: Nombre legible del agente
            description: Descripción de las capacidades del agente
            message_bus: Bus de mensajes (se inyecta desde framework)
        """
        super().__init__(agent_id, name, description)
        if message_bus:
            self.set_message_bus(message_bus)
        
        self.available_tools: Dict[str, List[MCPTool]] = {}
        self.service_endpoints: Dict[str, str] = {}
        self.http_client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"ToolCallingAgent '{agent_id}' initialized")
    
    async def start(self) -> None:
        """Inicia el agente y el cliente HTTP."""
        await super().start()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"ToolCallingAgent '{self.id}' started with HTTP client")
    
    async def stop(self) -> None:
        """Detiene el agente y cierra el cliente HTTP."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        await super().stop()
        logger.info(f"ToolCallingAgent '{self.id}' stopped")
    
    async def discover_tools(
        self,
        service_id: str,
        mcp_endpoint: str
    ) -> List[MCPTool]:
        """
        Descubre herramientas disponibles en un servicio externo.
        
        Args:
            service_id: ID del servicio (debe coincidir con NODOS.md)
            mcp_endpoint: URL base del servicio (ej: http://127.0.0.1:8002)
            
        Returns:
            Lista de herramientas MCP disponibles
            
        Raises:
            httpx.HTTPError: Si falla la comunicación con el servicio
        """
        if not self.http_client:
            raise RuntimeError("Agent not started. Call start() first.")
        
        tools_url = f"{mcp_endpoint.rstrip('/')}/mcp/tools"
        
        logger.info(f"Discovering MCP tools from {service_id} at {tools_url}")
        
        try:
            response = await self.http_client.get(tools_url)
            response.raise_for_status()
            
            tools_data = response.json()
            tools = [MCPTool(**tool) for tool in tools_data.get("tools", [])]
            
            # Almacenar herramientas y endpoint
            self.available_tools[service_id] = tools
            self.service_endpoints[service_id] = mcp_endpoint
            
            logger.info(
                f"Discovered {len(tools)} tools from {service_id}: "
                f"{[t.name for t in tools]}"
            )
            
            # Auditar descubrimiento si MAESTRO está disponible
            if self.maestro and hasattr(self.message_bus, 'audit_manager'):
                audit_manager = self.message_bus.audit_manager
                if audit_manager:
                    await audit_manager.log_event(
                        event_type="TOOL_DISCOVERY_COMPLETED",
                        agent_id=self.id,
                        details={
                            "service_id": service_id,
                            "tool_count": len(tools),
                            "tool_names": [t.name for t in tools]
                        }
                    )
            
            return tools
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to discover tools from {service_id}: {e}")
            raise
    
    async def call_tool(
        self,
        service_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Ejecuta una herramienta en un servicio externo.
        
        Args:
            service_id: ID del servicio
            tool_name: Nombre de la herramienta
            arguments: Argumentos de la herramienta
            
        Returns:
            Resultado de la ejecución de la herramienta
            
        Raises:
            ValueError: Si el servicio no ha sido descubierto
            httpx.HTTPError: Si falla la comunicación
        """
        if not self.http_client:
            raise RuntimeError("Agent not started. Call start() first.")
        
        if service_id not in self.available_tools:
            raise ValueError(
                f"Service '{service_id}' not discovered. "
                f"Call discover_tools() first."
            )
        
        # Verificar que la herramienta existe
        tool_exists = any(
            t.name == tool_name for t in self.available_tools[service_id]
        )
        if not tool_exists:
            available = [t.name for t in self.available_tools[service_id]]
            raise ValueError(
                f"Tool '{tool_name}' not found in {service_id}. "
                f"Available: {available}"
            )
        
        mcp_endpoint = self.service_endpoints[service_id]
        call_url = f"{mcp_endpoint.rstrip('/')}/mcp/call"
        
        logger.info(
            f"Calling tool '{tool_name}' on {service_id} "
            f"with args: {arguments}"
        )
        
        # Auditar inicio de llamada
        if self.maestro and hasattr(self.message_bus, 'audit_manager'):
            audit_manager = self.message_bus.audit_manager
            if audit_manager:
                await audit_manager.log_event(
                    event_type="TOOL_CALL_INITIATED",
                    agent_id=self.id,
                    details={
                        "service_id": service_id,
                        "tool_name": tool_name,
                        "arguments": arguments
                    }
                )
        
        try:
            # Crear solicitud MCP
            request_data = {
                "name": tool_name,
                "arguments": arguments
            }
            
            response = await self.http_client.post(call_url, json=request_data)
            response.raise_for_status()
            
            result_data = response.json()
            
            # Extraer resultado del formato MCP
            content = result_data.get("content", [])
            if content and len(content) > 0:
                result = content[0].get("text", "")
            else:
                result = result_data
            
            # Verificar firma si existe
            signature = result_data.get("signature")
            if signature and self.maestro:
                logger.debug(f"Tool result has signature: {signature[:16]}...")
                # TODO: Implementar verificación de firma
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            
            # Auditar éxito
            if self.maestro and hasattr(self.message_bus, 'audit_manager'):
                audit_manager = self.message_bus.audit_manager
                if audit_manager:
                    await audit_manager.log_event(
                        event_type="TOOL_CALL_COMPLETED",
                        agent_id=self.id,
                        details={
                            "service_id": service_id,
                            "tool_name": tool_name,
                            "has_signature": signature is not None
                        }
                    )
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to call tool '{tool_name}': {e}")
            
            # Auditar error
            if self.maestro and hasattr(self.message_bus, 'audit_manager'):
                audit_manager = self.message_bus.audit_manager
                if audit_manager:
                    await audit_manager.log_event(
                        event_type="TOOL_CALL_FAILED",
                        agent_id=self.id,
                        details={
                            "service_id": service_id,
                            "tool_name": tool_name,
                            "error": str(e)
                        }
                    )
            
            raise
    
    def get_available_tools(self, service_id: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Obtiene lista de herramientas disponibles.
        
        Args:
            service_id: ID del servicio (opcional, si None retorna todos)
            
        Returns:
            Diccionario {service_id: [tool_names]}
        """
        if service_id:
            if service_id not in self.available_tools:
                return {}
            return {
                service_id: [t.name for t in self.available_tools[service_id]]
            }
        
        return {
            sid: [t.name for t in tools]
            for sid, tools in self.available_tools.items()
        }
