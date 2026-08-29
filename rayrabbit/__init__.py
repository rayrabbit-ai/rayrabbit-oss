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
RayRabbit Framework - Un framework agéntico para la interoperabilidad de IA

Este framework proporciona:
- Comunicación entre agentes usando protocolos A2A y MCP
- Bus de mensajes centralizado
- Agentes especializados (LLM, Simple)
- Seguridad integrada con el marco MAESTRO
"""

from .version import __version__
__author__ = "RayRabbit Team"

# Importar componentes fundamentales primero
from .core.agent import Agent, AgentStatus
from .core.message_bus import MessageBus
from .communication.message import Message, MessageType
from .agents.simple_agent import SimpleAgent
from .protocols.a2a import A2AProtocol
from .protocols.mcp import MCPProtocol, MCPServer, MCPClient

# Importar el framework principal al final para evitar ciclos
from .core.framework import RayRabbitFramework

__all__ = [
    "__version__",
    "Agent",
    "AgentStatus", 
    "MessageBus",
    "Message",
    "MessageType",
    "SimpleAgent",
    "A2AProtocol",
    "MCPProtocol",
    "MCPServer",
    "MCPClient",
    "RayRabbitFramework"
]
