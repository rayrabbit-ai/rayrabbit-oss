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
Validator para mensajes A2UI v0.9.1 en RayRabbit OSS.
Utiliza jsonschema (Draft 2020-12) para asegurar que los mensajes cumplan con la especificación oficial.
"""

import json
import logging
from typing import Dict, Any, List, Union
from jsonschema import ValidationError
from jsonschema.validators import Draft202012Validator

class A2UIValidator:
    """
    Clase para validar mensajes A2UI (Server-to-Client y Client-to-Server).
    Utiliza Draft 2020-12 para resolver correctamente $defs/$ref del esquema oficial.
    """
    
    def __init__(self, schema_path: str = None):
        self.logger = logging.getLogger(__name__)
        from pathlib import Path
        self.base_path = Path(__file__).parent
        self.schema = self._load_official_schema()
        # Pre-compilar el validador para rendimiento
        self._validator_cls = Draft202012Validator(self.schema)

    def _load_official_schema(self) -> Dict[str, Any]:
        """Carga el esquema oficial v0.9.1 (Server-to-Client) desde la carpeta specs."""
        schema_file = self.base_path / "specs" / "server_to_client.json"
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"A2UI: No se pudo cargar el esquema oficial en {schema_file}: {e}")
            # Fallback mínimo para no romper la ejecución
            return { "type": "object", "properties": { "version": { "const": "v0.9.1" } } }

    def validate_message(self, message: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """
        Valida un mensaje individual o una lista de mensajes A2UI.
        """
        try:
            if isinstance(message, list):
                for msg in message:
                    self._validator_cls.validate(msg)
            else:
                self._validator_cls.validate(message)
            return True
        except ValidationError as e:
            self.logger.error(f"Error de validación A2UI: {e.message}")
            return False
        except Exception as e:
            self.logger.error(f"Error inesperado al validar A2UI: {e}")
            return False

# Pruebas básicas si se ejecuta directamente
if __name__ == "__main__":
    validator = A2UIValidator()
    test_msg = {
        "version": "v0.9.1",
        "beginRendering": {
            "surfaceId": "test",
            "catalogId": "test_catalog"
        }
    }
    if validator.validate_message(test_msg):
        print("Mensaje de prueba válido")
    else:
        print("Mensaje de prueba inválido")
