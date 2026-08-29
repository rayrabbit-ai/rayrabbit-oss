"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict, field

class MessageType(Enum):
    """Tipos de mensajes soportados por RayRabbit."""
    INFORM = "inform"
    REQUEST = "request"
    RESPONSE = "response"
    QUERY = "query"
    COMMAND = "command"
    EVENT = "event"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    BROADCAST = "broadcast"
    KEY_EXCHANGE_REQUEST = "key_exchange_request"
    KEY_EXCHANGE_RESPONSE = "key_exchange_response"

@dataclass
class Message:
    """
    Estructura estándar de mensaje en RayRabbit.
    
    Implementa el formato de mensaje compatible con protocolos A2A y MCP,
    utilizando JSON como formato de serialización estándar.
    
    Attributes:
        sender_id: ID único del agente emisor
        sender_name: Nombre del agente emisor
        recipient_id: ID del agente destinatario ("*" para broadcast)
        content: Contenido del mensaje (serializable o bytes)
        message_type: Tipo de mensaje (MessageType)
        message_id: ID único del mensaje (generado automáticamente)
        timestamp: Timestamp de creación (generado automáticamente)
        correlation_id: ID para correlacionar request/response
        metadata: Metadatos adicionales del mensaje
        encrypted: Indica si el mensaje está cifrado (añadido para MAESTRO)
    """
    
    sender_id: str
    sender_name: str
    recipient_id: str
    content: Union[Dict[str, Any], bytes]
    message_type: MessageType
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    encrypted: bool = False
    signature: Optional[bytes] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el mensaje a diccionario para serialización.
        
        Returns:
            Diccionario con todos los campos del mensaje
        """
        data = asdict(self)
        data["message_type"] = self.message_type.value
        data["timestamp"] = self.timestamp.isoformat()
        # No serializar contenido binario directamente
        if isinstance(self.content, bytes):
            data["content"] = "<binary_content>"
        return data
        
    def to_json(self) -> str:
        """
        Serializa el mensaje a JSON.
        
        Returns:
            String JSON del mensaje
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_canonical_json_bytes(self) -> bytes:
        """
        Serializa el mensaje a bytes usando una representación JSON canónica.
        Esto es CRUCIAL para la firma y verificación criptográfica.
        """
        # Prepara el diccionario, asegurando que los tipos complejos son serializables
        data = self.to_dict()
        # Excluir la firma del propio mensaje que se va a firmar
        if 'signature' in data:
            del data['signature']

        def deep_sort(obj):
            if isinstance(obj, dict):
                return {k: deep_sort(v) for k, v in sorted(obj.items())}
            if isinstance(obj, list):
                return [deep_sort(element) for element in obj]
            return obj

        sorted_data = deep_sort(data)

        # Serializar a JSON con claves ordenadas y sin espacios, luego codificar a bytes
        return json.dumps(sorted_data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Crea un mensaje desde un diccionario.
        
        Args:
            data: Diccionario con los datos del mensaje
            
        Returns:
            Instancia de Message
        """
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("message_type"), str):
            data["message_type"] = MessageType(data["message_type"])
        return cls(**data)
        
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """
        Crea un mensaje desde JSON.
        
        Args:
            json_str: String JSON del mensaje
            
        Returns:
            Instancia de Message
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
        
    def create_response(self, content: Union[Dict[str, Any], bytes], 
                       message_type: MessageType = MessageType.RESPONSE) -> 'Message':
        """
        Crea un mensaje de respuesta a este mensaje.
        
        Args:
            content: Contenido de la respuesta
            message_type: Tipo de mensaje de respuesta
            
        Returns:
            Nuevo mensaje de respuesta
        """
        return Message(
            sender_id=self.recipient_id,
            sender_name="",
            recipient_id=self.sender_id,
            content=content,
            message_type=message_type,
            correlation_id=self.message_id
        )
        
    def is_broadcast(self) -> bool:
        """
        Verifica si el mensaje es un broadcast.
        
        Returns:
            True si es un mensaje broadcast
        """
        return self.recipient_id == "*"
        
    def is_request(self) -> bool:
        """
        Verifica si el mensaje es una solicitud que espera respuesta.
        
        Returns:
            True si es un mensaje de solicitud
        """
        return self.message_type in [MessageType.REQUEST, MessageType.QUERY, MessageType.COMMAND]
        
    def validate(self) -> bool:
        """
        Valida que el mensaje tenga la estructura correcta.
        
        Returns:
            True si el mensaje es válido
        """
        # Check that required string fields are non-empty
        for field_name in ("sender_id", "recipient_id"):
            if not getattr(self, field_name):
                return False

        # Validate content serializability if it's a dict
        if isinstance(self.content, dict):
            try:
                json.dumps(self.content)
            except (TypeError, ValueError):
                return False
        
        # If content is not a dict, the type hint Union[Dict, bytes] guarantees it's bytes.
        # No further type check is needed for mypy to be satisfied.
            
        return True
        
    def __str__(self) -> str:
        return f"Message(id={self.message_id[:8]}..., type={self.message_type.value}, from={self.sender_name}, to={self.recipient_id})"
        
    def __repr__(self) -> str:
        return self.__str__()