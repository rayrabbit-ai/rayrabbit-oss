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
Módulo de almacenamiento persistente para el TaskEngine (MCP v2).
Provee la base de datos local SQLite para estado y reanudabilidad de Tareas.
"""

import sqlite3
import json
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class TaskStore:
    """
    Almacenamiento durable separado del bus para que el protocolo sea stateless
    pero la ejecución sea reanudable.
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Inicializa la estructura de la base de datos SQLite."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            # Activar el modo WAL para concurrencia libre de bloqueos
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            # Tabla de tareas principales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    tenant_id TEXT,
                    correlation_id TEXT,
                    parent_task_id TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Tabla del log de auditoría inmutable (Eventos de Tarea)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    parent_task_id TEXT,
                    event_type TEXT,
                    step TEXT,
                    payload TEXT,
                    signature TEXT,
                    nonce TEXT,
                    policy_decision TEXT,
                    hash_chain TEXT,
                    checkpoint_ref TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
                )
            ''')
            
            # --- MIGRACIONES DINÁMICAS (Para bases de datos existentes con esquemas desactualizados) ---
            # 1. Verificar y migrar 'tasks'
            cursor.execute("PRAGMA table_info(tasks)")
            existing_tasks_cols = {col[1] for col in cursor.fetchall()}
            expected_tasks_cols = ["tenant_id", "correlation_id", "parent_task_id", "status"]
            for col in expected_tasks_cols:
                if col not in existing_tasks_cols:
                    try:
                        cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col} TEXT;")
                    except sqlite3.OperationalError:
                        pass
            
            # 2. Verificar y migrar 'task_events'
            cursor.execute("PRAGMA table_info(task_events)")
            existing_events_cols = {col[1] for col in cursor.fetchall()}
            expected_events_cols = [
                "parent_task_id", "event_type", "step", "payload", 
                "signature", "nonce", "policy_decision", "hash_chain", "checkpoint_ref"
            ]
            for col in expected_events_cols:
                if col not in existing_events_cols:
                    try:
                        cursor.execute(f"ALTER TABLE task_events ADD COLUMN {col} TEXT;")
                    except sqlite3.OperationalError:
                        pass
                    
            conn.commit()
    
    async def save_task_event(
        self,
        task_id: str,
        tenant_id: str,
        correlation_id: str,
        parent_task_id: Optional[str],
        status: str,
        event_type: str,
        step: str,
        payload: Dict[str, Any],
        signature: str,
        nonce: str = "",
        policy_decision: str = "ALLOW",
        hash_chain: Optional[str] = None,
        checkpoint_ref: Optional[str] = None
    ) -> str:
        """Persiste un evento transicional y actualiza el estado de la tarea. Retorna el hash_chain calculado."""
        def _save():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                cursor = conn.cursor()
                # Upsert de la tarea principal
                cursor.execute('''
                    INSERT INTO tasks (task_id, tenant_id, correlation_id, parent_task_id, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(task_id) DO UPDATE SET
                    status = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
                ''', (task_id, tenant_id, correlation_id, parent_task_id, status))
                
                # Calcular el hash_chain acumulado
                actual_hash = hash_chain
                if not actual_hash:
                    cursor.execute('SELECT hash_chain FROM task_events WHERE task_id = ? ORDER BY id DESC LIMIT 1', (task_id,))
                    row = cursor.fetchone()
                    previous_hash = row[0] if row else ""
                    
                    # Unir los campos de forma determinista para la cadena de bloques auditables
                    payload_json = json.dumps(payload, sort_keys=True)
                    current_data_str = f"{task_id}|{parent_task_id or ''}|{event_type}|{step}|{payload_json}|{signature}|{nonce}|{policy_decision}|{checkpoint_ref or ''}"
                    combined = current_data_str + previous_hash
                    actual_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()

                # Insertar el evento inmutable en el trail
                cursor.execute('''
                    INSERT INTO task_events (
                        task_id, parent_task_id, event_type, step, payload, 
                        signature, nonce, policy_decision, hash_chain, checkpoint_ref
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id, parent_task_id, event_type, step, json.dumps(payload),
                    signature, nonce, policy_decision, actual_hash, checkpoint_ref
                ))
                conn.commit()
                return actual_hash
                
        return await asyncio.to_thread(_save)

    async def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Recupera el último estado de una tarea y su cadena de eventos."""
        def _get():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
                task_row = cursor.fetchone()
                if not task_row:
                    return None
                    
                cursor.execute('SELECT * FROM task_events WHERE task_id = ? ORDER BY id ASC', (task_id,))
                events = [dict(row) for row in cursor.fetchall()]
                
                for event in events:
                    if event.get("payload"):
                        try:
                            event["payload"] = json.loads(event["payload"])
                        except Exception:
                            pass
                        
                return {
                    "task": dict(task_row),
                    "events": events
                }
        return await asyncio.to_thread(_get)

    async def list_tasks(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Retorna la lista de todas las tareas asociadas a un tenant."""
        def _list():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE tenant_id = ? ORDER BY updated_at DESC', (tenant_id,))
                return [dict(row) for row in cursor.fetchall()]
        return await asyncio.to_thread(_list)

