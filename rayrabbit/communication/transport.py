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
Módulo Transport - Capas de transporte para RayRabbit

Implementa diferentes mecanismos de transporte para la comunicación entre agentes.
"""

import asyncio
import json
import aiohttp
import httpx
import websockets
from websockets.exceptions import ConnectionClosed
from aiohttp import web
import logging
from typing import Dict, Optional, Callable, List, Any, TYPE_CHECKING
from abc import ABC, abstractmethod

from .message import Message, MessageType
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from websockets.asyncio.server import ServerConnection


class BaseTransport(ABC):
    """Clase base para todos los transportes."""
    
    def __init__(self, transport_id: Optional[str] = None) -> None:
        self.is_running = False
        self.logger = get_logger(f"Transport.{transport_id or self.__class__.__name__}")
        
    @abstractmethod
    async def start(self) -> None:
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        pass
        
    @abstractmethod
    async def send(self, message: Message, endpoint: str) -> bool:
        pass

    def set_message_handler(self, handler: Callable[..., Any]) -> None:
        """Establece el manejador de mensajes para el transporte."""
        # Las implementaciones concretas deben sobrescribir esto si necesitan un handler.
        pass

class HTTPTransport(BaseTransport):
    """
    Transporte HTTP bidireccional para comunicación entre agentes.
    Puede actuar como cliente (para enviar) y como servidor (para recibir).
    """
    
    def __init__(self, 
                 host: Optional[str] = None, 
                 port: Optional[int] = None, 
                 message_handler: Optional[Callable] = None, 
                 timeout: float = 30.0) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.server: Optional[web.AppRunner] = None
        
    async def start(self) -> None:
        if self.is_running:
            return
        
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        
        if self.host and self.port and self.message_handler:
            app = web.Application()
            app.router.add_post("/message", self._handle_http_request)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            self.server = runner
            self.logger.info(f"Servidor de transporte HTTP escuchando en http://{self.host}:{self.port}/message")

        self.is_running = True
        self.logger.info("Transporte HTTP iniciado.")
        
    async def stop(self) -> None:
        if not self.is_running:
            return
        if self.session:
            await self.session.close()
        if self.server:
            await self.server.cleanup()
        self.is_running = False
        self.logger.info("Transporte HTTP detenido.")
        
    async def send(self, message: Message, endpoint: str) -> bool:
        if not self.session:
            raise RuntimeError("Transporte HTTP no iniciado para enviar.")
        try:
            async with self.session.post(endpoint, json=message.to_dict()) as response:
                is_successful: bool = (response.status == 200)
                return is_successful
        except Exception as e:
            self.logger.error(f"Error enviando mensaje a {endpoint}: {e}")
            return False

    async def _handle_http_request(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            message = Message.from_dict(data)
            if self.message_handler:
                asyncio.create_task(self.message_handler(message))
                return web.Response(status=202)
            return web.Response(status=404, text="No message handler configured")
        except Exception as e:
            self.logger.error(f"Error procesando solicitud HTTP entrante: {e}")
            return web.Response(status=500)

class HTTPClientTransport(BaseTransport):
    """
    Transporte HTTP de solo cliente para enviar mensajes usando httpx.
    Ideal para scripts que solo necesitan publicar mensajes a un endpoint HTTP.
    """
    def __init__(self, timeout: float = 30.0, security_manager: Any = None) -> None:
        super().__init__()
        self.client: Optional[httpx.AsyncClient] = None
        self.timeout = timeout
        self.security = security_manager

    async def start(self) -> None:
        if self.is_running:
            return
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.is_running = True
        self.logger.info("Transporte HTTP de cliente iniciado.")

    async def stop(self) -> None:
        if not self.is_running:
            return
        if self.client:
            await self.client.aclose()
        self.is_running = False
        self.logger.info("Transporte HTTP de cliente detenido.")

    async def send(self, message: Message, endpoint: str, headers: Optional[Dict[str, str]] = None) -> bool:
        if not self.client:
            raise RuntimeError("Transporte HTTP de cliente no iniciado para enviar.")
        
        request_headers = headers or {}
        payload = message.to_dict()
        
        try:
            response = await self.client.post(endpoint, json=payload, headers=request_headers)
            response.raise_for_status()
            return response.status_code in [200, 202, 204]
        except Exception as e:
            self.logger.error(f"Error inesperado en transporte POST: {e}")
            return False

    async def send_get_request(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Realiza una petición GET agnóstica de forma OO."""
        if not self.client:
            raise RuntimeError("Transporte HTTP no iniciado.")
        try:
            response = await self.client.get(endpoint, headers=headers or {})
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"Error enviando petición GET a {endpoint}: {e}")
            return None

class WebSocketTransport:
    """
    Transporte WebSocket para comunicación en tiempo real.
    """
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 8765,
                 message_handler: Optional[Callable] = None) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.server: Optional[websockets.Server] = None
        self.connections: Dict[str, 'ServerConnection'] = {}
        self.message_handler = message_handler
        self.message_handlers: List[Callable] = []
        
    async def start(self) -> None:
        if self.is_running:
            return
        try:
            self.server = await websockets.serve(self._handle_connection, self.host, self.port)
            self.is_running = True
            self.logger.info(f"Servidor WebSocket iniciado en ws://{self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Error iniciando servidor WebSocket: {e}")
            raise
            
    async def stop(self) -> None:
        if not self.is_running:
            return
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for connection in self.connections.values():
            await connection.close()
        self.connections.clear()
        self.is_running = False
        self.logger.info("Servidor WebSocket detenido")
                
    async def _handle_connection(self, websocket: 'ServerConnection') -> None:
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.connections[client_id] = websocket
        self.logger.info(f"Nueva conexión WebSocket: {client_id}")
        try:
            async for message_data in websocket:
                try:
                    json_data = message_data.decode('utf-8') if isinstance(message_data, bytes) else message_data
                    message = Message.from_json(json_data)
                    # Usa el message_handler principal si está disponible
                    if self.message_handler:
                        await self.message_handler(message, websocket)
                    # También llama a los handlers adicionales
                    for handler in self.message_handlers:
                        await handler(message, websocket)
                except Exception as e:
                    self.logger.error(f"Error procesando mensaje de {client_id}: {e}")
        finally:
            if client_id in self.connections:
                del self.connections[client_id]
                
    async def send(self, message: Message, endpoint: str) -> bool:
        websocket = self.connections.get(endpoint)
        if not websocket:
            return False
        try:
            await websocket.send(message.to_json())
            return True
        except ConnectionClosed:
            if endpoint in self.connections:
                del self.connections[endpoint]
            return False

    def add_message_handler(self, handler: Callable) -> None:
        self.message_handlers.append(handler)

class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, logger: logging.Logger, message_handler: Optional[Callable]) -> None:
        self.logger = logger
        self.message_handler = message_handler

    def error_received(self, exc: Exception) -> None:
        self.logger.error(f"Error en el transporte UDP: {exc}")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            message = Message.from_json(data.decode('utf-8'))
            self.logger.debug(f"Mensaje UDP recibido de {addr}: {message}")
            # Verifica que message_handler no sea None antes de llamarlo
            if self.message_handler is not None:
                asyncio.create_task(self.message_handler(message, addr))
            else:
                self.logger.warning(f"Mensaje UDP recibido de {addr} pero no hay handler configurado")
        except Exception as e:
            self.logger.error(f"Error procesando datagrama UDP de {addr}: {e}")

class UDPTransport(BaseTransport):
    """
    Transporte UDP para comunicación de baja latencia.
    """
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 8766, 
                 message_handler: Optional[Callable] = None) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self.transport: Optional[asyncio.DatagramTransport] = None

    async def start(self) -> None:
        if self.is_running:
            return
        loop = asyncio.get_running_loop()
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: UDPProtocol(self.logger, self.message_handler),
            local_addr=(self.host, self.port)
        )
        self.is_running = True
        self.logger.info(f"Transporte UDP iniciado en {self.host}:{self.port}")

    async def stop(self) -> None:
        if self.transport:
            self.transport.close()
        self.is_running = False

    async def send(self, message: Message, endpoint: str) -> bool:
        if not self.transport:
            return False
        host, port_str = endpoint.split(':')
        self.transport.sendto(message.to_json().encode('utf-8'), (host, int(port_str)))
        return True

class SSETransport(BaseTransport):
    """
    Transporte para Server-Sent Events (SSE).
    Actúa como un cliente que se suscribe a un stream de eventos.
    La recepción es asíncrona a través de un listener, y el envío es vía HTTP POST.
    """
    def __init__(self, 
                 uri: str,
                 message_handler: Callable[[Message], None], # <-- Tipo de handler cambiado
                 headers: Optional[Dict[str, str]] = None,
                 timeout: float = 30.0) -> None:
        super().__init__(transport_id=f"SSEClient_for_{uri}")
        self.uri = uri
        self.message_handler = message_handler
        self.headers = headers or {}
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        self._listener_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self.is_running:
            return
        
        self.client = httpx.AsyncClient(timeout=self.timeout, headers=self.headers)
        self._listener_task = asyncio.create_task(self._sse_listener())
        self.is_running = True
        self.logger.info(f"Transporte SSE iniciado y escuchando en {self.uri}")

    async def stop(self) -> None:
        if not self.is_running:
            return
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self.client:
            await self.client.aclose()
        self.is_running = False
        self.logger.info("Transporte SSE detenido.")

    async def _sse_listener(self) -> None:
        if not self.client:
            return
        try:
            async with self.client.stream("GET", self.uri) as response:
                response.raise_for_status()
                self.logger.info(f"Conexión SSE establecida con {self.uri}")
                async for line in response.aiter_lines():
                    if line.startswith('data:'):
                        data_str = line[len('data:'):].strip()
                        try:
                            data_dict = json.loads(data_str)
                            # Construir un objeto Message estandarizado
                            message = Message(
                                sender_id=self.uri, 
                                sender_name="SSE-Endpoint",
                                recipient_id="mcp_client", # El destinatario es el cliente que usa este transporte
                                content=data_dict, 
                                message_type=MessageType.EVENT
                            )
                            self.message_handler(message)
                        except json.JSONDecodeError:
                            self.logger.warning(f"No se pudo decodificar el evento SSE como JSON: {data_str}")
                        except Exception as e:
                            self.logger.error(f"Error en message_handler de SSE: {e}")
        except httpx.RequestError as e:
            self.logger.error(f"Error de conexión en el listener SSE: {e}")
        except asyncio.CancelledError:
            self.logger.info("Listener SSE cancelado.")
        except Exception as e:
            self.logger.error(f"Error inesperado en el listener SSE: {e}", exc_info=True)
        finally:
            self.is_running = False # Marcar como no corriendo si el listener muere

    async def send(self, message: Message, endpoint: str) -> bool:
        """Envía un mensaje vía HTTP POST al endpoint especificado."""
        if not self.client:
            raise RuntimeError("Transporte SSE (cliente httpx) no iniciado.")
        try:
            # Para SSE, el envío se realiza como una petición POST separada.
            response = await self.client.post(endpoint, json=message.to_dict())
            response.raise_for_status()
            return response.status_code in [200, 202, 204]
        except httpx.RequestError as e:
            self.logger.error(f"Error enviando mensaje (POST) a {endpoint}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error inesperado en send de SSE: {e}")
            return False