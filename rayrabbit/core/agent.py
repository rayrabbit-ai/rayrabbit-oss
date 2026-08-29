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
Agente Base - Implementación completa para producción

Este módulo define la clase base Agent que proporciona la funcionalidad
fundamental para todos los agentes en el framework RayRabbit.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING, cast
from datetime import datetime
from enum import Enum

from ..communication.message import Message, MessageType
from ..utils.logger import get_logger
from ..utils.exceptions import RayRabbitError

if TYPE_CHECKING:
    from ..security.maestro import MAESTROSecurity
    from .message_bus import MessageBus


class AgentStatus(Enum):
    """Estados posibles de un agente."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PROCESSING = "processing"
    BUSY = "busy"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


class Agent:
    """
    Clase base para todos los agentes en RayRabbit.
    
    Proporciona funcionalidad fundamental como:
    - Gestión de estado y ciclo de vida
    - Procesamiento de mensajes
    - Métricas y estadísticas
    - Configuración y capacidades
    """
    
    def __init__(self, agent_id: str, name: str, description: str = ""):
        """
        Inicializa el agente base.
        
        Args:
            agent_id: Identificador único del agente
            name: Nombre del agente
            description: Descripción del agente
        """
        self.id = agent_id
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Estado del agente
        self.status = AgentStatus.INITIALIZING
        self.is_running = False
        
        # Configuración
        self.config = {
            "max_concurrent_messages": 10,
            "message_timeout": 90.0,
            "enable_metrics": True,
            "log_level": "INFO"
        }
        
        # Capacidades del agente
        self.capabilities: List[str] = []
        
        # Métricas y estadísticas
        self.metrics = {
            "messages_received": 0,
            "messages_sent": 0,
            "messages_processed": 0,
            "processing_errors": 0,
            "average_processing_time": 0.0,
            "total_processing_time": 0.0,
            "uptime_seconds": 0.0
        }
        
        # Handlers de mensajes
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # Cola de mensajes pendientes
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        
        # Semáforo para controlar concurrencia
        self.processing_semaphore = asyncio.Semaphore(int(cast(int, self.config["max_concurrent_messages"])))
        
        # Tareas asíncronas activas
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Logger
        self.logger = get_logger(f"Agent-{agent_id}")

        # Módulos inyectados por el framework
        self.maestro: Optional["MAESTROSecurity"] = None
        self.message_bus: Optional["MessageBus"] = None
        
        # Registrar handlers por defecto
        self._register_default_handlers()
        
        self.logger.info(f"Agente {name} ({agent_id}) inicializado")

    def set_message_bus(self, message_bus: "MessageBus") -> None:
        """Inyecta la dependencia del MessageBus en el agente."""
        self.message_bus = message_bus

        
    def _register_default_handlers(self) -> None:
        """Registra los handlers por defecto para tipos de mensaje."""
        self.message_handlers[MessageType.REQUEST] = self._handle_request
        self.message_handlers[MessageType.RESPONSE] = self._handle_response
        self.message_handlers[MessageType.COMMAND] = self._handle_command
        self.message_handlers[MessageType.QUERY] = self._handle_query
        self.message_handlers[MessageType.INFORM] = self._handle_inform
        self.message_handlers[MessageType.ERROR] = self._handle_error
        # self.message_handlers[MessageType.NOTIFICATION] = self._handle_notification
        
    async def start(self) -> None:
        """Inicia el agente y sus procesos."""
        if self.is_running:
            self.logger.warning("Agente ya está ejecutándose")
            return
            
        try:
            self.status = AgentStatus.IDLE
            self.is_running = True
            
            # Iniciar procesamiento de mensajes
            self.active_tasks["message_processor"] = asyncio.create_task(
                self._message_processing_loop()
            )
            
            # Iniciar actualización de métricas
            if self.config["enable_metrics"]:
                self.active_tasks["metrics_updater"] = asyncio.create_task(
                    self._metrics_update_loop()
                )
                
            self.logger.info(f"Agente {self.name} iniciado")
            
        except Exception as e:
            self.logger.error(f"Error iniciando agente: {str(e)}")
            self.status = AgentStatus.ERROR
            raise
            
    async def stop(self) -> None:
        """Detiene el agente y limpia recursos."""
        if not self.is_running:
            return
            
        self.logger.info(f"Deteniendo agente {self.name}")
        self.status = AgentStatus.SHUTTING_DOWN
        
        try:
            # Cancelar todas las tareas activas
            for task_name, task in list(self.active_tasks.items()):
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        self.logger.debug(f"Tarea {task_name} cancelada")
                        
            self.active_tasks.clear()
            
            # Procesar mensajes pendientes
            await self._process_pending_messages()
            
            # Detener el gestor de auditoría si existe (Shared Nothing)
            if self.maestro and self.maestro.audit_manager:
                await self.maestro.audit_manager.stop()
                self.logger.info(f"Gestor de auditoría para '{self.id}' detenido.")

            self.is_running = False
            self.status = AgentStatus.SHUTDOWN
            
            self.logger.info(f"Agente {self.name} detenido")
            
        except Exception as e:
            self.logger.error(f"Error deteniendo agente: {str(e)}")
            self.status = AgentStatus.ERROR
            
    async def publish_message(self, message: Message) -> None:
        """
        Publica un mensaje en el bus de mensajes, aplicando seguridad si está configurada.

        Args:
            message: Mensaje a enviar.
        """
        if not self.message_bus:
            self.logger.error("MessageBus no está configurado para este agente. No se puede enviar el mensaje.")
            raise RayRabbitError("MessageBus not configured for this agent.")

        try:
            # >>> INICIO DE LA CAPA DE SEGURIDAD AUTOMÁTICA (SALIDA) <<<
            if self.maestro and message.recipient_id != "*": # No cifrar broadcasts por ahora
                
                # 1. Obtener la representación canónica del mensaje para la firma
                canonical_data = message.to_canonical_json_bytes()

                # DEBUG: Log para comparar con la verificación
                self.logger.info(f"FIRMANDO Mensaje {message.message_id}. Data Canónica: {canonical_data.decode('utf-8', errors='replace')}")

                # 2. Firmar los datos canónicos
                signature = self.maestro.sign(canonical_data)
                message.signature = signature

                # 3. Cifrar el contenido para el destinatario (opcional, si se requiere confidencialidad además de autenticidad)
                # Por ahora, nos centramos en la firma para asegurar integridad y autenticidad.
                # Si se necesitara cifrado, se haría aquí sobre message.content
                
                self.logger.debug(f"Mensaje {message.message_id} firmado para {message.recipient_id}")

            # >>> FIN DE LA CAPA DE SEGURIDAD AUTOMÁTICA (SALIDA) <<<

            await self.message_bus.publish(message)
            
            self.metrics["messages_sent"] += 1
            self.last_activity = datetime.now()
            self.logger.debug(f"Mensaje {message.message_id} publicado en el bus para {message.recipient_id}")

        except Exception as e:
            self.logger.error(f"Error publicando mensaje {message.message_id}: {e}", exc_info=True)
            self.metrics["processing_errors"] += 1
            # Re-lanzar la excepción para que el emisor original pueda manejarla si es necesario
            raise RayRabbitError(f"Failed to publish message: {e}") from e
        
    async def receive_message(self, message: Message) -> None:
        """
        Recibe un mensaje y lo añade a la cola de procesamiento.
        
        Args:
            message: Mensaje recibido
        """
        try:
            self.metrics["messages_received"] += 1
            self.last_activity = datetime.now()
            
            # Añadir mensaje a la cola
            await self.message_queue.put(message)
            
            self.logger.debug(f"Mensaje {message.message_id} añadido a la cola")
            
        except asyncio.QueueFull:
            self.logger.error("Cola de mensajes llena, mensaje descartado")
            self.metrics["processing_errors"] += 1
            
    async def _message_processing_loop(self) -> None:
        """Bucle principal de procesamiento de mensajes."""
        while self.is_running:
            try:
                # Obtener mensaje de la cola con timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                # Procesar mensaje de forma asíncrona
                task = asyncio.create_task(self._process_message_with_semaphore(message))
                task_id = str(uuid.uuid4())
                self.active_tasks[task_id] = task
                
                # Limpiar tarea cuando termine
                task.add_done_callback(lambda t: self.active_tasks.pop(task_id, None))
                
            except asyncio.TimeoutError:
                # Timeout normal, continuar
                continue
            except Exception as e:
                self.logger.error(f"Error en bucle de procesamiento: {str(e)}")
                self.metrics["processing_errors"] += 1
                
    async def _process_message_with_semaphore(self, message: Message) -> None:
        """Procesa un mensaje usando el semáforo de concurrencia."""
        async with self.processing_semaphore:
            await self._process_message(message)

    async def _process_message(self, message: Message) -> None:
        """
        Procesa un mensaje individual, aplicando una capa de seguridad automática.
        Verifica y descifra el mensaje antes de pasarlo al handler específico.
        
        Args:
            message: Mensaje a procesar
        """
        start_time = datetime.now()
        
        try:
            self.status = AgentStatus.PROCESSING

            # >>> INICIO DE LA CAPA DE SEGURIDAD AUTOMÁTICA (ENTRADA) <<<
            if self.maestro and message.signature:
                
                # 1. Obtener la representación canónica del mensaje para la verificación
                canonical_data = message.to_canonical_json_bytes()

                # DEBUG: Log para comparar con la verificación
                # if message.signature:
                #     self.logger.info(f"FIRMA RECIBIDA (Hex): {message.signature.hex()[:50]}...")


                # 2. Verificar Firma (sincrónica)
                if not self.maestro.verify(message.signature, canonical_data, message.sender_id):
                    self.logger.error(f"FALLO DE VERIFICACIÓN DE FIRMA:")
                    self.logger.error(f"  Mensaje ID: {message.message_id}")
                    self.logger.error(f"  Remitente: {message.sender_id}")
                    self.logger.error(f"  Data Canónica: {canonical_data.decode('utf-8', errors='replace')}")
                    raise RayRabbitError(f"Firma inválida para el mensaje {message.message_id} de {message.sender_id}")
                
                self.logger.debug("Firma del mensaje verificada con éxito.")

                # 3. Descifrar si es necesario (lógica futura)
                if message.encrypted and isinstance(message.content, bytes):
                    decrypted_bytes = self.maestro.decrypt_from(message.content)
                    message.content = json.loads(decrypted_bytes.decode('utf-8'))
                    self.logger.debug("Contenido del mensaje descifrado.")

            # >>> FIN DE LA CAPA DE SEGURIDAD AUTOMÁTICA (ENTRADA) <<<

            # Obtener handler para el tipo de mensaje (soporta tanto Enum como string)
            msg_type = message.message_type
            if isinstance(msg_type, str):
                try:
                    msg_type = MessageType(msg_type)
                except ValueError:
                    pass
            handler = self.message_handlers.get(msg_type)
            
            if handler:
                # Ejecutar handler con el mensaje ya descifrado
                response = await handler(message)
                
                # La responsabilidad de cifrar y firmar la respuesta recae en el método publish_message
                if response:
                    await self.publish_message(response)
                    
            else:
                self.logger.warning(f"No hay handler para tipo de mensaje: {message.message_type}")
                
            # Actualizar métricas
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_processing_metrics(processing_time)
            
            self.metrics["messages_processed"] += 1
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje {message.message_id}: {str(e)}", exc_info=True)
            self.metrics["processing_errors"] += 1
            
            # El envío de errores también debe ser seguro
            if message.is_request():
                error_content = {
                    "error": str(e),
                    "original_message_id": message.message_id
                }
                # Crear el mensaje de error, que será asegurado por el método que lo envíe
                error_response = Message(
                    sender_id=self.id,
                    sender_name=self.name,
                    recipient_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    content=error_content,
                    correlation_id=message.message_id
                )
                # El método de envío/publicación se encargará de la seguridad
                await self.publish_message(error_response)
                
        finally:
            self.status = AgentStatus.IDLE
            
    def _update_processing_metrics(self, processing_time: float) -> None:
        """Actualiza las métricas de procesamiento."""
        self.metrics["total_processing_time"] += processing_time
        
        # Calcular tiempo promedio
        if self.metrics["messages_processed"] > 0:
            self.metrics["average_processing_time"] = (
                self.metrics["total_processing_time"] / self.metrics["messages_processed"]
            )
            
    async def _metrics_update_loop(self) -> None:
        """Bucle de actualización de métricas."""
        while self.is_running:
            try:
                # Actualizar uptime
                self.metrics["uptime_seconds"] = (
                    datetime.now() - self.created_at
                ).total_seconds()
                
                # Esperar antes de la siguiente actualización
                await asyncio.sleep(10.0)
                
            except Exception as e:
                self.logger.error(f"Error actualizando métricas: {str(e)}")
                
    async def _process_pending_messages(self) -> None:
        """Procesa mensajes pendientes en la cola."""
        processed = 0
        
        while not self.message_queue.empty() and processed < 10:
            try:
                message = self.message_queue.get_nowait()
                await self._process_message(message)
                processed += 1
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                self.logger.error(f"Error procesando mensaje pendiente: {str(e)}")
                
        if processed > 0:
            self.logger.info(f"Procesados {processed} mensajes pendientes")
            
    # Handlers por defecto (pueden ser sobrescritos por subclases)
    
    async def _handle_request(self, message: Message) -> Optional[Message]:
        """Maneja mensajes de tipo REQUEST."""
        return Message(
            sender_id=self.id,
            sender_name=self.name,
            recipient_id=message.sender_id,
            message_type=MessageType.RESPONSE,
            content={
                "status": "received",
                "message": "Request processed by base agent"
            },
            correlation_id=message.message_id
        )
        
    async def _handle_response(self, message: Message) -> Optional[Message]:
        """Maneja mensajes de tipo RESPONSE."""
        content_str = str(message.content.decode('utf-8')) if isinstance(message.content, bytes) else str(message.content)
        self.logger.debug(f"Respuesta recibida: {content_str}")
        return None
        
    async def _handle_command(self, message: Message) -> Optional[Message]:
        """Maneja mensajes de tipo COMMAND."""
        command = message.content.get("command") if isinstance(message.content, dict) else str(message.content)
        
        if command == "status":
            return Message(
                sender_id=self.id,
                sender_name=self.name,
                recipient_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                content={
                    "status": self.status.value,
                    "metrics": self.metrics.copy(),
                    "capabilities": self.capabilities.copy()
                },
                correlation_id=message.message_id
            )
        elif command == "ping":
            return Message(
                sender_id=self.id,
                sender_name=self.name,
                recipient_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                content={"pong": True, "timestamp": datetime.now().isoformat()},
                correlation_id=message.message_id
            )
        else:
            return Message(
                sender_id=self.id,
                sender_name=self.name,
                recipient_id=message.sender_id,
                message_type=MessageType.ERROR,
                content={"error": f"Unknown command: {command}"},
                correlation_id=message.message_id
            )
            
    async def _handle_query(self, message: Message) -> Optional[Message]:
        """Maneja mensajes de tipo QUERY."""
        query = message.content.get("query") if isinstance(message.content, dict) else str(message.content)
        
        return Message(
            sender_id=self.id,
            sender_name=self.name,
            recipient_id=message.sender_id,
            message_type=MessageType.RESPONSE,
            content={
                "query": query,
                "result": "Query processed by base agent"
            },
            correlation_id=message.message_id
        )
        
    async def _handle_inform(self, message: Message) -> Optional[Message]:
        """Maneja mensajes de tipo INFORM."""
        content_str = str(message.content.decode('utf-8')) if isinstance(message.content, bytes) else str(message.content)
        self.logger.info(f"Información recibida de {message.sender_id}: {content_str}")
        return None
        
    async def _handle_error(self, message: Message) -> Optional[Message]:
        """Maneja mensajes de tipo ERROR."""
        content_str = str(message.content.decode('utf-8')) if isinstance(message.content, bytes) else str(message.content)
        self.logger.error(f"Error recibido de {message.sender_id}: {content_str}")
        return None
        
    async def _handle_notification(self, message: Message) -> Optional[Message]:
        """Maneja mensajes de tipo NOTIFICATION."""
        content_str = str(message.content.decode('utf-8')) if isinstance(message.content, bytes) else str(message.content)
        self.logger.info(f"Notificación recibida de {message.sender_id}: {content_str}")
        return None
        
    # Métodos de utilidad
    
    def add_capability(self, capability: str) -> None:
        """Añade una capacidad al agente."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.logger.info(f"Capacidad añadida: {capability}")
            
    def remove_capability(self, capability: str) -> None:
        """Elimina una capacidad del agente."""
        if capability in self.capabilities:
            self.capabilities.remove(capability)
            self.logger.info(f"Capacidad eliminada: {capability}")
            
    def has_capability(self, capability: str) -> bool:
        """Verifica si el agente tiene una capacidad específica."""
        return capability in self.capabilities
        
    def register_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """
        Registra un handler personalizado para un tipo de mensaje.
        
        Args:
            message_type: Tipo de mensaje
            handler: Función handler asíncrona
        """
        self.message_handlers[message_type] = handler
        self.logger.info(f"Handler registrado para tipo: {message_type}")
        
    def configure(self, **kwargs: Any) -> None:
        """
        Configura el agente.
        
        Args:
            **kwargs: Opciones de configuración
        """
        for key, value in kwargs.items():
            if key in self.config:
                old_value = self.config[key]
                self.config[key] = value
                self.logger.info(f"Configuración actualizada: {key} = {value} (anterior: {old_value})")
            else:
                self.logger.warning(f"Opción de configuración desconocida: {key}")
                
    async def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas del agente.
        
        Returns:
            Diccionario con estadísticas del agente
        """
        return {
            "agent_id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "is_running": self.is_running,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "capabilities": self.capabilities.copy(),
            "metrics": self.metrics.copy(),
            "config": self.config.copy(),
            "active_tasks_count": len(self.active_tasks),
            "queue_size": self.message_queue.qsize()
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Realiza una verificación de salud del agente.
        
        Returns:
            Estado de salud del agente
        """
        health_status = "healthy"
        issues = []
        
        # Verificar estado
        if self.status == AgentStatus.ERROR:
            health_status = "unhealthy"
            issues.append("Agent in error state")
            
        # Verificar actividad reciente
        time_since_activity = (datetime.now() - self.last_activity).total_seconds()
        if time_since_activity > 300:  # 5 minutos
            health_status = "warning"
            issues.append("No recent activity")
            
        # Verificar cola de mensajes
        if self.message_queue.qsize() > 50:
            health_status = "warning"
            issues.append("Message queue is getting full")
            
        # Verificar errores de procesamiento
        if self.metrics["processing_errors"] > 10:
            health_status = "warning"
            issues.append("High number of processing errors")
            
        return {
            "status": health_status,
            "issues": issues,
            "uptime_seconds": self.metrics["uptime_seconds"],
            "last_activity": self.last_activity.isoformat()
        }
        
    def __str__(self) -> str:
        """Representación en string del agente."""
        return f"Agent(id={self.id}, name={self.name}, status={self.status.value})"
        
    def __repr__(self) -> str:
        """Representación detallada del agente."""
        return (f"Agent(id={self.id}, name={self.name}, status={self.status.value}, "
                f"capabilities={len(self.capabilities)}, running={self.is_running})")