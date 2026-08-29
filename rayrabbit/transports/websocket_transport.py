"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import websockets
from websockets.exceptions import ConnectionClosed
from websockets.typing import Data
import asyncio
import json
import logging
from typing import Callable, Optional, Any, Dict
from ..communication.message import Message, MessageType
from ..utils.logger import get_logger

class WebSocketTransport:
    """
    Transporte basado en WebSockets para comunicación MCP.
    Permite el envío y recepción de mensajes JSON-RPC.
    """
    
    def __init__(self, uri: str, message_handler: Callable[[Message], None]):
        self.uri = uri
        self.message_handler = message_handler
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self.logger = get_logger(f"WebSocketTransport_{uri}")
        self._receive_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Inicia la conexión WebSocket y el loop de recepción."""
        if self.is_running:
            return
        
        try:
            self.logger.info(f"Conectando a {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.is_running = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            self.logger.info(f"Conexión establecida con {self.uri}")
        except Exception as e:
            self.logger.error(f"Error al conectar a {self.uri}: {e}")
            raise

    async def stop(self) -> None:
        """Cierra la conexión y detiene el loop."""
        self.is_running = False
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.logger.info(f"Transporte para {self.uri} detenido.")

    async def send(self, message: Message, endpoint: Optional[str] = None) -> bool:
        """Envía un mensaje a través del WebSocket."""
        if not self.websocket or not self.is_running:
            self.logger.error("No se puede enviar mensaje: WebSocket no conectado.")
            return False
        
        try:
            # MCP siempre usa el contenido como el payload JSON-RPC
            payload = message.content
            if not isinstance(payload, dict):
                 # Si no es un dict, lo envolvemos (aunque Message.content debería serlo para MCP)
                 payload = {"data": payload}
            
            await self.websocket.send(json.dumps(payload))
            return True
        except Exception as e:
            self.logger.error(f"Error al enviar mensaje a {self.uri}: {e}")
            return False

    async def _receive_loop(self) -> None:
        """Loop infinito para recibir mensajes."""
        while self.is_running and self.websocket:
            try:
                data = await self.websocket.recv()
                if not data:
                    continue
                
                payload = json.loads(data)
                
                # Convertimos el payload JSON-RPC a un objeto Message de RayRabbit
                msg = Message(
                    sender_id="mcp_server",
                    sender_name="mcp_server",
                    recipient_id="mcp_client",
                    content=payload,
                    message_type=MessageType.RESPONSE if "id" in payload else MessageType.NOTIFICATION
                )
                
                self.message_handler(msg)
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(f"Conexión cerrada por el servidor en {self.uri}")
                self.is_running = False
                break
            except Exception as e:
                self.logger.error(f"Error en loop de recepción de {self.uri}: {e}")
                if self.is_running:
                    await asyncio.sleep(1) # Reintentar después de un error
