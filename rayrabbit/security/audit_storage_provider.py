# -*- coding: utf-8 -*-
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
"""Definición de la interfaz para los proveedores de almacenamiento de auditoría.

Este archivo define la clase base abstracta que deben implementar todos los
proveedores de almacenamiento de logs de auditoría en la versión OSS de RayRabbit.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .auditing import AuditEvent


class AuditStorageProvider(ABC):
    """Clase base abstracta (Interfaz) para los proveedores de almacenamiento de auditoría.

    Define el contrato que deben seguir todos los proveedores de almacenamiento
    para garantizar la interoperabilidad y el desacoplamiento de la infraestructura.
    """

    @abstractmethod
    async def save_event(self, event: "AuditEvent") -> None:
        """Guarda un único evento de auditoría en el sistema de almacenamiento persistente."""
        pass

    @abstractmethod
    async def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        **kwargs: Any,
    ) -> List["AuditEvent"]:
        """Recupera una lista de eventos de auditoría con filtros y paginación."""
        pass

    @abstractmethod
    async def get_event_by_id(self, event_id: str) -> Optional["AuditEvent"]:
        """Recupera un evento de auditoría específico por su ID único."""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establece y prepara la conexión con el sistema de almacenamiento subyacente."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Cierra de forma segura la conexión con el sistema de almacenamiento."""
        pass
