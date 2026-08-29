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
Protocolo MCP (Model Context Protocol) - Implementación completa para producción

Este módulo implementa el protocolo MCP, incluyendo las clases de Protocolo, Servidor y Cliente,
para proporcionar contexto y herramientas a modelos de lenguaje grandes (LLMs) de forma estandarizada.
"""

import json
import asyncio
import websockets
from websockets.exceptions import ConnectionClosed
from typing import Dict, Any, Optional, List, TYPE_CHECKING, cast

from ..communication.message import Message, MessageType
from ..communication.transport import BaseTransport, WebSocketTransport, SSETransport
if TYPE_CHECKING:
    from ..core.message_bus import MessageBus
    from ..security.maestro import MAESTROSecurity
    from websockets.asyncio.server import ServerConnection

from ..utils.logger import get_logger
from ..transports.websocket_transport import WebSocketTransport
from ..transports.sse_transport import SSETransport
from .mcp_factory import MCPFactory
from ..security.auditing import AuditLevel, EventCategory
from ..version import __version__

class MCPError(Exception):
    def __init__(self, code: int, message: str, data: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(f"MCP Error {code}: {message}")

class MCPProtocol:
    """
    Gestiona la lógica del protocolo MCP, su ciclo de vida y su integración con el MessageBus.
    """
    def __init__(self, message_bus: "MessageBus", security_module: Optional['MAESTROSecurity'] = None):
        self.message_bus = message_bus
        self.security_module = security_module
        self.logger = get_logger("MCPProtocol")
        self.initialized = False
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.prompts: Dict[str, Dict[str, Any]] = {}
        # Obtener audit_manager para MAESTRO compliance
        audit_manager = getattr(self.security_module, 'audit_manager', None) if self.security_module else None
        self.mcp_factory = MCPFactory(audit_manager=audit_manager) # Factoría para herramientas dinámicas

    async def start(self) -> None:
        """Inicia el protocolo MCP."""
        self.logger.info("Protocolo MCP iniciado.")
        self.initialized = True
        self._register_builtin_tools()

    async def stop(self) -> None:
        """Detiene el protocolo MCP."""
        self.logger.info("Protocolo MCP detenido.")
        self.initialized = False

    def register_tool(self, tool_name: str, agent_id: str, schema: Dict[str, Any]) -> None:
        """Registra una herramienta y el agente que la maneja."""
        self.tools[tool_name] = {"schema": schema, "agent_id": agent_id}
        self.logger.info(f"Herramienta MCP '{tool_name}' registrada para el agente '{agent_id}'.")
    
    def _register_builtin_tools(self) -> None:
        """Registra herramientas nativas del protocolo MCP."""
        # Herramienta send_message: permite a clientes MCP enviar mensajes al bus
        send_message_schema = {
            "type": "function",
            "category": "hub_native",  # Categoría especial: handler nativo del Hub, NO se enruta por MessageBus
            "description": "Envia un mensaje a otro agente a través del MessageBus de RayRabbit",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_id": {
                        "type": "string",
                        "description": "ID del agente destinatario"
                    },
                    "content": {
                        "description": "Contenido del mensaje (objeto o texto)",
                        "anyOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ]
                    },
                    "message_type": {
                        "type": "string",
                        "enum": ["request", "response", "notification"],
                        "description": "Tipo de mensaje",
                        "default": "notification"
                    }
                },
                "required": ["recipient_id", "content"]
            }
        }
        # agent_id = "hub_native": señal para /api/execute-tool de invocar el handler directamente
        self.tools["send_message"] = {"schema": send_message_schema, "agent_id": "hub_native", "category": "hub_native"}

    async def handle_rpc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if not self.initialized and method != 'initialize':
            return self._create_error_response(request_id, -32002, "Server not initialized")

        if not isinstance(method, str):
            return self._create_error_response(request_id, -32600, "Invalid Request: method must be a string")

        handler_method = getattr(self, f"_handle_{method.replace('/', '_')}", None)
        if not handler_method:
            return self._create_error_response(request_id, -32601, f"Method not found: {method}")

        try:
            # Auditoría MAESTRO: Inicio de RPC
            if self.security_module and self.security_module.audit_manager:
                self.security_module.audit_manager.log_event(
                    level=AuditLevel.INFO,
                    category=EventCategory.COMMUNICATION,
                    event_type="MCP_RPC_REQUEST",
                    action=method,
                    result="STARTED",
                    details={"params": params, "request_id": request_id}
                )

            result = await handler_method(params)
            
            # Auditoría MAESTRO: Éxito
            if self.security_module and self.security_module.audit_manager:
                self.security_module.audit_manager.log_event(
                    level=AuditLevel.INFO,
                    category=EventCategory.COMMUNICATION,
                    event_type="MCP_RPC_SUCCESS",
                    action=method,
                    result="SUCCESS",
                    details={"request_id": request_id}
                )

            return self._create_success_response(request_id, result)
        except MCPError as e:
            # Auditoría MAESTRO: Error MCP
            if self.security_module and self.security_module.audit_manager:
                self.security_module.audit_manager.log_event(
                    level=AuditLevel.WARNING,
                    category=EventCategory.COMMUNICATION,
                    event_type="MCP_RPC_ERROR",
                    action=method,
                    result="ERROR",
                    details={"code": e.code, "message": e.message, "request_id": request_id}
                )
            return self._create_error_response(request_id, e.code, e.message, e.data)
        except Exception as e:
            self.logger.error(f"Error handling MCP method '{method}': {e}", exc_info=True)
            # Auditoría MAESTRO: Fallo Fatal
            if self.security_module and self.security_module.audit_manager:
                self.security_module.audit_manager.log_event(
                    level=AuditLevel.ERROR,
                    category=EventCategory.COMMUNICATION,
                    event_type="MCP_RPC_FATAL",
                    action=method,
                    result="CRITICAL",
                    details={"error": str(e), "request_id": request_id}
                )
            return self._create_error_response(request_id, -32000, "Internal server error")

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self.initialized = True
        client_caps = params.get("capabilities", {}) if isinstance(params, dict) else {}
        self.client_supports_tasks = "tasks" in client_caps
        
        caps = {"tools": True, "resources": True, "prompts": True}
        if self.client_supports_tasks or (hasattr(self.message_bus, "task_manager") and self.message_bus.task_manager):
            caps["tasks"] = {}
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": caps,
            "serverInfo": {
                "name": "rayrabbit-hub",
                "version": __version__
            }
        }

    async def _handle_tools_list(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        # 1. Herramientas registradas dinámicamente o nativas
        tools = [{"name": name, "description": data['schema'].get('description', ''), "input_schema": data['schema']} for name, data in self.tools.items()]
        
        # 2. Herramientas auto-generadas desde OpenAPI vía MCPFactory
        for service_id, service_data in self.mcp_factory.registered_services.items():
            for factory_tool in service_data["tools"]:
                tools.append({
                    "name": factory_tool["name"],
                    "description": factory_tool["description"],
                    "input_schema": factory_tool["inputSchema"]
                })
        return tools

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        # Si el cliente soporta tasks y el MessageBus tiene task_manager, enrutar a TaskEngine (MCP v2)
        if getattr(self, "client_supports_tasks", False) and hasattr(self.message_bus, "task_manager") and self.message_bus.task_manager:
            task_mgr = self.message_bus.task_manager
            # Validar política si existe
            if hasattr(task_mgr, "policy_engine") and task_mgr.policy_engine:
                if hasattr(task_mgr.policy_engine, "worker_allowlist") and task_mgr.policy_engine.worker_allowlist:
                    allowed = False
                    for w_id, caps in task_mgr.policy_engine.worker_allowlist.items():
                        if tool_name in caps or "tool_call" in caps or "tools" in caps:
                            allowed = True
                            break
                    if not allowed:
                        raise MCPError(-32003, f"No authorized worker found for tool '{tool_name}'")
            
            task_id = await task_mgr.create_task(
                payload={
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "params": tool_args
                }
            )
            return {"taskHandle": {"task_id": task_id, "status": "pending"}}

        # 1. Intentar ejecutar vía MCPFactory (para herramientas auto-wrapped de OpenAPI)
        try:
            factory_result = await self.mcp_factory.execute_tool(tool_name, tool_args)
            return {"content": [{"type": "json", "json": factory_result}]}
        except ValueError:
            # Si no está en la factoría, seguimos con la lógica manual/builtin
            pass

        # Handler especial para herramienta nativa send_message
        if tool_name == "send_message":
            return await self._handle_send_message(tool_args)
        
        # Handler para herramientas registradas por agentes
        tool_info = self.tools.get(tool_name)
        if not tool_info:
            raise MCPError(-32601, f"Tool '{tool_name}' not found.")

        if not self.security_module:
            raise MCPError(-32000, "Internal server error: Security module not configured for MCPProtocol.")

        agent_id = tool_info["agent_id"]
        
        # El contenido debe ser cifrado para el agente destinatario
        content_to_encrypt = {"operation": tool_name, "params": tool_args}
        encrypted_content = self.security_module.encrypt_for(
            json.dumps(content_to_encrypt).encode('utf-8'),
            agent_id
        )

        request_message = Message(
            sender_id="mcp_gateway",
            sender_name="MCP Gateway",
            recipient_id=agent_id,
            content=encrypted_content,
            message_type=MessageType.REQUEST
        )
        
        self.logger.info(f"Enviando llamada a herramienta '{tool_name}' al agente '{agent_id}' y esperando respuesta.")
        response_message = await self.message_bus.send_and_wait(request_message)

        if response_message.message_type == MessageType.ERROR:
            error_content = cast(Dict, response_message.content)
            raise MCPError(-32000, "Error from agent", error_content.get("error", "Unknown error"))

        if not isinstance(response_message.content, bytes):
            raise MCPError(-32000, "Invalid response from agent: content is not bytes.")

        # La respuesta del agente viene cifrada, necesitamos descifrarla.
        decrypted_bytes = self.security_module.decrypt_from(response_message.content)
        final_result = json.loads(decrypted_bytes.decode('utf-8'))

        # La especificación MCP espera un resultado con un campo 'content' que es una lista.
        # Adaptamos el resultado del agente a este formato.
        return {"content": [{"type": "json", "json": final_result}] }
    
    async def _handle_send_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la herramienta nativa send_message."""
        recipient_id = args.get("recipient_id")
        content = args.get("content")
        msg_type_str = args.get("message_type", "notification")
        
        if not recipient_id or not content:
            raise MCPError(-32602, "Invalid params: 'recipient_id' and 'content' are required.")
        
        # Mapear string a MessageType enum
        message_type_map = {
            "request": MessageType.REQUEST,
            "response": MessageType.RESPONSE,
            "notification": MessageType.NOTIFICATION
        }
        message_type = message_type_map.get(msg_type_str, MessageType.NOTIFICATION)
        
        # Crear y publicar mensaje
        message = Message(
            sender_id="mcp_client",
            sender_name="MCP Client",
            recipient_id=recipient_id,
            content=content,
            message_type=message_type
        )
        
        await self.message_bus.publish(message)
        self.logger.info(f"Mensaje enviado desde cliente MCP a '{recipient_id}' (tipo: {msg_type_str})")
        
        return {
            "content": [{
                "type": "text",
                "text": f"Mensaje enviado exitosamente a {recipient_id}"
            }]
        }

    async def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud resources/list del protocolo MCP."""
        return {
            "resources": [
                {
                    "uri": uri,
                    "name": data.get("name", ""),
                    "description": data.get("description", ""),
                    "mimeType": data.get("mimeType", "application/json")
                }
                for uri, data in self.resources.items()
            ]
        }

    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud resources/read del protocolo MCP."""
        uri = params.get("uri")
        if not isinstance(uri, str):
            raise MCPError(-32602, "Invalid params: 'uri' must be a string.")
        
        resource = self.resources.get(uri)
        if not resource:
            raise MCPError(-32601, f"Resource '{uri}' not found.")
            
        # Obtener el contenido del recurso (puede ser estático o dinámico)
        content_provider = resource.get("content_provider")
        if callable(content_provider):
            if asyncio.iscoroutinefunction(content_provider):
                content = await content_provider()
            else:
                content = content_provider()
        else:
            content = resource.get("content", "")
            
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": resource.get("mimeType", "application/json"),
                    "text": json.dumps(content) if isinstance(content, (dict, list)) else str(content)
                }
            ]
        }

    def register_resource(self, uri: str, name: str, description: str, content_provider: Any, mime_type: str = "application/json") -> None:
        """Registra un recurso MCP exposible."""
        self.resources[uri] = {
            "name": name,
            "description": description,
            "content_provider": content_provider,
            "mimeType": mime_type
        }
        self.logger.info(f"Recurso MCP registrado: {uri}")

    async def _handle_tasks_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud tasks/get del protocolo MCP v2."""
        task_id = params.get("task_id")
        if not task_id:
            raise MCPError(-32602, "Missing task_id")
        if not hasattr(self.message_bus, "task_manager") or not self.message_bus.task_manager:
            raise MCPError(-32000, "TaskManager not available")
        state = await self.message_bus.task_manager.store.get_task_state(task_id)
        if not state:
            raise MCPError(-32004, f"Task {task_id} not found")
        return state

    async def _handle_tasks_list(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Maneja la solicitud tasks/list del protocolo MCP v2."""
        tenant_id = params.get("tenant_id", "default")
        if not hasattr(self.message_bus, "task_manager") or not self.message_bus.task_manager:
            return []
        tasks = await self.message_bus.task_manager.store.list_tasks(tenant_id)
        return tasks

    async def _handle_tasks_cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud tasks/cancel del protocolo MCP v2."""
        task_id = params.get("task_id")
        actor_id = params.get("actor_id", "mcp_client")
        if not task_id:
            raise MCPError(-32602, "Missing task_id")
        if not hasattr(self.message_bus, "task_manager") or not self.message_bus.task_manager:
            raise MCPError(-32000, "TaskManager not available")
        ok = await self.message_bus.task_manager.cancel_task(task_id, actor_id=actor_id)
        return {"status": "cancelled" if ok else "failed", "task_id": task_id}

    async def _handle_tasks_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud tasks/update (resume HITL) del protocolo MCP v2."""
        task_id = params.get("task_id")
        user_input = params.get("user_input")
        actor_id = params.get("actor_id", "mcp_client")
        if not task_id:
            raise MCPError(-32602, "Missing task_id")
        if not hasattr(self.message_bus, "task_manager") or not self.message_bus.task_manager:
            raise MCPError(-32000, "TaskManager not available")
        ok = await self.message_bus.task_manager.resume_task(task_id, user_input=user_input, actor_id=actor_id)
        return {"status": "resumed" if ok else "failed", "task_id": task_id}

    def _create_success_response(self, req_id: Any, result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _create_error_response(self, req_id: Any, code: int, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        error_obj = {"code": code, "message": message}
        if data:
            error_obj["data"] = data
        return {"jsonrpc": "2.0", "id": req_id, "error": error_obj}

class MCPServer:
    """Servidor WebSocket que expone el protocolo MCP."""
    def __init__(self, protocol: MCPProtocol, host: str, port: int):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.logger = get_logger("MCPServer")
        self.server: Optional[websockets.Server] = None

    async def start(self) -> None:
        self.server = await websockets.serve(self._handler, self.host, self.port)
        self.logger.info(f"MCP Server listening on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("MCP Server stopped.")

    async def _handler(self, websocket: 'ServerConnection') -> None:
        self.logger.info(f"MCP client connected from {websocket.remote_address}")
        try:
            async for message in websocket:
                try:
                    request = json.loads(message)
                    response = await self.protocol.handle_rpc_request(request)
                    if response.get("id") is not None:
                        await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    error_resp = self.protocol._create_error_response(None, -32700, "Parse error")
                    await websocket.send(json.dumps(error_resp))
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}", exc_info=True)
                    error_resp = self.protocol._create_error_response(None, -32000, "Internal server error")
                    await websocket.send(json.dumps(error_resp))
        except ConnectionClosed:
            self.logger.info(f"MCP client disconnected from {websocket.remote_address}")
        except Exception as e:
            self.logger.error(f"Unexpected error in MCP handler: {e}", exc_info=True)

class MCPClient:
    """
    Cliente para conectarse a un servidor MCP de forma agnóstica al transporte.
    Soporta WebSockets y Server-Sent Events (SSE).
    """
    def __init__(self, uri: str, token: Optional[str] = None, rpc_endpoint: Optional[str] = None):
        self.uri = uri
        self.token = token
        self.rpc_endpoint = rpc_endpoint or uri # Endpoint explícito para RPC calls
        self.logger = get_logger(f"MCPClient_for_{self.uri!r}")
        self.request_id_counter = 0
        self._transport: Any = None
        self._pending_requests: Dict[int, asyncio.Future] = {}

        # Strategy Pattern: Seleccionar el transporte basado en la URI
        if self.uri.startswith("wss://") or self.uri.startswith("ws://"):
            self._transport = WebSocketTransport(uri=self.uri, message_handler=self._handle_mcp_message)
        elif self.uri.startswith("https://") or self.uri.startswith("http://"):
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._transport = SSETransport(uri=self.uri, message_handler=self._handle_mcp_message, headers=headers)
        else:
            raise ValueError(f"Unsupported URI scheme: {self.uri}")

    def _handle_mcp_message(self, message: Message) -> None:
        """Callback para procesar mensajes recibidos del transporte."""
        if not isinstance(message.content, dict):
            self.logger.warning(f"Received message with non-dict content: {message.content!r}")
            return

        response_data = message.content
        try:
            req_id = response_data.get("id")
            if req_id is not None and req_id in self._pending_requests:
                future = self._pending_requests.pop(int(req_id))
                if "error" in response_data:
                    error = response_data["error"]
                    future.set_exception(MCPError(error.get("code"), error.get("message"), error.get("data")))
                else:
                    future.set_result(response_data.get("result"))
            else:
                self.logger.info(f"Received un-correlated message or notification: {response_data}")
        except (KeyError, TypeError, ValueError) as e:
            self.logger.error(f"Error processing message from transport: {e} - Data: {response_data}", exc_info=True)

    async def connect(self) -> Optional[Dict[str, Any]]:
        if not self._transport:
            raise ConnectionError("Transport not initialized.")
        try:
            await self._transport.start()
            self.logger.info(f"Transport started for MCP Server at {self.uri}")
            return await self.call("initialize", {"protocolVersion": "2025-06-18"})
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP Server at {self.uri}: {e}")
            if self._transport:
                await self._transport.stop()
            raise

    async def disconnect(self) -> None:
        if self._transport:
            await self._transport.stop()
            self.logger.info("Disconnected from MCP Server.")

    async def call(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        if not self._transport or not self._transport.is_running:
            raise ConnectionError("Not connected to MCP server.")
        
        self.request_id_counter += 1
        req_id = self.request_id_counter
        
        request_content = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": req_id
        }
        request_message = Message(
            sender_id="mcp_client",
            sender_name="MCPClient",
            recipient_id=self.rpc_endpoint, # El destinatario es el endpoint RPC
            content=request_content,
            message_type=MessageType.REQUEST
        )

        future: asyncio.Future[Dict[str, Any]] = asyncio.Future()
        self._pending_requests[req_id] = future

        try:
            success = await self._transport.send(request_message, endpoint=self.rpc_endpoint)
            if not success:
                future.set_exception(ConnectionError("Failed to send message via transport."))
            
            eff_timeout = timeout if timeout is not None else 300.0
            return await asyncio.wait_for(future, timeout=eff_timeout)
        
        except Exception as e:
            if req_id in self._pending_requests:
                self._pending_requests.pop(req_id)
            self.logger.error(f"Error during MCP call '{method}': {e}")
            raise

    # --- Métodos de Conveniencia MCP ---

    async def initialize(self) -> Dict[str, Any]:
        """Inicializa la sesión MCP con el servidor."""
        return await self.call("initialize", {
            "protocolVersion": "2024-11-05", # Última versión estable
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "rayrabbit-core",
                "version": __version__
            }
        })

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Lista las herramientas disponibles en el servidor."""
        result = await self.call("tools/list")
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invoca una herramienta en el servidor."""
        return await self.call("tools/call", {"name": name, "arguments": arguments})

    async def list_resources(self) -> List[Dict[str, Any]]:
        """Lista los recursos disponibles en el servidor."""
        result = await self.call("resources/list")
        return result.get("resources", [])

    async def read_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Lee el contenido de un recurso específico."""
        result = await self.call("resources/read", {"uri": uri})
        return result.get("contents", [])

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """Lista los prompts disponibles en el servidor."""
        result = await self.call("prompts/list")
        return result.get("prompts", [])

    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Obtiene un prompt específico del servidor."""
        return await self.call("prompts/get", {"name": name, "arguments": arguments or {}})
