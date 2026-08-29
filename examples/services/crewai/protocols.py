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
Implementaciones robustas de protocolos A2A y MCP para Servicios Externos.

Este módulo es PROTEGIDO y AUTÓNOMO. No depende de RayRabbit.
Implementa los estándares:
- A2A (Agent-to-Agent): JSON-RPC 2.0 (Google/Linux Foundation)
- MCP (Model Context Protocol): Estándar Anthropic

Robustez: A prueba de fallos contra cambios de versión de Pydantic y tipos.
"""
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import uuid

# ============================================================================
# Protocolo A2A (Google - JSON-RPC 2.0)
# ============================================================================

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request - Estándar A2A de Google."""
    jsonrpc: str = Field(default="2.0")
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: Union[str, int, None] = Field(default_factory=lambda: str(uuid.uuid4()))

class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response - Estándar Abierto."""
    jsonrpc: str = Field(default="2.0")
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Union[str, int, None]

    @classmethod
    def success(cls, id: Union[str, int, None], result: Any):
        """Crea una respuesta exitosa estándar."""
        return cls(id=id, result=result)

    @classmethod
    def failure(cls, id: Union[str, int, None], code: int, message: str, data: Any = None):
        """Crea una respuesta de error estándar JSON-RPC."""
        error_obj = {"code": code, "message": message}
        if data:
            error_obj["data"] = data
        return cls(id=id, error=error_obj)

# ============================================================================
# Protocolo MCP (Anthropic - Model Context Protocol)
# ============================================================================

class MCPTool(BaseModel):
    """Tool Definition - Estándar MCP de Anthropic."""
    name: str
    description: str
    category: str = "cognitive_framework"
    inputSchema: Dict[str, Any]

class MCPToolsListResponse(BaseModel):
    """MCP tools/list response."""
    tools: List[MCPTool]

class MCPToolCallRequest(BaseModel):
    """MCP tools/call request."""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class MCPResponse:
    """Helper para construir respuestas MCP sin depender de modelos complejos."""
    @staticmethod
    def text(content: str) -> Dict[str, Any]:
        """Crea una respuesta de texto estándar MCP."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(content)
                }
            ],
            "isError": False
        }

    @staticmethod
    def error(message: str) -> Dict[str, Any]:
        """Crea una respuesta de error estándar MCP."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {message}"
                }
            ],
            "isError": True
        }
