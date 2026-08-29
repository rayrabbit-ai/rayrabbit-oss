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
"""Capa de repositorio para la auditoría con cifrado integrado.

Gestiona las operaciones de base de datos SQLite para persistir y consultar
los eventos de auditoría utilizando el cifrado provisto por MAESTRO.
"""


import datetime
import json
import sqlite3
from typing import Any, List, Optional, TYPE_CHECKING

from .auditing import AuditEvent, AuditLevel, EventCategory

if TYPE_CHECKING:
    from .maestro import MAESTROSecurity


class AuditRepository:
    """Gestiona las operaciones de base de datos para los eventos de auditoría."""

    def __init__(self, db_path: str, maestro: "MAESTROSecurity") -> None:
        """Inicializa el repositorio y crea la tabla si no existe.

        Args:
            db_path: Ruta del archivo de base de datos SQLite.
            maestro: Instancia del orquestador de seguridad para el cifrado.
        """
        self.db_path = db_path
        self.maestro = maestro
        self._create_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Establece una conexión con la base de datos SQLite."""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _create_table(self) -> None:
        """Crea la tabla de eventos de auditoría si no existe en la base de datos."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user_id TEXT,
                agent_id TEXT,
                resource TEXT,
                action TEXT NOT NULL,
                result TEXT NOT NULL,
                details BLOB,
                source_ip TEXT,
                session_id TEXT,
                correlation_id TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def add_event(self, event: AuditEvent) -> None:
        """Guarda un evento de auditoría aplicando cifrado en los detalles.

        Args:
            event: Objeto del evento de auditoría a guardar.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        details_json = json.dumps(event.details, default=str).encode("utf-8")
        encrypted_details = self.maestro.encrypt_for_storage(details_json)
        try:
            cursor.execute(
                "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.level.value,
                    event.category.value,
                    event.event_type,
                    event.user_id,
                    event.agent_id,
                    event.resource,
                    event.action,
                    event.result,
                    encrypted_details,
                    event.source_ip,
                    event.session_id,
                    event.correlation_id,
                ),
            )
            conn.commit()
        except sqlite3.Error as exc:
            if "no such table" in str(exc):
                # Auto-recuperación si la tabla fue eliminada externamente.
                try:
                    self._create_table()
                    conn = self._get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            event.event_id,
                            event.timestamp.isoformat(),
                            event.level.value,
                            event.category.value,
                            event.event_type,
                            event.user_id,
                            event.agent_id,
                            event.resource,
                            event.action,
                            event.result,
                            encrypted_details,
                            event.source_ip,
                            event.session_id,
                            event.correlation_id,
                        ),
                    )
                    conn.commit()
                except Exception as retry_exc:
                    print(
                        f"Error de Repositorio de Auditoría (Reintento fallido): {retry_exc}"
                    )
            else:
                print(f"Error de Repositorio de Auditoría al escribir en la BD: {exc}")
        finally:
            conn.close()

    def query_events(self, **kwargs: Any) -> List[AuditEvent]:
        """Consulta y descifra eventos de auditoría con filtros y paginación."""
        conn = self._get_connection()
        cursor = conn.cursor()
        base_query = "SELECT * FROM audit_events"
        where_clauses = []
        params = []
        allowed_filters = [
            "level",
            "category",
            "user_id",
            "agent_id",
            "event_type",
            "event_id",
            "correlation_id",
        ]
        for key, value in kwargs.items():
            if key in allowed_filters:
                where_clauses.append(f"{key} = ?")
                params.append(value)
            elif key == "start_date":
                where_clauses.append("timestamp >= ?")
                params.append(value)
            elif key == "end_date":
                where_clauses.append("timestamp <= ?")
                params.append(value)
        if where_clauses:
            query = f"{base_query} WHERE {' AND '.join(where_clauses)}"
        else:
            query = base_query

        query += " ORDER BY timestamp DESC"

        limit = kwargs.get("limit", 100)
        offset = kwargs.get("offset", 0)
        query += f" LIMIT {limit} OFFSET {offset}"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        events = []
        for row in rows:
            try:
                decrypted_details_json = self.maestro.decrypt_for_storage(
                    row[10], agent_id=row[6]
                )
                details = json.loads(decrypted_details_json)
                event = AuditEvent(
                    event_id=row[0],
                    timestamp=datetime.datetime.fromisoformat(row[1]),
                    level=AuditLevel(row[2]),
                    category=EventCategory(row[3]),
                    event_type=row[4],
                    user_id=row[5],
                    agent_id=row[6],
                    resource=row[7],
                    action=row[8],
                    result=row[9],
                    details=details,
                    source_ip=row[11],
                    session_id=row[12],
                    correlation_id=row[13],
                )
                events.append(event)
            except Exception as exc:
                print(
                    f"Error al reconstruir AuditEvent desde la BD. "
                    f"Tipo: {type(exc).__name__}, Error: {exc}, Fila de datos: {row}"
                )
        return events
