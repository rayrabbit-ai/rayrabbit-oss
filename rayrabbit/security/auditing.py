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
"""Módulo de auditoría asíncrona para RayRabbit OSS.

Proporciona el gestor de auditoría (``AuditManager``), el evento de auditoría
(``AuditEvent``) y los enumerados de nivel y categoría. Toda la lógica es
100 % funcional y asíncrona; no contiene simulaciones ni placeholders.

Nota arquitectónica (Enterprise):
    El encadenamiento de hashes para logs inmutables (garantía de no repudio)
    corresponde a ``rayrabbit_enterprise/security`` y no forma parte de OSS.
"""


import asyncio
import datetime
import hashlib
import secrets
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, cast

from ..utils.logger import get_logger
from .audit_storage_provider import AuditStorageProvider


class AuditLevel(Enum):
    """Niveles de severidad para los eventos de auditoría."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventCategory(Enum):
    """Categorías funcionales para los eventos de auditoría."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    SYSTEM_CHANGE = "system_change"
    SECURITY_VIOLATION = "security_violation"
    AGENT_ACTION = "agent_action"
    COMMUNICATION = "communication"
    ENCRYPTION = "encryption"
    ACCESS_CONTROL = "access_control"


@dataclass
class AuditEvent:
    """Estructura de datos que representa un evento de auditoría registrable."""

    event_id: str
    timestamp: datetime.datetime
    level: AuditLevel
    category: EventCategory
    event_type: str
    action: str
    result: str
    details: Dict[str, Any]
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    resource: Optional[str] = None
    source_ip: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el evento a un diccionario JSON-compatible."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["level"] = self.level.value
        data["category"] = self.category.value
        return data

    def to_json(self) -> str:
        """Serializa el evento a una cadena JSON."""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditManager:
    """Gestor de auditoría asíncrono basado en cola.

    Utiliza ``asyncio.Queue`` y una tarea en segundo plano para procesar y
    guardar eventos de auditoría sin bloquear el bucle de eventos principal.
    """

    def __init__(self, agent_id: Optional[str] = None) -> None:
        self.agent_id = agent_id
        self.storage_provider: Optional[AuditStorageProvider] = None
        self.event_queue: asyncio.Queue[Optional[AuditEvent]] = asyncio.Queue(maxsize=1000)
        self.logger = get_logger("AuditManager")
        self._worker_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]

    def set_storage_provider(self, provider: AuditStorageProvider) -> None:
        """Asigna el proveedor de almacenamiento persistente."""
        self.storage_provider = provider

    async def start(self) -> None:
        """Lanza la tarea en segundo plano que procesa la cola de eventos."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._process_queue())
            self.logger.info("Trabajador asíncrono del AuditManager iniciado.")

    async def stop(self) -> None:
        """Detiene de forma segura la tarea de procesamiento de la cola."""
        if self._worker_task and not self._worker_task.done():
            self.logger.info("Deteniendo el trabajador de auditoría...")
            # Señal de parada: un valor None en la cola
            await self.event_queue.put(None)
            await self._worker_task
            self._worker_task = None
            self.logger.info("Trabajador asíncrono del AuditManager detenido.")

    async def _process_queue(self) -> None:
        """Bucle asíncrono que consume y persiste eventos de la cola."""
        while True:
            try:
                event = await self.event_queue.get()
                if event is None:
                    self.logger.info("Señal de parada recibida. Finalizando procesador de cola.")
                    break
                await cast(AuditStorageProvider, self.storage_provider).save_event(event)
                self.event_queue.task_done()
            except Exception as exc:
                self.logger.error(f"Error procesando evento de auditoría: {exc}", exc_info=True)

    async def flush(self) -> None:
        """Espera a que todos los eventos pendientes en la cola sean procesados."""
        self.logger.info("Vaciando la cola de auditoría...")
        await self.event_queue.join()
        self.logger.info("Cola de auditoría vaciada.")

    def log_event(self, **kwargs: Any) -> None:
        """Crea y encola un ``AuditEvent``. Método síncrono y no bloqueante.

        Parámetros obligatorios en ``kwargs``: ``level``, ``category``,
        ``event_type``, ``action``, ``result``, ``details``.
        """
        campos_requeridos = ["level", "category", "event_type", "action", "result", "details"]
        for campo in campos_requeridos:
            if campo not in kwargs:
                self.logger.error(f"Campo requerido '{campo}' ausente en el evento de auditoría.")
                return

        try:
            event_id = hashlib.sha256(
                f"{datetime.datetime.now().isoformat()}{secrets.token_hex(8)}".encode()
            ).hexdigest()
            evento = AuditEvent(event_id=event_id, timestamp=datetime.datetime.now(), **kwargs)
            self.event_queue.put_nowait(evento)
        except asyncio.QueueFull:
            self.logger.warning("Cola de auditoría llena. El evento será descartado.")
        except Exception as exc:
            self.logger.error(f"Error al encolar evento de auditoría: {exc}")


__all__ = ["AuditLevel", "EventCategory", "AuditEvent", "AuditManager"]
