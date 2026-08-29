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
Generador de mensajes A2UI v0.9.1 para RayRabbit OSS.
Proporciona una API fluida para construir payloads compatibles con la especificación.
"""

from typing import Dict, Any, List, Optional
import uuid

class A2UIGenerator:
    """
    Clase de utilidad para generar mensajes A2UI v0.9.1.
    Siguiendo el estándar definido en specs/server_to_client.json.
    """
    
    VERSION = "v0.9.1"
    DEFAULT_CATALOG_ID = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"

    @classmethod
    def begin_rendering(cls, surface_id: str, catalog_id: str = DEFAULT_CATALOG_ID, theme: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Crea un mensaje beginRendering (v0.9.1)."""
        payload = {
            "version": cls.VERSION,
            "beginRendering": {
                "surfaceId": surface_id,
                "catalogId": catalog_id
            }
        }
        if theme:
            payload["beginRendering"]["theme"] = theme
        return payload

    @classmethod
    def surface_update(cls, surface_id: str, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crea un mensaje surfaceUpdate (v0.9.1)."""
        return {
            "version": cls.VERSION,
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": components
            }
        }

    @classmethod
    def update_data_model(cls, surface_id: str, value: Any, path: str = "/") -> Dict[str, Any]:
        """Crea un mensaje updateDataModel."""
        return {
            "version": cls.VERSION,
            "updateDataModel": {
                "surfaceId": surface_id,
                "path": path,
                "value": value
            }
        }

    @classmethod
    def delete_surface(cls, surface_id: str) -> Dict[str, Any]:
        """Crea un mensaje deleteSurface."""
        return {
            "version": cls.VERSION,
            "deleteSurface": {
                "surfaceId": surface_id
            }
        }
