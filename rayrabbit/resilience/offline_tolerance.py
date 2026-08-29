"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import sqlite3
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..communication.message import Message
from ..utils.logger import get_logger

class OutboxStore:
    """
    Almacenamiento persistente basado en SQLite para mensajes pendientes de envío.
    Garantiza la tolerancia a desconexiones (Offline Tolerance).
    """
    
    def __init__(self, db_path: str = "rayrabbit-oss/resilience/outbox.db"):
        self.db_path = db_path
        self.logger = get_logger("OutboxStore")
        self._init_db()

    def _init_db(self):
        """Inicializa el esquema de la base de datos si no existe."""
        from pathlib import Path
        db_file = Path(self.db_path)
        if db_file.parent:
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outbox (
                    message_id TEXT PRIMARY KEY,
                    sender_id TEXT,
                    recipient_id TEXT,
                    message_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    timestamp TEXT,
                    attempts INTEGER DEFAULT 0,
                    last_attempt TEXT
                )
            """)
            conn.commit()
            
            # Limpieza inicial: eliminar mensajes que superen el límite de 3 intentos o requests antiguos de arranques previos
            conn.execute("DELETE FROM outbox WHERE attempts >= 3 OR message_type IN ('request', 'MessageType.REQUEST')")
            conn.commit()

    async def store_message(self, message: Message) -> bool:
        """Guarda un mensaje en el outbox para envío posterior."""
        try:
            # Serializar contenido si es dict
            content_str = json.dumps(message.content) if isinstance(message.content, dict) else message.content.hex() if isinstance(message.content, bytes) else str(message.content)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO outbox (message_id, sender_id, recipient_id, message_type, content, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    message.message_id,
                    message.sender_id,
                    message.recipient_id,
                    getattr(message.message_type, 'value', message.message_type),
                    content_str,
                    json.dumps(message.metadata or {}),
                    message.timestamp.isoformat()
                ))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error guardando mensaje en outbox: {e}")
            return False

    async def get_pending_messages(self, limit: int = 50) -> List[Message]:
        """Recupera mensajes pendientes de envío, descartando los que hayan expirado (>300s)."""
        messages = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM outbox ORDER BY timestamp ASC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                expired_ids = []
                now = datetime.now()
                for row in rows:
                    try:
                        msg_time = datetime.fromisoformat(row["timestamp"])
                        # Descartar mensajes de tipo request con más de 120s o eventos con más de 3600s
                        m_type = str(row["message_type"]).lower()
                        age_secs = (now - msg_time).total_seconds()
                        if ("request" in m_type and age_secs > 120) or age_secs > 3600:
                            expired_ids.append(row["message_id"])
                            continue

                        # Recrear el mensaje
                        try:
                            content = json.loads(row["content"])
                        except:
                            content = bytes.fromhex(row["content"])

                        msg = Message(
                            sender_id=row["sender_id"],
                            sender_name="",
                            recipient_id=row["recipient_id"],
                            content=content,
                            message_type=row["message_type"],
                            message_id=row["message_id"],
                            timestamp=msg_time,
                            metadata=json.loads(row["metadata"])
                        )
                        messages.append(msg)
                    except Exception as e:
                        self.logger.error(f"Error reconstruyendo mensaje {row['message_id']}: {e}")
                        expired_ids.append(row["message_id"])
                
                if expired_ids:
                    conn.executemany("DELETE FROM outbox WHERE message_id = ?", [(mid,) for mid in expired_ids])
                    conn.commit()
                    self.logger.info(f"Descartados {len(expired_ids)} mensajes expirados del outbox.")
            return messages
        except Exception as e:
            self.logger.error(f"Error recuperando mensajes del outbox: {e}")
            return []

    async def remove_message(self, message_id: str):
        """Elimina un mensaje tras envío exitoso."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM outbox WHERE message_id = ?", (message_id,))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error eliminando mensaje {message_id} del outbox: {e}")

    async def increment_attempt(self, message_id: str, max_attempts: int = 3):
        """Incrementa el contador de intentos y elimina el mensaje si supera max_attempts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE outbox 
                    SET attempts = attempts + 1, last_attempt = ? 
                    WHERE message_id = ?
                """, (datetime.now().isoformat(), message_id))
                conn.commit()
                
                # Obtener intentos actuales para verificar descarte
                cursor = conn.execute("SELECT attempts FROM outbox WHERE message_id = ?", (message_id,))
                row = cursor.fetchone()
                if row and row[0] >= max_attempts:
                    conn.execute("DELETE FROM outbox WHERE message_id = ?", (message_id,))
                    conn.commit()
                    self.logger.warning(f"Mensaje {message_id} descartado del outbox tras superar el límite de {max_attempts} intentos.")
        except Exception as e:
            self.logger.error(f"Error incrementando intentos de mensaje {message_id}: {e}")

class OfflineToleranceService:
    """
    Servicio que gestiona la tolerancia a desconexiones.
    Integra OutboxStore y maneja la lógica de reintento.
    """
    
    def __init__(self, message_bus, db_path: Optional[str] = None):
        self.message_bus = message_bus
        
        # Generación dinámica y soberana de la ruta de base de datos para evitar colisiones (Sin Estado Global)
        if not db_path:
            import os
            env_db = os.getenv("RAYRABBIT_OUTBOX_DB")
            if env_db:
                db_path = env_db
            else:
                import sys
                from pathlib import Path
                main_script = Path(sys.argv[0]).stem if sys.argv else "default"
                
                # Aislamiento por puerto si corre bajo uvicorn/fastapi para múltiples instancias
                port_suffix = ""
                for arg in sys.argv:
                    if "--port" in arg:
                        try:
                            if "=" in arg:
                                port_suffix = f"_{arg.split('=')[1]}"
                            else:
                                idx = sys.argv.index(arg)
                                if idx + 1 < len(sys.argv):
                                    port_suffix = f"_{sys.argv[idx + 1]}"
                        except Exception:
                            pass
                db_path = f"rayrabbit-oss/resilience/outbox_{main_script}{port_suffix}.db"
                
        self.store = OutboxStore(db_path)
        self.logger = get_logger("OfflineToleranceService")
        self.is_running = False
        self._sync_task: Optional[asyncio.Task] = None

    async def start(self):
        """Inicia el servicio de sincronización de fondo."""
        if not self.is_running:
            self.is_running = True
            self._sync_task = asyncio.create_task(self._sync_loop())
            self.logger.info("Servicio de Offline Tolerance iniciado.")

    async def stop(self):
        """Detiene el servicio."""
        self.is_running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Servicio de Offline Tolerance detenido.")

    async def handle_publish_failure(self, message: Message):
        """Maneja un fallo de publicación guardando el mensaje en el outbox."""
        self.logger.warning(f"Fallo de publicación para mensaje {message.message_id}. Guardando en outbox...")
        await self.store.store_message(message)

    async def sync_now(self) -> None:
        """Sincroniza inmediatamente los mensajes pendientes del outbox."""
        try:
            if self.message_bus.is_running:
                pending = await self.store.get_pending_messages()
                if pending:
                    self.logger.info(f"Procesando {len(pending)} mensajes pendientes en outbox...")
                    for msg in pending:
                        try:
                            # Intentar publicar de nuevo sin disparar este mismo handler
                            # Usamos un flag interno o bypass si es necesario, 
                            # pero publish normal debería estar bien si controlamos la recursión
                            success = await self.message_bus._handle_publish_direct(msg)
                            if success:
                                await self.store.remove_message(msg.message_id)
                                self.logger.info(f"Mensaje {msg.message_id} sincronizado exitosamente.")
                            else:
                                await self.store.increment_attempt(msg.message_id)
                        except Exception as e:
                            await self.store.increment_attempt(msg.message_id)
                            self.logger.error(f"Error reintentando mensaje {msg.message_id}: {e}")
        except Exception as e:
            self.logger.error(f"Error en sincronización outbox instantánea: {e}")

    def trigger_sync(self):
        """Dispara una sincronización en segundo plano de manera inmediata."""
        if self.is_running:
            asyncio.create_task(self.sync_now())

    async def _sync_loop(self):
        """Bucle de fondo para reintentar el envío de mensajes pendientes."""
        while self.is_running:
            await self.sync_now()
            await asyncio.sleep(60) # Intervalo de sincronización
