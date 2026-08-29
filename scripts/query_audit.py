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
Consulta específica de eventos de seguridad en la BD de Auditoría MAESTRO.
Muestra: eventos de validación fallida, ataques bloqueados, advertencias de seguridad.
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path.cwd() / "audit_logs" / "audit.db"
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

SEP = "=" * 72
sep = "-" * 72

print(SEP)
print("  RayRabbit MAESTRO -- Reporte de Auditoria de Seguridad")
print(f"  BD: {DB_PATH}")
print(f"  Total registros: ", end="")
cur.execute("SELECT COUNT(*) FROM audit_events")
print(cur.fetchone()[0])
print(SEP)

# ── 1. Estadísticas por nivel ─────────────────────────────────────────────────
print("\n[1] DISTRIBUCION POR NIVEL (level)")
print(sep)
cur.execute("""
    SELECT level, COUNT(*) as total
    FROM audit_events
    GROUP BY level
    ORDER BY total DESC
""")
for row in cur.fetchall():
    bar = "#" * min(row["total"], 40)
    print(f"  {row['level']:15} : {row['total']:5}  {bar}")

# ── 2. Estadísticas por categoría ─────────────────────────────────────────────
print("\n[2] DISTRIBUCION POR CATEGORIA")
print(sep)
cur.execute("""
    SELECT category, COUNT(*) as total
    FROM audit_events
    GROUP BY category
    ORDER BY total DESC
""")
for row in cur.fetchall():
    print(f"  {row['category']:35} : {row['total']:5}")

# ── 3. Eventos WARNING (alertas de seguridad) ─────────────────────────────────
print("\n[3] TODOS LOS EVENTOS WARNING / ERROR (alertas de seguridad)")
print(sep)
cur.execute("""
    SELECT event_id, timestamp, level, category, event_type,
           agent_id, action, result, source_ip, session_id, correlation_id
    FROM audit_events
    WHERE level IN ('warning', 'error', 'critical')
    ORDER BY timestamp DESC
    LIMIT 30
""")
rows = cur.fetchall()
print(f"  Encontrados: {len(rows)} eventos de alerta\n")
for i, row in enumerate(rows, 1):
    print(f"  [{i:02d}] {row['timestamp']}")
    print(f"       Nivel      : {row['level'].upper()}")
    print(f"       Categoria  : {row['category']}")
    print(f"       Tipo       : {row['event_type']}")
    print(f"       Agente     : {row['agent_id']}")
    print(f"       Accion     : {row['action']}")
    print(f"       Resultado  : {row['result']}")
    if row['source_ip']:
        print(f"       IP Origen  : {row['source_ip']}")
    if row['session_id']:
        print(f"       Session    : {row['session_id']}")
    if row['correlation_id']:
        print(f"       Correlacion: {row['correlation_id']}")
    print()

# ── 4. Eventos de tipo específico de validación / acceso ─────────────────────
print("\n[4] EVENTOS DE CONTROL DE ACCESO Y VALIDACION")
print(sep)
cur.execute("""
    SELECT event_id, timestamp, level, category, event_type,
           agent_id, action, result, source_ip, correlation_id
    FROM audit_events
    WHERE category IN ('access_control', 'data_validation', 'authentication',
                       'authorization', 'security_event')
       OR event_type LIKE '%BLOCK%'
       OR event_type LIKE '%DENY%'
       OR event_type LIKE '%REJECT%'
       OR event_type LIKE '%INVALID%'
       OR event_type LIKE '%THREAT%'
       OR event_type LIKE '%ATTACK%'
       OR event_type LIKE '%INJECT%'
       OR event_type LIKE '%SANITIZ%'
       OR event_type LIKE '%VALIDATION%'
       OR event_type LIKE '%AUTH%'
    ORDER BY timestamp DESC
    LIMIT 30
""")
rows = cur.fetchall()
print(f"  Encontrados: {len(rows)} eventos de control/validacion\n")
for i, row in enumerate(rows, 1):
    marker = ">>>" if row['result'] in ('FAILURE', 'BLOCKED', 'DENIED', 'REJECTED') else "   "
    print(f"  {marker} [{i:02d}] {row['timestamp']}")
    print(f"         Nivel      : {row['level'].upper()}")
    print(f"         Categoria  : {row['category']}")
    print(f"         Tipo Evento: {row['event_type']}")
    print(f"         Agente     : {row['agent_id']}")
    print(f"         Accion     : {row['action']}")
    print(f"         Resultado  : {row['result']}")
    if row['source_ip']:
        print(f"         IP Origen  : {row['source_ip']}")
    if row['correlation_id']:
        print(f"         Correlacion: {row['correlation_id']}")
    print()

# ── 5. Resumen de hoy (2026-06-03) ────────────────────────────────────────────
print("\n[5] ACTIVIDAD DE HOY (2026-06-03)")
print(sep)
cur.execute("""
    SELECT level, category, event_type, agent_id, action, result, timestamp
    FROM audit_events
    WHERE timestamp LIKE '2026-06-03%'
    ORDER BY timestamp DESC
    LIMIT 20
""")
rows = cur.fetchall()
print(f"  Registros de hoy encontrados: {len(rows)}\n")
for i, row in enumerate(rows, 1):
    print(f"  [{i:02d}] {row['timestamp']}  [{row['level'].upper():8}]  "
          f"{row['event_type']:40}  {row['agent_id']}  -> {row['result']}")

# ── 6. Últimos registros del test de SQLi (hoy) ───────────────────────────────
print("\n[6] BUSQUEDA ESPECIFICA: Test SQLi/Prompt-Injection (hoy)")
print(sep)
cur.execute("""
    SELECT *
    FROM audit_events
    WHERE timestamp LIKE '2026-06-03%'
      AND (
           event_type LIKE '%VALID%'
        OR event_type LIKE '%SANIT%'
        OR event_type LIKE '%BLOCK%'
        OR event_type LIKE '%THREAT%'
        OR event_type LIKE '%INJECT%'
        OR event_type LIKE '%REJECT%'
        OR result LIKE '%BLOCK%'
        OR result LIKE '%FAIL%'
        OR level IN ('warning','error','critical')
      )
    ORDER BY timestamp DESC
""")
rows = cur.fetchall()
if rows:
    print(f"  [!!!] {len(rows)} eventos de validacion/seguridad encontrados hoy:\n")
    for i, row in enumerate(rows, 1):
        print(f"  [ATAQUE #{i}] ─────────────────────────────────────────────────")
        for key in row.keys():
            val = row[key]
            if val is not None and not isinstance(val, (bytes, bytearray)):
                print(f"    {key:20}: {val}")
        print()
else:
    print("  No se hallaron eventos de validacion/bloqueo especificos de hoy.")
    print("  Nota: El campo 'details' esta cifrado con AES-256-GCM (MAESTRO E2E).")
    print("  Los metadatos del evento si son legibles en texto claro.")

conn.close()
print("\n" + SEP)
print("  Reporte completado.")
print(SEP)
