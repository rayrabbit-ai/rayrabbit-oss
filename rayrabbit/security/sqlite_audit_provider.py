from __future__ import annotations

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
"""Proveedor de almacenamiento de logs de auditoría basado en SQLite.

Implementa la interfaz AuditStorageProvider utilizando la capa de
repositorio para interactuar con SQLite de forma asíncrona.
"""


import asyncio
from typing import Any, List, Optional, TYPE_CHECKING

from .audit_repository import AuditRepository
from .audit_storage_provider import AuditStorageProvider

if TYPE_CHECKING:
    from .auditing import AuditEvent
    from .maestro import MAESTROSecurity


class SQLiteAuditProvider(AuditStorageProvider):
    """Implementación de proveedor de almacenamiento que utiliza SQLite."""

    def __init__(self, db_path: str, maestro: "MAESTROSecurity") -> None:
        """Inicializa el proveedor de auditoría de SQLite.

        Args:
            db_path: Ruta al archivo de la base de datos SQLite.
            maestro: Instancia del gestor de seguridad MAESTRO para el cifrado.
        """
        self.repository = AuditRepository(db_path, maestro)

    async def connect(self) -> None:
        """Establece y prepara la conexión con el almacenamiento.

        Operación no bloqueante en SQLite.
        """
        await asyncio.sleep(0)

    async def disconnect(self) -> None:
        """Cierra de forma segura la conexión con el almacenamiento.

        Operación no bloqueante en SQLite.
        """
        await asyncio.sleep(0)

    async def save_event(self, event: "AuditEvent") -> None:
        """Guarda un único evento de auditoría en la base de datos SQLite.

        Se ejecuta en un hilo separado para evitar bloquear el bucle de eventos.
        """
        await asyncio.to_thread(self.repository.add_event, event)

    async def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        **kwargs: Any,
    ) -> List["AuditEvent"]:
        """Recupera una lista de eventos de auditoría con filtros y paginación.

        Se ejecuta en un hilo separado para evitar bloquear el bucle de eventos.
        """
        filters = {
            "limit": limit,
            "offset": offset,
            "event_type": event_type,
            "actor": actor,
            **kwargs,
        }
        valid_filters = {k: v for k, v in filters.items() if v is not None}
        return await asyncio.to_thread(self.repository.query_events, **valid_filters)

    async def get_event_by_id(self, event_id: str) -> Optional["AuditEvent"]:
        """Recupera un evento de auditoría específico por su ID único.

        Se ejecuta en un hilo separado para evitar bloquear el bucle de eventos.
        """
        events = await asyncio.to_thread(
            self.repository.query_events, event_id=event_id
        )
        return events[0] if events else None
