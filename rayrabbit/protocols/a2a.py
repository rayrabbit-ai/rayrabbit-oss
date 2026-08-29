from __future__ import annotations

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
Protocolo A2A (Agent-to-Agent) - Implementación completa para producción

Este módulo implementa el protocolo A2A para comunicación directa entre agentes,
utilizando JSON-RPC 2.0 sobre HTTP/HTTPS y se integra con el MessageBus de RayRabbit.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

import json
import datetime
import uuid

from aiohttp import web

from ..communication.message import Message, MessageType
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..core.message_bus import MessageBus

from .a2a_router import A2ARouter, AgentCard

class A2AError(Exception):
    def __init__(self, code: int, message: str, data: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(f"A2A Error {code}: {message}")

class A2ATask:
    """Representa una tarea A2A con su ciclo de vida completo."""
    def __init__(self, task_id: str, agent_id: str, input_data: Any):
        self.task_id = task_id
        self.agent_id = agent_id
        self.input = input_data
        self.status = "pending"
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        self.result: Optional[Any] = None
        self.error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "input": self.input,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

class A2AProtocol:
    """
    Gestiona la lógica del protocolo A2A, el ciclo de vida de las tareas y el formato de mensajes.
    """
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.logger = get_logger("A2AProtocol")
        self.active_tasks: Dict[str, A2ATask] = {}
        
        # Obtener audit_manager del bus si está disponible para MAESTRO compliance
        audit_manager = getattr(self.message_bus.security_module, 'audit_manager', None) if self.message_bus.security_module else None
        self.router = A2ARouter(message_bus, audit_manager=audit_manager) # Router para routing inteligente
        
        # Handler opcional para procesamiento local de tareas (Nodos de Agente)
        self.local_task_handler: Optional[Callable[[str, Any], Awaitable[Any]]] = None

    def set_task_handler(self, handler: Callable[[str, Any], Awaitable[Any]]) -> None:
        """Registra un manejador para procesar tareas localmente en este nodo."""
        self.local_task_handler = handler

    async def start(self) -> None:
        """Inicia el protocolo A2A."""
        self.logger.info("Protocolo A2A iniciado.")

    async def stop(self) -> None:
        """Detiene el protocolo A2A."""
        self.logger.info("Protocolo A2A detenido.")

    async def handle_rpc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if not isinstance(method, str):
            return self._create_error_response(request_id, -32600, "Invalid Request: method must be a string")

        handler_method = getattr(self, f"_handle_{method.replace('/', '_')}", None)
        if not handler_method:
            return self._create_error_response(request_id, -32601, "Método no encontrado")

        try:
            result = await handler_method(params)
            return self._create_success_response(request_id, result)
        except A2AError as e:
            return self._create_error_response(request_id, e.code, e.message, e.data)
        except Exception as e:
            self.logger.error(f"Error inesperado manejando el método A2A '{method}': {e}", exc_info=True)
            return self._create_error_response(request_id, -32000, "Error interno del servidor")

    async def _handle_tasks_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = params.get("agent_id")
        input_data = params.get("input")
        sender_id = params.get("sender_id", "a2a_protocol_server")
        
        if not agent_id or not input_data:
            raise A2AError(-32602, "Parámetros inválidos")
        
        task_id = str(uuid.uuid4())
        task = A2ATask(task_id, agent_id, input_data)
        self.active_tasks[task_id] = task
        
        # Soporte para procesamiento LOCAL (Nodos de Agente Autónomos)
        if self.local_task_handler:
            self.logger.info(f"Procesando tarea A2A {task_id} LOCALMENTE...")
            try:
                result_data = await self.local_task_handler(agent_id, input_data)
                task.status = "completed"
                task.result = result_data
                task.updated_at = datetime.datetime.now()
                return task.to_dict()
            except Exception as e:
                self.logger.error(f"Error en procesador local A2A: {e}")
                task.status = "failed"
                task.error = {"code": -32000, "message": str(e)}
                return task.to_dict()

        # Routing inteligente: Directo P2P > Hub Fallback
        self.logger.info(f"Enrutando tarea A2A {task_id} para el agente {agent_id}...")
        route_result = await self.router.route_message(
            sender_id=sender_id,
            recipient_id=agent_id,
            content=input_data,
            message_type=MessageType.REQUEST
        )
        
        result = task.to_dict()
        result["routing"] = route_result
        return result

    async def _handle_tasks_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("task_id")
        status = params.get("status")
        result_data = params.get("result")
        error_data = params.get("error")
        
        if not task_id:
            raise A2AError(-32602, "Parámetro inválido: se requiere task_id")
            
        task = self.active_tasks.get(task_id)
        if not task:
            raise A2AError(-32001, "Tarea no encontrada")
            
        if status:
            task.status = status
        if result_data:
            task.result = result_data
        if error_data:
            task.error = error_data
            
        task.updated_at = datetime.datetime.now()
        self.logger.info(f"Tarea A2A {task_id} actualizada a estado: {task.status}")
        return task.to_dict()

    async def _handle_tasks_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("task_id")
        if not task_id:
            raise A2AError(-32602, "Parámetro inválido: se requiere task_id")
            
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            self.logger.info(f"Tarea A2A {task_id} eliminada.")
            return {"status": "deleted", "task_id": task_id}
        else:
            raise A2AError(-32001, "Tarea no encontrada")

    async def _handle_tasks_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("task_id")
        if not task_id:
            raise A2AError(-32602, "Parámetro inválido: se requiere task_id")
        task = self.active_tasks.get(task_id)
        if not task:
            raise A2AError(-32001, "Tarea no encontrada")
        return task.to_dict()

    def _create_success_response(self, req_id: Any, result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _create_error_response(self, req_id: Any, code: int, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        error_obj = {"code": code, "message": message}
        if data:
            error_obj["data"] = data
        return {"jsonrpc": "2.0", "id": req_id, "error": error_obj}

class A2AServer:
    """
    Servidor HTTP que expone el protocolo A2A a la red.
    """
    def __init__(self, protocol: A2AProtocol, host: str, port: int):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.logger = get_logger("A2AServer")
        self.runner: Optional[web.AppRunner] = None

    async def start(self) -> None:
        app = web.Application()
        app.router.add_post("/a2a", self._handle_http_request)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        self.logger.info(f"Servidor A2A escuchando en http://{self.host}:{self.port}/a2a")

    async def stop(self) -> None:
        if self.runner:
            await self.runner.cleanup()
            self.logger.info("Servidor A2A detenido.")

    async def _handle_http_request(self, request: web.Request) -> web.Response:
        try:
            rpc_request = await request.json()
            rpc_response = await self.protocol.handle_rpc_request(rpc_request)
            return web.json_response(rpc_response)
        except json.JSONDecodeError:
            return web.json_response(self.protocol._create_error_response(None, -32700, "Error de parseo JSON"), status=400)
        except Exception as e:
            self.logger.error(f"Error fatal en el manejador HTTP de A2A: {e}", exc_info=True)
            return web.json_response(self.protocol._create_error_response(None, -32000, "Error interno del servidor"), status=500)
