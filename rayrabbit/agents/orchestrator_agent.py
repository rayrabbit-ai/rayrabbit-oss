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
Orchestrator Agent - Agente con orquestación automática de pipelines.

Combina la flexibilidad de ToolCallingAgent con la orquestación automática
de a2a_service.py, permitiendo definir pipelines de tareas que se ejecutan
automáticamente.

Este agente implementa el patrón de "workflow orchestration" donde una tarea
inicial desencadena una cadena de llamadas a herramientas de diferentes servicios.
"""
from typing import Dict, Any, List, Optional, Callable, Awaitable
import logging

from .tool_calling_agent import ToolCallingAgent
from ..core.message_bus import MessageBus

logger = logging.getLogger(__name__)


class Pipeline:
    """
    Definición de un pipeline de orquestación.
    
    Un pipeline es una secuencia de pasos donde cada paso llama a una
    herramienta MCP y el resultado se pasa al siguiente paso.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: List[Dict[str, Any]] = []
    
    def add_step(
        self,
        service_id: str,
        tool_name: str,
        arguments_extractor: Optional[Callable[[Any], Dict[str, Any]]] = None
    ):
        """
        Añade un paso al pipeline.
        
        Args:
            service_id: ID del servicio que expone la herramienta
            tool_name: Nombre de la herramienta a ejecutar
            arguments_extractor: Función que extrae argumentos del resultado previo
                                Firma: def extractor(prev_result: Any) -> Dict[str, Any]
                                Si es None, se pasa el resultado completo
        """
        self.steps.append({
            "service_id": service_id,
            "tool_name": tool_name,
            "arguments_extractor": arguments_extractor
        })
        return self  # Para encadenamiento fluido


class OrchestratorAgent(ToolCallingAgent):
    """
    Agente orquestador con capacidad de ejecutar pipelines automáticos.
    
    Extiende ToolCallingAgent añadiendo la capacidad de definir y ejecutar
    pipelines de tareas que se encadenan automáticamente.
    
    Example:
        ```python
        # Crear orquestador
        orchestrator = OrchestratorAgent(
            agent_id="orchestrator",
            name="Logistics Orchestrator"
        )
        
        # Definir pipeline logístico
        logistics_pipeline = Pipeline("logistics_flow", "Pipeline completo de logística")
        logistics_pipeline \\
            .add_step("logistics_manager", "analyze_order",
                     lambda args: {"order_id": args["order_id"], "priority": args["priority"]}) \\
            .add_step("route_optimizer", "optimize_route",
                     lambda prev: {"origin": prev.get("origin", "MAD"), "destination": prev.get("destination", "BCN")}) \\
            .add_step("fleet_commander", "assign_vehicle",
                     lambda prev: {"cargo_type": "fragile", "distance_km": prev.get("distance_km", 320)})
        
        # Registrar pipeline
        orchestrator.register_pipeline(logistics_pipeline)
        
        # Ejecutar pipeline completo con una sola llamada
        result = await orchestrator.execute_pipeline(
            "logistics_flow",
            initial_args={"order_id": "ORD-123", "priority": "high"}
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
        Inicializa el orquestador.
        
        Args:
            agent_id: Identificador único del agente
            name: Nombre legible del agente
            description: Descripción de las capacidades
            message_bus: Bus de mensajes (se inyecta desde framework)
        """
        super().__init__(agent_id, name, description, message_bus)
        self.pipelines: Dict[str, Pipeline] = {}
        logger.info(f"OrchestratorAgent '{agent_id}' initialized")
    
    async def discover_from_router(self, service_id: str) -> bool:
        """
        Descubre herramientas MCP consultando el router del framework.
        Requiere que el DiscoveryService haya registrado al agente.
        
        Args:
            service_id: ID del servicio en el router
            
        Returns:
            True si se descubrieron herramientas, False en caso contrario
        """
        if not self.message_bus or not hasattr(self.message_bus, "a2a_router"):
            logger.error("No A2A router available in message bus")
            return False
            
        router = self.message_bus.a2a_router
        card = router.get_agent_card(service_id)
        
        if not card:
            logger.warning(f"Agent card for '{service_id}' not found in router")
            return False
            
        # Buscar endpoint MCP
        mcp_endpoint = card.endpoints.get("mcp") or card.endpoints.get("mcp_tools")
        if not mcp_endpoint:
            logger.warning(f"No MCP/mcp_tools endpoint found for '{service_id}'")
            return False
            
        logger.info(f"Discovering tools for '{service_id}' via router: {mcp_endpoint}")
        return await self.discover_tools(service_id, mcp_endpoint)

    def register_pipeline(self, pipeline: Pipeline) -> None:
        """
        Registra un pipeline para ejecución automática.
        
        Args:
            pipeline: Pipeline a registrar
        """
        self.pipelines[pipeline.name] = pipeline
        logger.info(
            f"Pipeline '{pipeline.name}' registered with {len(pipeline.steps)} steps"
        )
    
    async def execute_pipeline(
        self,
        pipeline_name: str,
        initial_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta un pipeline completo automáticamente.
        
        Args:
            pipeline_name: Nombre del pipeline a ejecutar
            initial_args: Argumentos iniciales para el primer paso
            
        Returns:
            Diccionario con resultados de cada paso:
            {
                "pipeline": "logistics_flow",
                "steps": [
                    {"step": 0, "service": "...", "tool": "...", "result": "..."},
                    {"step": 1, "service": "...", "tool": "...", "result": "..."},
                    ...
                ],
                "final_result": "..."
            }
            
        Raises:
            ValueError: Si el pipeline no existe
        """
        if pipeline_name not in self.pipelines:
            raise ValueError(
                f"Pipeline '{pipeline_name}' not found. "
                f"Available: {list(self.pipelines.keys())}"
            )
        
        pipeline = self.pipelines[pipeline_name]
        
        logger.info(
            f"Executing pipeline '{pipeline_name}' with {len(pipeline.steps)} steps"
        )
        
        # Auditar inicio de pipeline
        if self.maestro and hasattr(self.message_bus, 'audit_manager'):
            audit_manager = self.message_bus.audit_manager
            if audit_manager:
                await audit_manager.log_event(
                    event_type="PIPELINE_EXECUTION_STARTED",
                    agent_id=self.id,
                    details={
                        "pipeline_name": pipeline_name,
                        "step_count": len(pipeline.steps),
                        "initial_args": initial_args
                    }
                )
        
        results = []
        current_result = initial_args
        
        try:
            for step_idx, step in enumerate(pipeline.steps):
                service_id = step["service_id"]
                tool_name = step["tool_name"]
                extractor = step["arguments_extractor"]
                
                # Extraer argumentos del resultado previo
                if extractor:
                    try:
                        arguments = extractor(current_result)
                    except Exception as e:
                        logger.error(
                            f"Error extracting arguments for step {step_idx}: {e}"
                        )
                        arguments = current_result
                else:
                    arguments = current_result if isinstance(current_result, dict) else {}
                
                logger.info(
                    f"Pipeline '{pipeline_name}' - Step {step_idx + 1}/{len(pipeline.steps)}: "
                    f"{service_id}.{tool_name}"
                )
                
                # Ejecutar herramienta
                result = await self.call_tool(
                    service_id=service_id,
                    tool_name=tool_name,
                    arguments=arguments
                )
                
                # Almacenar resultado
                step_result = {
                    "step": step_idx,
                    "service_id": service_id,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": result
                }
                results.append(step_result)
                
                # El resultado de este paso es el input del siguiente
                current_result = result
                
                logger.debug(f"Step {step_idx} completed: {str(result)[:100]}...")
            
            # Auditar éxito de pipeline
            if self.maestro and hasattr(self.message_bus, 'audit_manager'):
                audit_manager = self.message_bus.audit_manager
                if audit_manager:
                    await audit_manager.log_event(
                        event_type="PIPELINE_EXECUTION_COMPLETED",
                        agent_id=self.id,
                        details={
                            "pipeline_name": pipeline_name,
                            "steps_executed": len(results)
                        }
                    )
            
            logger.info(f"Pipeline '{pipeline_name}' completed successfully")
            
            return {
                "pipeline": pipeline_name,
                "steps": results,
                "final_result": current_result
            }
            
        except Exception as e:
            logger.exception(f"Pipeline '{pipeline_name}' failed at step {step_idx}: {e}")
            
            # Auditar fallo de pipeline
            if self.maestro and hasattr(self.message_bus, 'audit_manager'):
                audit_manager = self.message_bus.audit_manager
                if audit_manager:
                    await audit_manager.log_event(
                        event_type="PIPELINE_EXECUTION_FAILED",
                        agent_id=self.id,
                        details={
                            "pipeline_name": pipeline_name,
                            "failed_step": step_idx,
                            "error": str(e)
                        }
                    )
            
            raise
    
    def get_pipelines(self) -> List[str]:
        """
        Obtiene lista de pipelines registrados.
        
        Returns:
            Lista de nombres de pipelines
        """
        return list(self.pipelines.keys())
