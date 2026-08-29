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
import json
import logging
import aiohttp
from typing import Callable, Optional, Dict, Any
from ..communication.message import Message, MessageType
from ..utils.logger import get_logger

class SSETransport:
    """
    Transporte basado en Server-Sent Events (SSE) para comunicación MCP.
    Utiliza HTTP POST para enviar y SSE para recibir.
    """
    
    def __init__(self, uri: str, message_handler: Callable[[Message], None], headers: Optional[Dict[str, str]] = None):
        self.uri = uri # URL para el stream de eventos
        self.message_handler = message_handler
        self.headers = headers or {}
        self.is_running = False
        self.logger = get_logger(f"SSETransport_{uri}")
        self._session: Optional[aiohttp.ClientSession] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._post_url: Optional[str] = None # URL del endpoint RPC (se obtiene del servidor MCP)

    async def start(self) -> None:
        """Inicia la sesión SSE y el loop de recepción."""
        if self.is_running:
            return
        
        self._session = aiohttp.ClientSession(headers=self.headers)
        self.is_running = True
        self._receive_task = asyncio.create_task(self._receive_loop())
        self.logger.info(f"Transporte SSE iniciado para {self.uri}")

    async def stop(self) -> None:
        """Detiene el transporte."""
        self.is_running = False
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self.logger.info(f"Transporte SSE para {self.uri} detenido.")

    async def send(self, message: Message, endpoint: Optional[str] = None) -> bool:
        """Envía un mensaje vía HTTP POST al endpoint RPC."""
        if not self.is_running or not self._session:
            self.logger.error("No se puede enviar mensaje: SSETransport no iniciado.")
            return False
        
        url = endpoint or self._post_url
        if not url:
            self.logger.error("No hay endpoint RPC configurado para enviar el mensaje.")
            return False
        
        try:
            async with self._session.post(url, json=message.content) as response:
                if response.status >= 400:
                    text = await response.text()
                    self.logger.error(f"Error al enviar mensaje a {url}: {response.status} - {text}")
                    return False
                return True
        except Exception as e:
            self.logger.error(f"Error al enviar mensaje HTTP POST a {url}: {e}")
            return False

    async def _receive_loop(self) -> None:
        """Loop para leer el stream SSE."""
        while self.is_running and self._session:
            try:
                async with self._session.get(self.uri) as response:
                    if response.status >= 400:
                        self.logger.error(f"Error al abrir stream SSE en {self.uri}: {response.status}")
                        await asyncio.sleep(5)
                        continue
                    
                    async for line in response.content:
                        if not self.is_running:
                            break
                        
                        line = line.decode('utf-8').strip()
                        if not line:
                            continue
                        
                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                            if event_type == "endpoint":
                               # Recibimos el endpoint real para RPC
                               pass
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                            try:
                                payload = json.loads(data_str)
                                
                                # Si recibimos el endpoint real para los POSTs (común en MCP SSE)
                                if isinstance(payload, str) and payload.startswith("http"):
                                    self._post_url = payload
                                    self.logger.info(f"Endpoint RPC recibido: {self._post_url}")
                                    continue

                                msg = Message(
                                    sender_id="mcp_server",
                                    recipient_id="mcp_client",
                                    content=payload,
                                    message_type=MessageType.RESPONSE if "id" in payload else MessageType.NOTIFICATION
                                )
                                self.message_handler(msg)
                            except json.JSONDecodeError:
                                self.logger.error(f"Error al parsear JSON de data SSE: {data_str}")
            except Exception as e:
                self.logger.error(f"Error en loop SSE de {self.uri}: {e}")
                if self.is_running:
                    await asyncio.sleep(5)
