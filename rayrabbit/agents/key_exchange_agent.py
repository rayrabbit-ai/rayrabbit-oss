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
KeyExchangeAgent - Agente especializado para la comunicación federada segura.

Este agente gestiona el intercambio de claves públicas entre diferentes instancias
de RayRabbit, permitiendo que se establezca un canal de comunicación cifrado.
"""


from ..core.agent import Agent
from ..communication.message import Message, MessageType
from ..security.maestro import MAESTROSecurity
from ..core.message_bus import MessageBus
from ..security.encryption_defs import KeyType

class KeyExchangeAgent(Agent):
    """
    Agente que maneja las solicitudes de intercambio de claves públicas.
    
    Escucha los mensajes de tipo KEY_EXCHANGE_REQUEST y responde con
    la clave pública de la instancia actual, firmada por su clave privada.
    """
    
    def __init__(self, agent_id: str, name: str, description: str, 
                 message_bus: MessageBus, security_manager: MAESTROSecurity):
        """
        Inicializa el KeyExchangeAgent.
        
        Args:
            agent_id: ID único del agente.
            name: Nombre del agente.
            description: Descripción del agente.
            message_bus: El bus de mensajes del framework.
            security_manager: El gestor de seguridad MAESTRO.
        """
        super().__init__(agent_id, name, description)
        self.message_bus = message_bus
        self.security = security_manager
        self.add_capability("key-exchange-responder")
        
    async def start(self) -> None:
        """Inicia el agente y se suscribe al topic de key exchange."""
        await super().start()
        if self.message_bus:
            await self.message_bus.register_agent(self)
            self.register_message_handler(MessageType.KEY_EXCHANGE_REQUEST, self.handle_key_exchange_request)
            self.logger.info(f"KeyExchangeAgent suscrito a mensajes para '{self.id}'")
        else:
            self.logger.error("MessageBus no está configurado para KeyExchangeAgent, no se puede iniciar.")

    async def handle_key_exchange_request(self, message: Message) -> None:
        """
        Maneja una solicitud de intercambio de claves.
        
        Recupera la clave pública de la instancia, la empaqueta en una respuesta
        y la envía de vuelta al solicitante.
        
        Args:
            message: El mensaje de solicitud de clave.
        """
        self.logger.info(f"Recibida solicitud de intercambio de claves de '{message.sender_id}'")
        
        try:
            # 1. Obtener la clave pública propia
            public_key_obj = self.security.get_identity_key(KeyType.PUBLIC)
            
            if not public_key_obj:
                raise RuntimeError("No se pudo obtener la clave pública de la instancia.")

            # La clave está en bytes (formato PEM), decodificar a string para JSON
            public_key_pem = public_key_obj.key_data.decode('utf-8')
            
            # 2. Crear el contenido de la respuesta
            response_content = {
                "status": "success",
                "public_key_pem": public_key_pem,
                "agent_id": self.security.agent_id
            }
            
            # 3. Crear el mensaje de respuesta
            response_message = message.create_response(
                content=response_content,
                message_type=MessageType.KEY_EXCHANGE_RESPONSE
            )
            response_message.sender_id = self.id
            response_message.sender_name = self.name
            
            # 4. Enviar la respuesta a través del bus de mensajes
            if self.message_bus:
                await self.message_bus.publish(response_message)
            
            self.logger.info(f"Enviada clave pública a '{message.sender_id}'")
            
        except Exception as e:
            self.logger.error(f"Error manejando la solicitud de intercambio de claves: {e}")
            # Opcional: Enviar un mensaje de error de vuelta
            error_response = message.create_response(
                content={"status": "error", "message": str(e)},
                message_type=MessageType.ERROR
            )
            error_response.sender_id = self.id
            if self.message_bus:
                await self.message_bus.publish(error_response)

