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
SovereignProxyAgent - Proxy de agente soberano para el MessageBus del Hub.

Cuando un servicio soberano (ej: A2UI en puerto 8006) completa su Handshake,
el Hub registra este proxy en el MessageBus para que los mensajes dirigidos
a ese agente sean reenviados vía A2A Router (HTTP P2P directo) en lugar de
ir al Outbox.

Este patrón resuelve la race condition donde el browser envía mensajes
antes de que el servicio soberano complete su registro.
"""

from typing import Any, Optional, TYPE_CHECKING

from .agent import Agent
from ..communication.message import Message
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..protocols.a2a_router import A2ARouter


class SovereignProxyAgent(Agent):
    """
    Agente proxy que representa a un servicio soberano externo en el MessageBus del Hub.
    
    Cuando recibe un mensaje a través del MessageBus, lo reenvía vía A2A Router
    (HTTP P2P directo) al servicio soberano real, eliminando la necesidad de
    almacenar mensajes en el Outbox durante la ventana de arranque.
    """
    
    def __init__(self, agent_id: str, p2p_endpoint: str, message_bus: Any) -> None:
        """
        Args:
            agent_id: ID del agente soberano remoto (ej: 'sovereign_node_1').
            p2p_endpoint: URL del endpoint A2A del servicio soberano (ej: 'http://127.0.0.1:8006/a2a').
            message_bus: Referencia al MessageBus del Hub (para set_message_bus en register_agent).
        """
        super().__init__(
            agent_id=agent_id,
            name=f"SovereignProxy({agent_id})",
            description=f"Proxy para servicio soberano en {p2p_endpoint}"
        )
        self._p2p_endpoint = p2p_endpoint
        self._router: Optional['A2ARouter'] = None
        self.logger = get_logger(f"SovereignProxy-{agent_id}")
        self.logger.info(f"Proxy soberano creado para '{agent_id}' -> {p2p_endpoint}")

    def set_router(self, router: 'A2ARouter') -> None:
        """Inyecta el A2A Router para el reenvío de mensajes."""
        self._router = router

    async def receive_message(self, message: Message) -> None:
        """
        Intercepta mensajes del MessageBus y los reenvía al servicio soberano
        vía A2A Router (HTTP P2P directo).
        
        Sobreescribe el método base para evitar el encolado interno y hacer
        relay directo al servicio externo.
        """
        self.metrics["messages_received"] += 1
        
        if self._router:
            try:
                await self._router.route_message(
                    sender_id=message.sender_id,
                    recipient_id=self.id,
                    content=message.content,
                    message_type=message.message_type,
                    correlation_id=message.correlation_id or message.message_id
                )
                self.logger.debug(
                    f"Mensaje {message.message_id} reenviado a servicio soberano "
                    f"'{self.id}' vía A2A Router."
                )
            except Exception as e:
                self.logger.error(
                    f"Error reenviando mensaje {message.message_id} al servicio "
                    f"soberano '{self.id}': {e}"
                )
                self.metrics["processing_errors"] += 1
        else:
            self.logger.error(
                f"SovereignProxy '{self.id}': No hay A2A Router disponible para relay. "
                f"Mensaje {message.message_id} descartado."
            )
            self.metrics["processing_errors"] += 1
