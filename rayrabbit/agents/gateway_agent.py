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
GatewayAgent - Agente de Pasarela para Comunicación Federada.

Este agente actúa como el único punto de entrada y salida para la comunicación
entre diferentes instancias de RayRabbit. Intercepta mensajes
dirigidos a agentes externos, gestiona el intercambio de claves y asegura
la comunicación a través de un transporte de red.
"""

import json
from typing import Dict, cast, Optional

from ..core.agent import Agent
from ..communication.message import Message
from ..communication.transport import BaseTransport
from ..security.maestro import MAESTROSecurity
from ..core.message_bus import MessageBus
from ..utils.logger import get_logger

class GatewayAgent(Agent):
    """
    Gestiona la comunicación segura y federada con otras instancias de RayRabbit.
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, security_manager: MAESTROSecurity, external_transport: BaseTransport, known_peers: Dict[str, str]) -> None:
        super().__init__(agent_id, "GatewayAgent", "Agente de pasarela para comunicación federada.")
        self.message_bus: Optional[MessageBus] = message_bus
        self.security: Optional[MAESTROSecurity] = security_manager
        self.external_transport = external_transport
        self.known_peers = known_peers # Mapeo de instance_id -> endpoint_url
        self.logger = get_logger(f"GatewayAgent-{self.id}")

    async def start(self) -> None:
        await super().start()
        # Hook para interceptar todos los mensajes publicados en el bus local
        if self.message_bus:
            self.message_bus.gateway_hook = self.handle_outgoing_message
        # El transporte externo llamará a este método para los mensajes entrantes
        self.external_transport.set_message_handler(self.handle_incoming_federated_message)
        await self.external_transport.start()
        self.logger.info("GatewayAgent iniciado y escuchando en el transporte externo.")

    async def handle_outgoing_message(self, message: Message) -> bool:
        """
        Hook que intercepta mensajes en el bus local. Si un mensaje es para un
        agente externo, lo procesa y lo envía a través de la federación.
        """
        recipient_instance_id = self._get_instance_id(message.recipient_id)
        if self.message_bus and self.message_bus.instance_id and recipient_instance_id != self.message_bus.instance_id:
            self.logger.info(f"Interceptado mensaje para federación. Destinatario: {message.recipient_id}")
            await self.send_federated_message(message)
            return True 
        return False

    async def send_federated_message(self, message: Message) -> None:
        recipient_instance_id = self._get_instance_id(message.recipient_id)
        peer_endpoint = self.known_peers.get(recipient_instance_id)

        if not peer_endpoint:
            self.logger.error(f"No se conoce el endpoint para la instancia '{recipient_instance_id}'.")
            return
        
        if not self.security:
            self.logger.error("No se puede enviar mensaje federado: el módulo de seguridad no está configurado.")
            return

        try:
            if not isinstance(message.content, dict):
                self.logger.error(f"GatewayAgent solo puede federar contenido de tipo 'dict'. Se recibió '{type(message.content)}'.")
                return

            content_bytes = json.dumps(message.content).encode('utf-8')
            encrypted_content = self.security.encrypt_for(content_bytes, message.recipient_id)
            
            federated_message = Message(
                sender_id=message.sender_id,
                sender_name=message.sender_name,
                recipient_id=message.recipient_id,
                content=encrypted_content,
                message_type=message.message_type,
                encrypted=True
            )
            
            await self.external_transport.send(federated_message, peer_endpoint)
            self.logger.info(f"Mensaje federado enviado a {message.recipient_id} en {peer_endpoint}")
        except Exception as e:
            self.logger.error(f"Error al enviar mensaje federado: {e}", exc_info=True)

    async def handle_incoming_federated_message(self, message: Message) -> None:
        """
        Maneja un mensaje cifrado recibido desde otra instancia a través del transporte externo.
        """
        self.logger.info(f"Recibido mensaje federado de {message.sender_id}")
        
        if not self.security or not self.message_bus:
            self.logger.error("No se puede procesar mensaje entrante: seguridad o bus no configurados.")
            return

        try:
            if not isinstance(message.content, bytes):
                self.logger.error(f"Se recibió un mensaje federado con un tipo de contenido inválido: {type(message.content)}")
                return

            decrypted_content_bytes = self.security.decrypt_from(message.content)
            
            # Deserializar el JSON a un diccionario de Python
            content_dict = json.loads(decrypted_content_bytes.decode('utf-8'))

            internal_message = Message(
                sender_id=message.sender_id,
                sender_name=message.sender_name,
                recipient_id=message.recipient_id,
                content=content_dict,
                message_type=message.message_type,
                encrypted=False
            )
            
            await self.message_bus.publish(internal_message)
            self.logger.info(f"Mensaje federado de {message.sender_id} publicado en el bus local para {message.recipient_id}")
        except Exception as e:
            self.logger.error(f"Error al procesar mensaje federado entrante: {e}", exc_info=True)

    def _get_instance_id(self, agent_id: str) -> str:
        if '.' in agent_id:
            return agent_id.split('.')[0]
        if self.message_bus and self.message_bus.instance_id:
            return self.message_bus.instance_id
        
        # Si no se puede determinar el ID de la instancia, es un error crítico.
        raise ValueError("No se pudo determinar el instance_id local porque message_bus no está configurado o no tiene un ID.")
