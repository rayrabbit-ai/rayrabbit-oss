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
Transporte local para comunicación en memoria.
"""

import asyncio
from typing import Optional

from .message import Message
from .transport import BaseTransport

class LocalTransport(BaseTransport):
    """Transporte local para comunicación en memoria."""
    
    def __init__(self, transport_id: str = "local") -> None:
        super().__init__(transport_id)
        self.message_queue: asyncio.Queue[Message] = asyncio.Queue()
        
    async def connect(self) -> bool:
        """Establece la conexión local."""
        self.is_connected = True
        self.logger.info("Transporte local conectado")
        return True
        
    async def disconnect(self) -> None:
        """Cierra la conexión local."""
        self.is_connected = False
        self.logger.info("Transporte local desconectado")
        
    async def send(self, message: Message, endpoint: Optional[str] = None) -> bool:
        """Envía un mensaje a la cola local."""
        if not self.is_connected:
            return False
            
        try:
            await self.message_queue.put(message)
            return True
        except Exception as e:
            self.logger.error(f"Error enviando mensaje: {str(e)}")
            return False
            
    async def receive(self) -> Optional[Message]:
        """Recibe un mensaje de la cola local."""
        if not self.is_connected:
            return None
            
        try:
            message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
            return message
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Error recibiendo mensaje: {str(e)}")
            return None
            
    async def close(self) -> None:
        """Cierra el transporte local."""
        await self.disconnect()
        
        # Limpiar cola
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
