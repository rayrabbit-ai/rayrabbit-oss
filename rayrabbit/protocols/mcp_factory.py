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
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger
from ..security.auditing import AuditManager, AuditEvent, AuditLevel, EventCategory

class MCPFactory:
    """
    Factoría para la generación dinámica de componentes MCP.
    Permite convertir automáticamente especificaciones OpenAPI en herramientas MCP.
    """
    
    def __init__(self, audit_manager: Optional[AuditManager] = None):
        self.logger = get_logger("MCPFactory")
        self.audit_manager = audit_manager
        self.registered_services: Dict[str, Dict[str, Any]] = {}

    async def register_service(self, service_id: str, openapi_url: str) -> List[Dict[str, Any]]:
        """
        Registra un servicio externo vía su especificación OpenAPI y genera herramientas MCP.
        
        Args:
            service_id (str): Identificador único del servicio.
            openapi_url (str): URL de la especificación JSON de OpenAPI.
            
        Returns:
            List[Dict[str, Any]]: Lista de herramientas MCP generadas.
        """
        self.logger.info(f"Registrando servicio {service_id} desde {openapi_url}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(openapi_url) as response:
                    if response.status >= 400:
                        self.logger.error(f"Error al obtener OpenAPI de {service_id}: {response.status}")
                        return []
                    spec = await response.json()
            
            tools = []
            base_url = spec.get("servers", [{}])[0].get("url", "")
            if not base_url.startswith("http"):
                # Si la URL del server es relativa, intentamos construirla desde openapi_url
                from urllib.parse import urljoin
                base_url = urljoin(openapi_url, base_url)

            paths = spec.get("paths", {})
            for path, methods in paths.items():
                for method, operation in methods.items():
                    if method.lower() not in ["get", "post", "put", "delete"]:
                        continue
                    
                    operation_id = operation.get("operationId")
                    if not operation_id:
                        # Generar un ID determinista si no existe
                        operation_id = f"{service_id}_{method}_{path.strip('/')}".replace("/", "_")
                    
                    tool = {
                        "name": operation_id,
                        "description": operation.get("summary") or operation.get("description") or f"{method.upper()} {path}",
                        "inputSchema": self._extract_input_schema(operation),
                        "_rayrabbit_meta": {
                            "service_id": service_id,
                            "path": path,
                            "method": method.upper(),
                            "base_url": base_url
                        }
                    }
                    tools.append(tool)
            
            self.registered_services[service_id] = {
                "spec": spec,
                "tools": tools,
                "base_url": base_url
            }
            
            self.logger.info(f"Servicio {service_id} registrado exitosamente con {len(tools)} herramientas.")
            
            # Auditoría MAESTRO
            if self.audit_manager:
                self.audit_manager.log_event(
                    level=AuditLevel.INFO,
                    category=EventCategory.SYSTEM_CHANGE,
                    event_type="MCP_SERVICE_REGISTERED",
                    action="register_service",
                    result="SUCCESS",
                    details={"service_id": service_id, "tool_count": len(tools), "url": openapi_url}
                )
            return tools

        except Exception as e:
            self.logger.error(f"Error fatal registrando servicio {service_id}: {e}")
            return []

    def _extract_input_schema(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae o genera un JSON Schema para la entrada de la operación."""
        properties = {}
        required = []

        # 1. Parámetros (path, query, header)
        parameters = operation.get("parameters", [])
        for param in parameters:
            param_name = param.get("name")
            param_schema = param.get("schema", {"type": "string"})
            properties[param_name] = param_schema
            if param.get("required"):
                required.append(param_name)

        # 2. Body (JSON)
        request_body = operation.get("requestBody", {})
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        body_schema = json_content.get("schema", {})
        
        if body_schema:
            if body_schema.get("type") == "object":
                # Mezclar propiedades del body con parámetros
                properties.update(body_schema.get("properties", {}))
                required.extend(body_schema.get("required", []))
            else:
                # Si el body no es un objeto, lo mapeamos bajo la clave 'requestBody'
                properties["requestBody"] = body_schema
                if request_body.get("required"):
                    required.append("requestBody")

        return {
            "type": "object",
            "properties": properties,
            "required": list(set(required))
        }

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Ejecuta una herramienta generada dinámicamente realizando la llamada HTTP correspondiente.
        """
        # Buscar la herramienta en los servicios registrados
        target_tool = None
        for service_data in self.registered_services.values():
            for tool in service_data["tools"]:
                if tool["name"] == tool_name:
                    target_tool = tool
                    break
            if target_tool:
                break
        
        if not target_tool:
            raise ValueError(f"Herramienta '{tool_name}' no encontrada en MCPFactory.")

        meta = target_tool["_rayrabbit_meta"]
        method = meta["method"]
        path = meta["path"]
        base_url = meta["base_url"]

        # 1. Resolver parámetros de path
        resolved_path = path
        for key, value in arguments.items():
             if f"{{{key}}}" in resolved_path:
                 resolved_path = resolved_path.replace(f"{{{key}}}", str(value))
        
        url = f"{base_url.rstrip('/')}/{resolved_path.lstrip('/')}"
        
        # 2. Separar query params y body
        # Por simplicidad en esta versión, si el método es GET van a query, sino a body
        # En una versión más robusta usaríamos la spec de OpenAPI para saber dónde va cada uno
        query_params = {}
        body = {}
        
        if method == "GET":
            query_params = arguments
        else:
            body = arguments

        self.logger.info(f"Ejecutando herramienta {tool_name} -> {method} {url}")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300.0)) as session:
            try:
                async with session.request(method, url, params=query_params, json=body) as response:
                    res_data = await response.json()
                    # Auditoría MAESTRO
                    if self.audit_manager:
                        self.audit_manager.log_event(
                            level=AuditLevel.INFO,
                            category=EventCategory.COMMUNICATION,
                            event_type="MCP_FACTORY_TOOL_EXECUTED",
                            action=tool_name,
                            result="SUCCESS",
                            details={"service_id": meta["service_id"], "method": method, "url": url}
                        )
                    return res_data
            except Exception as e:
                self.logger.error(f"Error ejecutando llamada HTTP para {tool_name}: {e}")
                # Auditoría MAESTRO: Fallo
                if self.audit_manager:
                    self.audit_manager.log_event(
                        level=AuditLevel.ERROR,
                        category=EventCategory.COMMUNICATION,
                        event_type="MCP_FACTORY_TOOL_FAILED",
                        action=tool_name,
                        result="FAILURE",
                        details={"service_id": meta["service_id"], "error": str(e)}
                    )
                return {"error": str(e)}
