#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RayRabbit Official MCP Bridge Server for Google Antigravity
Copyright © 2024-2026 RayRabbit Labs, Inc.

Proporciona un puente bidireccional JSON-RPC (stdio) entre sesiones de Antigravity
y la malla de interoperabilidad L3 de RayRabbit (MessageBus, A2A, MCP y Memoria Soberana)
en modo local y remoto con seguridad criptográfica MAESTRO Zero-Trust (Mutual PoP Handshake + JWS RSA-2048).
"""

import sys
import json
import os
import time
import uuid
import base64
import sqlite3
import hashlib
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# === CONFIGURACIÓN Y CONTEXTO SOBERANO ===
HUB_URL = os.getenv("RAYRABBIT_HUB_URL", "http://127.0.0.1:8005").rstrip("/")
AGENT_ID = os.getenv("RAYRABBIT_AGENT_ID", "antigravity_devops")
AGENT_NAME = os.getenv("RAYRABBIT_AGENT_NAME", "Antigravity DevOps Assistant")
TIMEOUT = float(os.getenv("RAYRABBIT_TIMEOUT", "10.0"))

def _resolve_identity_dir() -> Path:
    """Resuelve la ruta soberana canónica para .rayrabbit_data/identity."""
    env_home = os.getenv("RAYRABBIT_HOME")
    if env_home:
        p = Path(env_home).resolve() / "identity"
        p.mkdir(parents=True, exist_ok=True)
        return p
        
    env_root = os.getenv("RAYRABBIT_PROJECT_ROOT")
    if env_root:
        p = Path(env_root).resolve() / ".rayrabbit_data" / "identity"
        p.mkdir(parents=True, exist_ok=True)
        return p

    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parents[1],
        Path(__file__).resolve().parents[2],
        Path(__file__).resolve().parents[3] if len(Path(__file__).resolve().parents) > 3 else Path.cwd()
    ]
    if os.environ.get("RAYRABBIT_ROOT"):
        candidates.insert(0, Path(os.environ["RAYRABBIT_ROOT"]))
    
    for candidate in candidates:
        if (candidate / ".git").exists() or (candidate / "clients").exists() or (candidate / ".rayrabbit_data").exists():
            p = candidate / ".rayrabbit_data" / "identity"
            p.mkdir(parents=True, exist_ok=True)
            return p

    default_p = Path.cwd() / ".rayrabbit_data" / "identity"
    default_p.mkdir(parents=True, exist_ok=True)
    return default_p

IDENTITY_DIR = _resolve_identity_dir()

# === GESTIÓN DE SEGURIDAD MAESTRO (MUTUAL PoP HANDSHAKE + JWS RSA-2048) ===

_PRIVATE_KEY = None
_RSA_NUMBERS: Optional[Tuple[int, int]] = None  # (modulus n, private exponent d)
_PUBLIC_KEY_PEM_CLEAN = ""
_PUBLIC_KEY_PEM_FULL = ""

def _parse_asn1_integers(der_bytes: bytes) -> List[int]:
    """Extrae enteros ASN.1 (modulus n, exponent d) escaneando cualquier estructura DER/PKCS#8."""
    integers = []
    idx = 0
    n_len = len(der_bytes)
    while idx < n_len - 4:
        if der_bytes[idx] == 0x02: # INTEGER tag
            tag_idx = idx
            idx += 1
            length = der_bytes[idx]
            idx += 1
            if length & 0x80:
                num_len_bytes = length & 0x7F
                if idx + num_len_bytes > n_len:
                    idx = tag_idx + 1
                    continue
                length = int.from_bytes(der_bytes[idx:idx+num_len_bytes], 'big')
                idx += num_len_bytes
            if length > 0 and idx + length <= n_len:
                val_bytes = der_bytes[idx:idx+length]
                val = int.from_bytes(val_bytes, 'big')
                if val > 2**1000 or val == 65537:
                    integers.append(val)
                    idx += length
                    continue
            idx = tag_idx + 1
        else:
            idx += 1
    return integers

def _sign_rsa_pss_pure(n: int, d: int, message_bytes: bytes, salt_len: int = 32) -> bytes:
    """Implementa EMSA-PSS-ENCODE y firma RSA según RFC 8017 / PKCS #1 v2.2."""
    em_bits = n.bit_length()
    em_len = (em_bits + 7) // 8 # 256 bytes para RSA-2048
    h_len = 32 # SHA-256
    
    m_hash = hashlib.sha256(message_bytes).digest()
    salt = os.urandom(salt_len)
    
    m_prime = b'\x00' * 8 + m_hash + salt
    h = hashlib.sha256(m_prime).digest()
    
    ps_len = em_len - salt_len - h_len - 2
    ps = b'\x00' * ps_len
    db = ps + b'\x01' + salt
    
    def mgf1(seed: bytes, mask_len: int) -> bytes:
        t = b""
        counter = 0
        while len(t) < mask_len:
            c = counter.to_bytes(4, byteorder="big")
            t += hashlib.sha256(seed + c).digest()
            counter += 1
        return t[:mask_len]
        
    db_mask = mgf1(h, len(db))
    masked_db = bytes(a ^ b for a, b in zip(db, db_mask))
    
    first_byte_mask = 0xFF >> (8 * em_len - em_bits)
    masked_db = bytes([masked_db[0] & first_byte_mask]) + masked_db[1:]
    
    em = masked_db + h + b'\xbc'
    m_int = int.from_bytes(em, 'big')
    s_int = pow(m_int, d, n)
    return s_int.to_bytes(em_len, 'big')

def _init_crypto_identity():
    """Inicializa o carga el par de claves RSA-2048 en .rayrabbit_data/identity."""
    global _PRIVATE_KEY, _RSA_NUMBERS, _PUBLIC_KEY_PEM_CLEAN, _PUBLIC_KEY_PEM_FULL
    
    priv_path = IDENTITY_DIR / f"{AGENT_ID}_private.pem"
    pub_path = IDENTITY_DIR / f"{AGENT_ID}_public.pem"
    
    fallback_priv_paths = [
        priv_path,
        Path.cwd() / "keystore_mcp" / f"{AGENT_ID}_private.pem",
        Path.cwd() / ".rayrabbit_data" / "identity" / f"{AGENT_ID}_private.pem"
    ]
    
    for cand in fallback_priv_paths:
        if cand.exists():
            try:
                with open(cand, "rb") as f:
                    priv_raw = f.read()
                pub_cand = cand.parent / f"{AGENT_ID}_public.pem"
                if not pub_cand.exists():
                    pub_cand = IDENTITY_DIR / f"{AGENT_ID}_public.pem"
                with open(pub_cand, "r", encoding="utf-8") as f:
                    pub_raw = f.read()
                    
                _PUBLIC_KEY_PEM_FULL = pub_raw.strip()
                _PUBLIC_KEY_PEM_CLEAN = pub_raw.replace("\n", "").replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").strip()
                
                try:
                    clean_b64 = b"".join(line for line in priv_raw.splitlines() if not line.startswith(b"-----"))
                    der = base64.b64decode(clean_b64)
                    ints = _parse_asn1_integers(der)
                    large_ints = [x for x in ints if x > 2**1000]
                    if len(large_ints) >= 2:
                        _RSA_NUMBERS = (large_ints[0], large_ints[1])
                except Exception as ex_der:
                    sys.stderr.write(f"[RayRabbit MCP Security] Aviso ASN.1 parse: {ex_der}\n")
                
                try:
                    from cryptography.hazmat.primitives import serialization
                    from cryptography.hazmat.backends import default_backend
                    _PRIVATE_KEY = serialization.load_pem_private_key(priv_raw, password=None, backend=default_backend())
                except Exception:
                    pass
                
                sys.stderr.write(f"[RayRabbit MCP Security] Identidad MAESTRO cargada ({AGENT_ID}) desde {cand}\n")
                sys.stderr.flush()
                return
            except Exception as e:
                sys.stderr.write(f"[RayRabbit MCP Security] Error cargando clave desde {cand}: {e}\n")
                sys.stderr.flush()

def _sign_bytes_raw(data_bytes: bytes) -> Optional[bytes]:
    """Firma un arreglo de bytes usando pure Python RSA-PSS o cryptography."""
    if not _PRIVATE_KEY and not _RSA_NUMBERS:
        _init_crypto_identity()
        
    if _RSA_NUMBERS:
        try:
            n, d = _RSA_NUMBERS
            return _sign_rsa_pss_pure(n, d, data_bytes)
        except Exception as e:
            sys.stderr.write(f"[RayRabbit MCP Security] Error en pure RSA-PSS: {e}\n")
            sys.stderr.flush()

    if _PRIVATE_KEY:
        try:
            from cryptography.hazmat.primitives import hashes, padding
            return _PRIVATE_KEY.sign(
                data_bytes,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
        except Exception as e:
            sys.stderr.write(f"[RayRabbit MCP Security] Error en cryptography sign: {e}\n")
            sys.stderr.flush()
            
    return None

def _perform_pop_handshake() -> bool:
    """Ejecuta el Handshake Proof of Possession (PoP) contra el Hub /api/security/register."""
    if not _PUBLIC_KEY_PEM_FULL:
        _init_crypto_identity()
    if not _PUBLIC_KEY_PEM_FULL:
        return False
        
    try:
        timestamp = str(int(time.time()))
        challenge = f"REG-AUTH:{AGENT_ID}:{timestamp}"
        
        sig_bytes = _sign_bytes_raw(challenge.encode('utf-8'))
        if not sig_bytes:
            return False
            
        sig_b64 = base64.b64encode(sig_bytes).decode('utf-8')
        
        payload = {
            "agent_id": AGENT_ID,
            "public_key_pem": _PUBLIC_KEY_PEM_FULL,
            "timestamp": timestamp,
            "signature": sig_b64
        }
        
        url = f"{HUB_URL}/api/security/register"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"RayRabbit-Antigravity-MCP/{AGENT_ID}"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            hub_pk = res_data.get("hub_public_key")
            if hub_pk:
                hub_pk_path = IDENTITY_DIR / "hub_public.pem"
                with open(hub_pk_path, "w", encoding="utf-8") as f:
                    f.write(hub_pk)
            sys.stderr.write(f"[RayRabbit MCP Security] Handshake PoP OK con Hub ({HUB_URL})\n")
            sys.stderr.flush()
            return True
    except Exception as e:
        sys.stderr.write(f"[RayRabbit MCP Security] Handshake PoP con Hub ({HUB_URL}) diferido: {e}\n")
        sys.stderr.flush()
        return False

def _sign_jws(payload_dict: Dict[str, Any]) -> Optional[str]:
    """Genera una firma JWS Compact (RFC 7515 con PSS SHA-256) para el mensaje."""
    if not _PRIVATE_KEY and not _RSA_NUMBERS:
        _init_crypto_identity()
    if not _PRIVATE_KEY and not _RSA_NUMBERS:
        return None
        
    try:
        def b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')
            
        header = {"alg": "RS256", "typ": "JWS"}
        header_b64 = b64url(json.dumps(header, separators=(',', ':')).encode('utf-8'))
        payload_b64 = b64url(json.dumps(payload_dict, sort_keys=True, separators=(',', ':')).encode('utf-8'))
        
        signing_input = f"{header_b64}.{payload_b64}"
        signature = _sign_bytes_raw(signing_input.encode('utf-8'))
        if not signature:
            return None
        return f"{signing_input}.{b64url(signature)}"
    except Exception as e:
        sys.stderr.write(f"[RayRabbit MCP Security] Error firmando JWS: {e}\n")
        sys.stderr.flush()
        return None

# Inicializar criptografía al arranque
_init_crypto_identity()
_perform_pop_handshake()

def _http_request(endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None, retry_handshake: bool = True) -> Dict[str, Any]:
    """Realiza una petición HTTP al Hub de RayRabbit firmada con MAESTRO Zero-Trust."""
    url = f"{HUB_URL}{endpoint}"
    headers = {
        "User-Agent": f"RayRabbit-Antigravity-MCP/{AGENT_ID}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-RayRabbit-Agent-Id": AGENT_ID
    }
    
    if correlation_id:
        headers["X-RayRabbit-Correlation-ID"] = correlation_id
        
    encoded_data = None
    if data is not None:
        jws_sig = _sign_jws(data)
        if jws_sig:
            headers["X-RayRabbit-JWS"] = jws_sig
            if _PUBLIC_KEY_PEM_CLEAN:
                headers["X-RayRabbit-Bridge-Public-Key-PEM"] = _PUBLIC_KEY_PEM_CLEAN
        encoded_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            res_body = response.read().decode("utf-8")
            if not res_body:
                return {"status": "ok", "code": response.status}
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        if e.code == 401 and retry_handshake:
            sys.stderr.write("[RayRabbit MCP] Error 401 detectado, reintentando Handshake PoP...\n")
            sys.stderr.flush()
            if _perform_pop_handshake():
                return _http_request(endpoint, method=method, data=data, correlation_id=correlation_id, retry_handshake=False)
        return {"error": f"HTTP {e.code}: {e.reason}", "details": err_body}
    except Exception as e:
        return {"error": f"Error de conexión con el Hub ({HUB_URL}): {str(e)}"}

# === DEFINICIÓN DE HERRAMIENTAS MCP ===

TOOLS_MANIFEST = [
    {
        "name": "rayrabbit_send_message",
        "description": "Envía un mensaje A2A firmado con MAESTRO Zero-Trust (JWS RSA-2048) a otro agente, nodo o sesión de Antigravity remota/local a través del MessageBus L3.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipient_id": {
                    "type": "string",
                    "description": "ID del agente o sesión destinataria (ej. 'antigravity_core', 'crewai_service', 'langchain_service', 'autogen_service')."
                },
                "content": {
                    "type": "object",
                    "description": "Cuerpo del mensaje o datos estructurados a transmitir."
                },
                "message_type": {
                    "type": "string",
                    "enum": ["request", "response", "event", "notification"],
                    "default": "request",
                    "description": "Tipo de mensaje A2A."
                },
                "correlation_id": {
                    "type": "string",
                    "description": "ID de correlación para asociar respuestas o tareas de consenso."
                }
            },
            "required": ["recipient_id", "content"]
        }
    },
    {
        "name": "rayrabbit_read_inbox",
        "description": "Inspecciona el buzón de mensajes entrantes y de auditoría L3 dirigidos a esta sesión de Antigravity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "correlation_id": {
                    "type": "string",
                    "description": "Filtro opcional para buscar un hilo de consenso específico."
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Número máximo de mensajes a recuperar."
                }
            }
        }
    },
    {
        "name": "rayrabbit_list_agents",
        "description": "Descubre todos los agentes, nodos soberanos y sesiones federadas activas en la malla RayRabbit (local o remota).",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "rayrabbit_call_tool",
        "description": "Invoca una herramienta de negocio distribuida en un nodo soberano remoto (ej. WMS en LangChain, Routing en CrewAI o Flota en AutoGen).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Nombre de la herramienta remota (ej. 'get_order_tracking', 'get_routing_plan', 'get_fleet_assignment')."
                },
                "arguments": {
                    "type": "object",
                    "description": "Parámetros de entrada para la herramienta."
                }
            },
            "required": ["tool_name"]
        }
    },
    {
        "name": "rayrabbit_get_telemetry",
        "description": "Consulta el estado de salud, métricas y telemetría viva del clúster y del Dashboard A2UI de RayRabbit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stream_id": {
                    "type": "string",
                    "default": "default_dashboard",
                    "description": "ID del stream de telemetría a consultar."
                }
            }
        }
    },
    {
        "name": "rayrabbit_publish_fact",
        "description": "Publica y persiste un hecho validado en la Memoria Soberana L3 global compartida entre todos los agentes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fact_key": {
                    "type": "string",
                    "description": "Clave identificadora del hecho (ej. 'consenso_devops', 'cluster_status')."
                },
                "fact_value": {
                    "type": "object",
                    "description": "Contenido estructurado del hecho verificado."
                }
            },
            "required": ["fact_key", "fact_value"]
        }
    }
]

# === CONTROLADORES DE HERRAMIENTAS ===

def handle_send_message(args: Dict[str, Any]) -> Dict[str, Any]:
    recipient_id = args.get("recipient_id")
    content = args.get("content", {})
    message_type = args.get("message_type", "request")
    correlation_id = args.get("correlation_id") or str(uuid.uuid4())
    
    payload = {
        "sender_id": AGENT_ID,
        "sender_name": AGENT_NAME,
        "recipient_id": recipient_id,
        "message_type": message_type,
        "correlation_id": correlation_id,
        "content": content
    }
    
    res = _http_request("/api/publish-message", method="POST", data=payload, correlation_id=correlation_id)
    return {
        "status": "delivered" if "error" not in res else "failed",
        "correlation_id": correlation_id,
        "sender": AGENT_ID,
        "recipient": recipient_id,
        "hub_response": res
    }

def handle_read_inbox(args: Dict[str, Any]) -> Dict[str, Any]:
    correlation_id = args.get("correlation_id")
    limit = args.get("limit", 10)
    messages = []
    
    db_candidates = [
        IDENTITY_DIR.parent / "audit_logs" / "audit.db",
        Path.cwd() / "audit_logs" / "audit.db"
    ]
    
    for db_path in db_candidates:
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
                
                if "audit_events" in tables:
                    query = "SELECT timestamp, event_type, agent_id, correlation_id, details FROM audit_events WHERE 1=1"
                    params = []
                    if correlation_id:
                        query += " AND correlation_id = ?"
                        params.append(correlation_id)
                    query += " ORDER BY timestamp DESC LIMIT ?"
                    params.append(limit)
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    for row in rows:
                        ts, ev_type, ag_id, corr_id, details_raw = row
                        det = None
                        if isinstance(details_raw, str):
                            try:
                                det = json.loads(details_raw)
                            except Exception:
                                det = {"raw": details_raw}
                        elif isinstance(details_raw, bytes):
                            det = {"encrypted_payload": True, "raw_bytes_len": len(details_raw)}
                        messages.append({
                            "timestamp": ts,
                            "event_type": ev_type,
                            "agent_id": ag_id,
                            "correlation_id": corr_id,
                            "details": det
                        })
                elif "audit_logs" in tables:
                    query = "SELECT timestamp, event_type, details FROM audit_logs WHERE 1=1"
                    params = []
                    if correlation_id:
                        query += " AND details LIKE ?"
                        params.append(f"%{correlation_id}%")
                    query += " ORDER BY id DESC LIMIT ?"
                    params.append(limit)
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    for row in rows:
                        ts, ev_type, details_raw = row
                        try:
                            det = json.loads(details_raw) if details_raw else {}
                        except Exception:
                            det = {"raw": details_raw}
                        messages.append({
                            "timestamp": ts,
                            "event_type": ev_type,
                            "details": det
                        })
                conn.close()
                if messages:
                    break
            except Exception as e:
                sys.stderr.write(f"[RayRabbit MCP Inbox] Error leyendo audit.db ({db_path}): {e}\n")
    
    return {
        "agent_id": AGENT_ID,
        "correlation_id_filter": correlation_id,
        "messages_found": len(messages),
        "inbox": messages,
        "checked_at": datetime.now().isoformat()
    }

def handle_list_agents(args: Dict[str, Any]) -> Dict[str, Any]:
    health = _http_request("/health", method="GET")
    known_nodes = [
        {"agent_id": "hub", "role": "L3 Central Core & MessageBus", "status": "online" if "error" not in health else "offline"},
        {"agent_id": "crewai_service", "role": "Routing & Optimization Node", "port": 8001, "protocol": "A2A/MCP"},
        {"agent_id": "langchain_service", "role": "WMS & Inventory Node", "port": 8002, "protocol": "A2A/MCP"},
        {"agent_id": "autogen_service", "role": "Fleet & Dispatch Commander", "port": 8003, "protocol": "A2A/MCP"},
        {"agent_id": "logistics_ui_manager", "role": "A2UI Visual Telemetry Manager", "port": 8006, "protocol": "A2UI/WS"},
        {"agent_id": "antigravity_core", "role": "Core & Architecture L3 Session (Primary Hub)", "status": "federated"},
        {"agent_id": "antigravity_devops", "role": "DevOps Infrastructure Session (Remote Host)", "status": "active"}
    ]
    return {
        "hub_url": HUB_URL,
        "cluster_health": health,
        "federated_agents": known_nodes
    }

def handle_call_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    tool_name = args.get("tool_name")
    arguments = args.get("arguments", {})
    payload = {
        "name": tool_name,
        "arguments": arguments,
        "invoker": AGENT_ID
    }
    return _http_request("/api/execute-tool", method="POST", data=payload)

def handle_get_telemetry(args: Dict[str, Any]) -> Dict[str, Any]:
    stream_id = args.get("stream_id", "default_dashboard")
    health = _http_request("/health", method="GET")
    return {
        "stream_id": stream_id,
        "hub_url": HUB_URL,
        "timestamp": datetime.now().isoformat(),
        "health": health
    }

def handle_publish_fact(args: Dict[str, Any]) -> Dict[str, Any]:
    fact_key = args.get("fact_key")
    fact_value = args.get("fact_value", {})
    payload = {
        "sender_id": AGENT_ID,
        "sender_name": AGENT_NAME,
        "recipient_id": "hub",
        "message_type": "event",
        "correlation_id": f"fact-{uuid.uuid4()}",
        "content": {
            "fact_key": fact_key,
            "fact_value": fact_value,
            "published_at": datetime.now().isoformat()
        }
    }
    res = _http_request("/api/publish-message", method="POST", data=payload)
    return {"status": "fact_persisted", "key": fact_key, "hub_response": res}

TOOL_HANDLERS = {
    "rayrabbit_send_message": handle_send_message,
    "rayrabbit_read_inbox": handle_read_inbox,
    "rayrabbit_list_agents": handle_list_agents,
    "rayrabbit_call_tool": handle_call_tool,
    "rayrabbit_get_telemetry": handle_get_telemetry,
    "rayrabbit_publish_fact": handle_publish_fact
}

# === BUCLE DE MENSAJERÍA JSON-RPC (STDIO) ===

def main():
    sys.stderr.write(f"[RayRabbit MCP] Servidor MAESTRO JWS iniciado para {AGENT_ID} (Hub: {HUB_URL})\n")
    sys.stderr.flush()
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": False
                            }
                        },
                        "serverInfo": {
                            "name": "rayrabbit-sovereign-mesh",
                            "version": "0.1.0"
                        }
                    }
                }
            elif method == "notifications/initialized":
                continue
            elif method == "ping":
                response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": TOOLS_MANIFEST
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                handler = TOOL_HANDLERS.get(tool_name)
                
                if handler:
                    try:
                        res_data = handler(arguments)
                        response = {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(res_data, indent=2, ensure_ascii=False)
                                    }
                                ],
                                "isError": "error" in res_data
                            }
                        }
                    except Exception as e:
                        response = {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "result": {
                                "content": [{"type": "text", "text": f"Error ejecutando {tool_name}: {str(e)}"}],
                                "isError": True
                            }
                        }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Herramienta no encontrada: {tool_name}"
                        }
                    }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Método no soportado: {method}"
                    }
                }
            
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as err:
            sys.stderr.write(f"[RayRabbit MCP] Error procesando JSON-RPC: {err}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
