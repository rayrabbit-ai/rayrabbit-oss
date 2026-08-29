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
Módulo MessageBus - Sistema de comunicación central de RayRabbit
"""

import asyncio
from collections import defaultdict
from typing import Dict, Set, List, Optional, Callable, TYPE_CHECKING, cast, Awaitable

if TYPE_CHECKING:
    from .agent import Agent
    from ..security.maestro import MAESTROSecurity

from ..communication.message import Message, MessageType
from ..protocols.a2a import A2AProtocol
from ..protocols.mcp import MCPProtocol
from ..utils.logger import get_logger
from ..utils.config import MessageBusConfig # Importar el dataclass de configuración
from ..security.auditing import AuditManager, AuditEvent, AuditLevel, EventCategory
from ..resilience.offline_tolerance import OfflineToleranceService
from .task_engine.store import TaskStore
from .task_engine.manager import TaskManager
from pathlib import Path

class MessageBus:
    """
    Sistema de comunicación central para agentes RayRabbit.
    """
    
    def __init__(self, config: Optional[MessageBusConfig] = None, security_module: Optional['MAESTROSecurity'] = None) -> None:
        self.config = config or MessageBusConfig()
        self.instance_id: Optional[str] = self.config.instance_id
        self.security_module = security_module
        self.agents: Dict[str, 'Agent'] = {}
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.message_history: List[Message] = []
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.pending_responses: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.is_running = False
        
        self.gateway_hook: Optional[Callable[[Message], Awaitable[bool]]] = None
        
        self.a2a_protocol = A2AProtocol(self)
        self.mcp_protocol = MCPProtocol(self, security_module=self.security_module)
        
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "agents_registered": 0,
            "errors": 0
        }
        self.logger = get_logger("MessageBus")
        
        # Servicio de resiliencia (Offline Tolerance)
        self.offline_tolerance = OfflineToleranceService(self)
        
        # Motor de tareas (MCP v2)
        from .runtime_context import RuntimeContext
        store_path = RuntimeContext.get_data_dir() / "tasks.db"
        self.task_store = TaskStore(store_path)
        self.task_manager = TaskManager(self, self.task_store)

        
    async def start(self) -> None:
        self.is_running = True
        self.logger.info("MessageBus iniciado")
        await self.a2a_protocol.start()
        await self.mcp_protocol.start()
        await self.offline_tolerance.start()
        
    async def stop(self) -> None:
        self.is_running = False
        self.logger.info("MessageBus detenido")
        await self.a2a_protocol.stop()
        await self.mcp_protocol.stop()
        await self.offline_tolerance.stop()
        
    async def register_agent(self, agent: 'Agent') -> bool:
        if agent.id in self.agents and self.agents[agent.id] is not None:
            self.logger.warning(f"El agente con ID '{agent.id}' ya está registrado")
            return False
        self.agents[agent.id] = agent
        agent.set_message_bus(self)
        self.metrics["agents_registered"] += 1
        
        # Auditoría MAESTRO
        if self.security_module and self.security_module.audit_manager:
            self.security_module.audit_manager.log_event(
                level=AuditLevel.INFO,
                category=EventCategory.AGENT_ACTION,
                event_type="AGENT_REGISTERED",
                action="register",
                result="SUCCESS",
                agent_id=agent.id,
                details={"agent_name": agent.name, "capabilities": agent.capabilities}
            )

        self.logger.info(f"Agente {agent.name} ({agent.id}) registrado exitosamente")
        await self._emit_event("agent_registered", {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "capabilities": agent.capabilities
        })
        return True
        
    def subscribe(self, topic: str, agent_id: str) -> None:
        """Suscribe un agente a un topic específico."""
        if agent_id not in self.agents:
            self.logger.error(f"Intento de suscribir un agente no registrado: {agent_id}")
            return
        self.subscribers[topic].add(agent_id)
        self.logger.info(f"Agente {agent_id} suscrito al topic '{topic}'")
        
    async def publish(self, message: Message) -> bool:
        if not self.is_running:
            self.logger.error("MessageBus no está ejecutándose")
            return False
        if not message.validate():
            self.logger.error(f"Mensaje inválido: {message}")
            self.metrics["errors"] += 1
            return False
            
        # Hook de Gateway para intercepción/enrutamiento
        if self.gateway_hook:
            should_continue = await self.gateway_hook(message)
            if not should_continue:
                return True # El hook manejó el mensaje y pidió detener el procesamiento normal
                
        if self.config.enable_persistence:
            self._store_message(message)
        self.metrics["messages_sent"] += 1
        
        # Auditoría MAESTRO (solo para mensajes importantes o todos según config)
        if self.security_module and self.security_module.audit_manager:
            self.security_module.audit_manager.log_event(
                level=AuditLevel.DEBUG,
                category=EventCategory.COMMUNICATION,
                event_type="MESSAGE_PUBLISHED",
                action="publish",
                result="SUCCESS",
                agent_id=message.sender_id,
                correlation_id=message.correlation_id,
                details={
                    "recipient_id": message.recipient_id,
                    "message_type": message.message_type.value,
                    "is_broadcast": message.is_broadcast(),
                    "content": message.content # Inyectar contenido para trazabilidad total
                }
            )

        try:
            if message.is_broadcast():
                await self._handle_broadcast(message)
            else:
                await self._handle_direct_message(message)
            return True
        except ValueError as e:
            self.logger.warning(f"Aviso de enrutamiento (Offline Tolerance): {e}")
            await self.offline_tolerance.handle_publish_failure(message)
            return True
        except Exception as e:
            self.logger.error(f"Error publicando mensaje: {e}")
            self.metrics["errors"] += 1
            
            # Fallback a Offline Tolerance
            await self.offline_tolerance.handle_publish_failure(message)
            return True
            
    async def send_and_wait(self, message: Message, timeout: int = 30) -> Message:
        """
        Envía un mensaje y espera una respuesta con un correlation_id coincidente.
        """
        if not self.is_running:
            raise RuntimeError("MessageBus no está ejecutándose.")

        # El ID del mensaje saliente será el correlation_id de la respuesta esperada
        correlation_id = message.message_id
        
        # Crear una cola de respuesta para este ID de correlación
        response_queue = self.pending_responses[correlation_id]

        # Publicar el mensaje
        await self.publish(message)

        try:
            # Esperar la respuesta de la cola
            self.logger.debug(f"Esperando respuesta para correlation_id: {correlation_id}")
            response = await asyncio.wait_for(response_queue.get(), timeout=timeout)
            self.logger.debug(f"Respuesta recibida para correlation_id: {correlation_id}")
            return cast(Message, response)
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout esperando respuesta para correlation_id: {correlation_id}")
            self.metrics["errors"] += 1
            raise
        finally:
            # Limpiar la cola de respuestas pendientes
            del self.pending_responses[correlation_id]

    async def _handle_publish_direct(self, message: Message) -> bool:
        """Método interno para reintento de publicación desde resiliencia sin bucles."""
        try:
            if message.is_broadcast():
                await self._handle_broadcast(message)
            else:
                await self._handle_direct_message(message)
            return True
        except Exception:
            return False
            
    async def _handle_direct_message(self, message: Message) -> None:
        # Si este mensaje es una respuesta que alguien está esperando, ponerlo en la cola.
        if message.correlation_id and message.correlation_id in self.pending_responses:
            await self.pending_responses[message.correlation_id].put(message)
            return

        # Si el destinatario es un tópico (empieza con rr.) o está en subscribers, entregamos a todos sus suscriptores
        is_topic = message.recipient_id.startswith("rr.")
        if is_topic or message.recipient_id in self.subscribers:
            recipients = set()
            if message.recipient_id in self.subscribers:
                recipients.update(self.subscribers[message.recipient_id])
            if "*" in self.subscribers:
                recipients.update(self.subscribers["*"])
                
            if recipients:
                for agent_id in list(recipients):
                    agent = self.agents.get(agent_id)
                    if agent:
                        topic_msg = Message(
                            sender_id=message.sender_id,
                            sender_name=message.sender_name,
                            recipient_id=agent_id,
                            content=message.content,
                            message_type=message.message_type,
                            correlation_id=message.correlation_id
                        )
                        topic_msg.signature = message.signature
                        await self._deliver_message_to_agent(topic_msg, agent)
                return

        recipient_agent = self.agents.get(message.recipient_id)
        if recipient_agent is not None:
            try:
                await self._deliver_message_to_agent(message, recipient_agent)
                return
            except Exception as e:
                # Si el recipient es SovereignProxyAgent y falla (por ejemplo, porque el peer está offline),
                # lo guardamos en outbox de resiliencia
                if hasattr(recipient_agent, "__class__") and recipient_agent.__class__.__name__ == "SovereignProxyAgent":
                    self.logger.warning(f"Fallo en el ruteo directo a SovereignProxyAgent '{message.recipient_id}': {e}. Se guardará en outbox para reintento posterior.")
                    raise ValueError(f"Fallo proxy: {e}")
                    raise


        # NUEVO: Comprobar si es un agente externo/soberano registrado en el router A2A o tiene un placeholder None en agents
        is_external = False
        if message.recipient_id in self.agents and self.agents[message.recipient_id] is None:
            is_external = True
        elif hasattr(self, "a2a_protocol") and self.a2a_protocol and hasattr(self.a2a_protocol, "router") and self.a2a_protocol.router:
            if message.recipient_id in self.a2a_protocol.router.registry:
                is_external = True

        if is_external:
            self.logger.info(f"Ruteando mensaje para agente soberano '{message.recipient_id}' vía A2A...")
            try:
                # Llamamos al route_message del router con no_hub_fallback=True para evitar bucles recursivos en el Hub.
                # Si falla el envío directo P2P (por ejemplo, porque el agente externo está offline o precalentando),
                # se lanzará una excepción y la capturaremos en esta misma función para guardarlo en el outbox de resiliencia.
                a2a_result = await self.a2a_protocol.router.route_message(
                    sender_id=message.sender_id,
                    recipient_id=message.recipient_id,
                    content=message.content,
                    message_type=message.message_type,
                    correlation_id=message.correlation_id,
                    no_hub_fallback=True
                )
                if message.message_id and message.message_id in self.pending_responses:
                    resp_msg = Message(
                        sender_id=message.recipient_id,
                        sender_name=message.recipient_id,
                        recipient_id=message.sender_id,
                        message_type=MessageType.RESPONSE,
                        content=a2a_result,
                        correlation_id=message.correlation_id or message.message_id
                    )
                    await self.pending_responses[message.message_id].put(resp_msg)
                return
            except Exception as e:
                self.logger.warning(f"Fallo en el ruteo directo A2A a '{message.recipient_id}': {e}. Se guardará en outbox para reintento posterior.")
                raise ValueError(f"Fallo A2A: {e}")

        self.logger.warning(f"Destinatario '{message.recipient_id}' no encontrado como Agente. Enviando a Outbox.")
        raise ValueError(f"Agente destinatario '{message.recipient_id}' no encontrado en la infraestructura local o remota.")
        
    async def _handle_broadcast(self, message: Message) -> None:
        for agent_id in self.agents:
            if agent_id != message.sender_id:
                broadcast_msg = Message(
                    sender_id=message.sender_id,
                    sender_name=message.sender_name,
                    recipient_id=agent_id,
                    content=message.content,
                    message_type=message.message_type
                )
                await self._deliver_message_to_agent(broadcast_msg, self.agents[agent_id])
                
    async def _deliver_message_to_agent(self, message: Message, agent: 'Agent') -> None:
        try:
            self.metrics["messages_received"] += 1
            await agent.receive_message(message)
        except Exception as e:
            self.logger.error(f"Error entregando mensaje a Agente {agent.name}: {e}")
            self.metrics["errors"] += 1
            
    def _store_message(self, message: Message) -> None:
        self.message_history.append(message)
        if len(self.message_history) > self.config.max_message_history:
            self.message_history = self.message_history[-self.config.max_message_history:]
            
    async def _emit_event(self, event_type: str, data: dict) -> None:
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                self.logger.error(f"Error en manejador de evento {event_type}: {e}")

    def apply(self, decorator: Callable) -> 'MessageBus':
        """
        Aplica un decorador (middleware) al método publish del MessageBus.
        Permite inyectar lógica Enterprise (como el ThreatDetector o IncidentResponder)
        sin modificar el código fuente core OSS.
        """
    async def replay_history(self, topic: str, agent_id: str) -> None:
        """
        Recupera el historial de mensajes persistentes para el tópico seleccionado
        y los entrega de forma ordenada y controlada al agente.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            self.logger.error(f"Replay fallido: Agente '{agent_id}' no encontrado.")
            return

        self.logger.info(f"Iniciando replay controlado del tópico '{topic}' para agente '{agent_id}'...")
        for msg in list(self.message_history):
            if msg.recipient_id == topic:
                replay_msg = Message(
                    sender_id=msg.sender_id,
                    sender_name=msg.sender_name,
                    recipient_id=agent_id,
                    content=msg.content,
                    message_type=msg.message_type,
                    correlation_id=msg.correlation_id
                )
                replay_msg.signature = msg.signature
                await self._deliver_message_to_agent(replay_msg, agent)

    def apply(self, decorator: Callable) -> 'MessageBus':
        """
        Aplica un decorador (middleware) al método publish del MessageBus.
        Permite inyectar lógica Enterprise (como el ThreatDetector o IncidentResponder)
        sin modificar el código fuente core OSS.
        """
        # Hacemos un bind del método original para mantener la referencia
        original_publish = self.publish
        
        # Aplicamos el decorador. El decorador debe aceptar una corutina y retornar una corutina.
        decorated_publish = decorator(original_publish)
        
        # Reemplazamos el método publish a nivel de instancia
        self.publish = decorated_publish
        
        return self