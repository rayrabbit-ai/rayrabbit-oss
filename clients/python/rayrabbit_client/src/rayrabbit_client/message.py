import json
import uuid
from enum import Enum
from typing import Dict, Any, Optional

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class Message:
    def __init__(self, sender_id: str, recipient_id: str, content: Any, message_type: MessageType = MessageType.NOTIFICATION, correlation_id: Optional[str] = None):
        self.message_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.message_type = message_type
        self.correlation_id = correlation_id
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "correlation_id": self.correlation_id
        }
