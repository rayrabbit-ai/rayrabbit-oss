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
MAESTRO Security Orchestrator
Conceptual Framework: Ken Huang (Cloud Security Alliance, 2025)
Production Implementation: RayRabbit Labs
"""
"""
DataValidator - Componente de validación y sanitización de datos para MAESTRO.
"""

import html
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger

if TYPE_CHECKING:
    from .auditing import AuditManager

class ValidationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    PARANOID = "paranoid"

class SanitizationMode(Enum):
    ESCAPE = "escape"
    REMOVE = "remove"
    ENCODE = "encode"
    REJECT = "reject"

@dataclass
class ValidationRule:
    name: str
    field_path: str
    validator: Callable[[Any], bool]
    error_message: str
    sanitizer: Optional[Callable[[Any], Any]] = None
    required: bool = False

class DataValidator:
    """
    Motor de validación y sanitización de datos.
    """
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        audit_manager: Optional["AuditManager"] = None,
    ) -> None:
        self.config = config or {}
        self.logger = get_logger("DataValidator")
        self._audit_manager: Optional["AuditManager"] = audit_manager
        self.dangerous_patterns = {
            'sql_injection': [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
                r"(--|#|\/\*|\*\/)",
            ],
            'xss': [
                r"<script[^>]*>.*?<\/script>",
                r"javascript:",
                r"on\w+\s*=",
            ],
            'path_traversal': [
                r"\.\.\/",
                r"\\\\.\\/",
            ]
        }

    def set_audit_manager(self, audit_manager: "AuditManager") -> None:
        """Inyecta el AuditManager para persistir eventos de seguridad en SQLite."""
        self._audit_manager = audit_manager

    def validate_and_sanitize(self, data: Dict[str, Any], rules: List[ValidationRule]) -> Dict[str, Any]:
        validated_data = data.copy()
        for rule in rules:
            try:
                field_value = self._get_field_value(validated_data, rule.field_path)
                if field_value is None:
                    if rule.required:
                        raise ValueError(f"El campo requerido '{rule.field_path}' no se encuentra.")
                    continue

                if not rule.validator(field_value):
                    raise ValueError(f"Validación fallida para '{rule.field_path}': {rule.error_message}")

                if rule.sanitizer:
                    sanitized_value = rule.sanitizer(field_value)
                    self._set_field_value(validated_data, rule.field_path, sanitized_value)

            except (KeyError, IndexError):
                if rule.required:
                    raise ValueError(f"El campo requerido '{rule.field_path}' no se encuentra en los datos.")
            except Exception as e:
                self.logger.error(f"Error procesando la regla '{rule.name}': {e}")
                raise
        return validated_data

    def _get_field_value(self, data: Dict[str, Any], path: str) -> Optional[Any]:
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def _set_field_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        keys = path.split('.')
        current_level = data
        for i, key in enumerate(keys[:-1]):
            if key not in current_level or not isinstance(current_level[key], dict):
                current_level[key] = {}
            current_level = current_level[key]
        current_level[keys[-1]] = value

    def sanitize_string(self, text: str, mode: SanitizationMode = SanitizationMode.ESCAPE) -> str:
        if mode == SanitizationMode.ESCAPE:
            return html.escape(text)
        # Implementar otros modos si es necesario
        return text

    def sanitize_payload(self, text: str, source_agent_id: Optional[str] = None) -> bool:
        """
        Sanitiza y valida un payload/prompt de usuario.
        Retorna True si el payload está libre de patrones peligrosos (SQLi, XSS, Path Traversal),
        y False si se detecta alguna anomalía o patrón sospechoso.

        Cuando se detecta un patrón peligroso, el evento es registrado tanto en
        el logger (consola) como en el AuditManager (SQLite) si está configurado.

        Args:
            text: Cadena de texto a validar.
            source_agent_id: Identificador del agente origen (opcional, para auditoría).
        """
        if not isinstance(text, str):
            return False

        import re
        for category, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    self.logger.warning(f"Patrón peligroso detectado [{category}]: {pattern}")
                    self._audit_blocked_payload(
                        category=category,
                        pattern=pattern,
                        payload_preview=text[:120],
                        source_agent_id=source_agent_id,
                    )
                    return False
        return True

    def _audit_blocked_payload(
        self,
        category: str,
        pattern: str,
        payload_preview: str,
        source_agent_id: Optional[str] = None,
    ) -> None:
        """Persiste en el AuditManager el evento de payload peligroso bloqueado.

        Solo actúa si se ha inyectado un AuditManager mediante el constructor
        o ``set_audit_manager``. Falla de forma silenciosa si no está disponible.
        """
        if self._audit_manager is None:
            return
        try:
            from .auditing import AuditLevel, EventCategory
            self._audit_manager.log_event(
                level=AuditLevel.WARNING,
                category=EventCategory.SECURITY_VIOLATION,
                event_type="PAYLOAD_BLOCKED_INJECTION",
                action="sanitize_payload",
                result="BLOCKED",
                agent_id=source_agent_id or self._audit_manager.agent_id,
                details={
                    "threat_category": category,
                    "matched_pattern": pattern,
                    "payload_preview": payload_preview,
                },
            )
        except Exception as exc:
            self.logger.error(f"Error al auditar payload bloqueado: {exc}")

