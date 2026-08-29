"""
RayRabbit OSS — Sovereign Memory SDK Node
========================================
Nodo SDK soberano de memoria declarativa por sesión.
Implementa el estándar Anthropic MCP resources/read para responder a la URI `rayrabbit://memory/{session_id}`
y la herramienta `save_memory_fact`.

Conexión: WebSocket saliente soberano a ws://127.0.0.1:8005/ws
Categoría MCP: "memory"
Persistencia: SQLite local cifrada en `.rayrabbit_data/memory/memory.db`

SPDX-License-Identifier: Apache-2.0
"""
import os
import sys
import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from rayrabbit_client import RayRabbitNode

# ─── Configuración de Persistencia SQLite y Directorios ───────────────────────
DATA_DIR = Path(".rayrabbit_data/memory")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "memory.db"


class SovereignMemoryStore:
    """Gestor de almacenamiento SQLite privado para el nodo de memoria."""
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    fact_key TEXT NOT NULL,
                    fact_value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    timestamp TEXT NOT NULL,
                    UNIQUE(session_id, fact_key) ON CONFLICT REPLACE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON session_facts(session_id)")

    def save_fact(self, session_id: str, fact_key: str, fact_value: Union[str, Dict[str, Any], Any], category: str = "general") -> bool:
        try:
            if not isinstance(fact_value, str):
                fact_value = json.dumps(fact_value, ensure_ascii=False)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO session_facts (session_id, fact_key, fact_value, category, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, fact_key, fact_value, category, datetime.now().isoformat())
                )
            return True
        except Exception:
            return False

    def get_facts_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT fact_key, fact_value, category, timestamp FROM session_facts WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]


store = SovereignMemoryStore(DB_PATH)

# ─── Inicialización del Nodo SDK Soberano ──────────────────────────────────────
HUB_WS_URL = os.getenv("RAYRABBIT_HUB_WS_URL", "ws://127.0.0.1:8005/ws")

node = RayRabbitNode(
    name="sovereign_memory_node",
    hub_url=HUB_WS_URL
)


# ─── Herramientas y Recursos MCP ───────────────────────────────────────────────

@node.tool
async def save_memory_fact(session_id: str, fact_key: str, fact_value: Union[str, Dict[str, Any], Any] = "", category: str = "general") -> str:
    """Guarda o actualiza un hecho/preferencia del usuario asociado a una sesión específica (acepta texto o dict)."""
    if not session_id or not fact_key or fact_value is None:
        return "Error: 'session_id', 'fact_key' y 'fact_value' son requeridos."

    success = store.save_fact(session_id, fact_key, fact_value, category)
    if success:
        return f"Éxito: Hecho '{fact_key}' guardado para la sesión '{session_id}'."
    return f"Error: No se pudo guardar el hecho en la base de datos de memoria."


@node.tool
async def read_session_memory(session_id: str) -> str:
    """Lee y retorna en formato JSON el conjunto de hechos y contexto guardados para la sesión."""
    facts = store.get_facts_for_session(session_id)
    if not facts:
        return json.dumps({"session_id": session_id, "facts_count": 0, "facts": []}, indent=2)

    return json.dumps({
        "session_id": session_id,
        "facts_count": len(facts),
        "facts": facts
    }, indent=2)


# Registramos la función de proveedor de recurso para resources/read
def get_memory_resource_content(uri: str) -> str:
    """Resuelve la URI rayrabbit://memory/{session_id} retornando JSON."""
    session_id = uri.replace("rayrabbit://memory/", "").strip()
    facts = store.get_facts_for_session(session_id)
    return json.dumps({
        "uri": uri,
        "session_id": session_id,
        "facts": facts
    })


# ─── Arranque del Nodo SDK Soberano ───────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 Iniciando SovereignMemoryNode conectándose a {HUB_WS_URL}...")
    asyncio.run(node.connect())
