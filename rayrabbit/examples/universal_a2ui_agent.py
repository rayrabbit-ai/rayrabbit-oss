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
Generative A2UI Sovereign Service
Este servicio es un nodo soberano completo.
Implementa FastAPI, Handshake JWS y el endpoint /a2ui en el puerto 8006.
"""

import os
import asyncio
import json
import logging
import sys
import time
import uuid
import base64
import httpx
from pathlib import Path

# --- Carga de Entorno Soberano ---
from dotenv import load_dotenv
DOTENV_PATH = Path(__file__).parent / ".env"
if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
import uvicorn

# --- Integridad RayRabbit (Importaciones del Core) ---
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from rayrabbit.protocols.a2ui.agent import SovereignA2UIAgent
from rayrabbit.communication.message import Message, MessageType
from rayrabbit.communication.payload import UniversalPayloadUnwrapper
from rayrabbit.security.sovereign_identity import SovereignIdentity
from rayrabbit.protocols.mcp import MCPClient

# --- Configuración de Identidad y Red
AGENT_ID = os.getenv("AGENT_ID", "universal_a2ui_agent")
AGENT_NAME = os.getenv("AGENT_NAME", "Universal UI Agent")
PORT = 8006
ENDPOINT = f"http://127.0.0.1:{PORT}/a2ui"
HUB_URL = os.environ.get("RAYRABBIT_HUB_URL", "http://127.0.0.1:8005")
MCP_HUB_WS_URL = os.environ.get("RAYRABBIT_MCP_WS_URL", "ws://127.0.0.1:8005/ws")

mcp_client = MCPClient(MCP_HUB_WS_URL)

# Inicialización del Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(AGENT_ID)

# --- Gestor JWS Federado ---
class LocalJWSManager:
    """Gestor de JWS para el agente soberano (OSS)."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.identity = SovereignIdentity(agent_id)
        self.identity.ensure_identity()
        
        with open(self.identity.private_key_path, "rb") as key_file:
            self.private_key = serialization.load_pem_private_key(key_file.read(), password=None)
        
        with open(self.identity.public_key_path, "r") as key_file:
            self.public_key_pem = key_file.read()

    def _b64url(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    def sign_message(self, message: Dict[str, Any]) -> str:
        header = {"alg": "RS256", "typ": "JWS"}
        # Separadores consistentes (sin espacios) para interoperabilidad con MAESTRO Enterprise
        header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
        payload_json = json.dumps(message, sort_keys=True, separators=(',', ':')).encode('utf-8')
        
        header_b64 = self._b64url(header_json)
        payload_b64 = self._b64url(payload_json)
        
        signing_input = f"{header_b64}.{payload_b64}"
        signature = self.private_key.sign(
            signing_input.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return f"{signing_input}.{self._b64url(signature)}"

    def get_public_key_pem_clean(self) -> str:
        return self.public_key_pem.replace('\n', '').replace('-----BEGIN PUBLIC KEY-----', '').replace('-----END PUBLIC KEY-----', '').strip()

    def get_jws_headers(self, message: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "X-RayRabbit-JWS": self.sign_message(message),
            "X-RayRabbit-Agent-ID": self.agent_id,
            "X-RayRabbit-Bridge-Public-Key-PEM": self.get_public_key_pem_clean()
        }
        if correlation_id:
            headers["X-RayRabbit-Correlation-ID"] = correlation_id
        return headers

# Inicializar Gestor de Seguridad
jws_manager = LocalJWSManager(AGENT_ID)

app = FastAPI(title=f"RayRabbit A2UI Sovereign Service - {AGENT_ID}")

# --- Instancia del Agente con Inteligencia A2UI ---
class UniversalA2UIAgent(SovereignA2UIAgent):
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name)
        
        # Patrón de Memoria L2
        self.brain_dir = Path(".rayrabbit_data/brain") / self.id
        self.brain_dir.mkdir(parents=True, exist_ok=True)
        self.current_use_case = None  # None = sin workspace seleccionado (muestra saludo generico)
        self.orchestration_context = self._load_context()
        
        # Vincular gestor de seguridad para firma JWS
        self.maestro = jws_manager
        self.telemetry_lock = asyncio.Lock()
        
        # Cargar Configuración para Descubrimiento Dinámico
        from rayrabbit.utils.config import get_config_manager
        self.config_mgr = get_config_manager()
        try:
            root_config = Path.cwd() / "config.yaml"
            if root_config.exists():
                self.config_mgr.load_from_file(root_config)
        except Exception as e:
            logger.warning(f"No se pudo cargar config.yaml para descubrimiento: {e}")
            
        self.surface_id = "universal_dashboard"
            
        # Limpieza de Historial L2 (Sesión Viva)
        try:
            for f in ["conversation_history.json", "orchestration_context.json"]:
                p = self.brain_dir / f
                if p.exists(): p.unlink()
            self.conversation_history = {}
            self.orchestration_context = {"events": []}
            logger.info("🧠 Memoria L2 limpiada para nueva sesión A2UI.")
        except Exception as e:
            logger.error(f"Error limpiando memoria L2: {e}")

        # Inyectar Taxonomía Jerárquica de Herramientas (Hierarchical Tool Selection / Tool Routing)
        taxonomy_guide = """
## 🧭 Guía de Enrutamiento y Selección Jerárquica de Herramientas (Taxonomy-Guided Tool Routing)
Cuando tengas herramientas disponibles en la sesión (`tools`), selecciona la herramienta adecuada evaluando la taxonomía `category` y la descripción provista en su esquema JSON Schema:

1. **`category: cognitive` (Servicios Cognitivos / Frameworks Multi-Agente)**:
   - Utilízalas para orquestar flujos multi-agente, análisis colaborativo por roles o negociaciones conversacionales (CrewAI, AutoGen, LangChain).
2. **`category: memory` (Memoria Declarativa Soberana)**:
   - Utilízalas para guardar, recordar o consultar diagnósticos y hechos declarativos de la sesión.
3. **`category: domain` (Sistemas y Datos de Aplicación)**:
   - Utilízalas para consultar información directa de bases de datos o servicios de negocio.
4. **`category: system` (Runtime y Sistema Operativo)**:
   - Utilízalas para operaciones de archivos, terminal, web o gestión de habilidades locales.

REGLA DE DELEGACIÓN EXPLÍCITA DE FRAMEWORKS Y PIPELINES:
La infraestructura RayRabbit soporta la orquestación dinámica y paramétrica de múltiples frameworks y agentes cognitivos soberanos.
Si la consulta del usuario solicita un flujo multi-agente que interactúa con varios agentes o etapas, NO debes invocarlos todos a la vez. 
Analiza la secuencia requerida e invoca ÚNICAMENTE la herramienta de la primera etapa del flujo. El TaskEngine manejará la tarea en segundo plano. En la UI debes reflejar la fase en ejecución y colocar el botón de acción para la siguiente etapa pendiente. Solo cuando recibas la notificación de finalización o el usuario presione el botón de acción, se desencadenará la siguiente etapa de la cadena.
"""
        if hasattr(self, "system_prompt") and self.system_prompt:
            self.system_prompt = self.system_prompt + "\n" + taxonomy_guide
        self.cached_mcp_tools_map = {}
    
    def _load_context(self) -> Dict[str, Any]:
        path = self.brain_dir / "orchestration_context.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return {"events": []}
        return {"events": []}

    
    def load_dashboard(self, use_case: str) -> dict:
        import pathlib
        dashboard_path = pathlib.Path(__file__).parent.parent.parent / "examples" / "use_cases" / use_case / "dashboard.json"
        if dashboard_path.exists():
            import json
            with open(dashboard_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"components": []}

    def save_context(self):
        path = self.brain_dir / "orchestration_context.json"
        try:
            path.write_text(json.dumps(self.orchestration_context, indent=2), encoding="utf-8")
        except Exception:
            pass

    async def ingest_telemetry(self, sender_id: str, content: Dict[str, Any], correlation_id: str):
        """Punto de entrada directo para telemetría de alta velocidad."""
        async with self.telemetry_lock:
            context_event = {
                "timestamp": datetime.now().isoformat(),
                "sender": sender_id,
                "data": content
            }
            self.orchestration_context["events"].append(context_event)
            self.save_context()
            print(f"📊 [DIRECT TELEMETRY] Evento de {sender_id} (CID: {correlation_id}). Total en RAM: {len(self.orchestration_context['events'])}")
            
            if isinstance(content, dict):
                action = content.get("action")
                if action == "ui_update":
                    query = f"PROGRESO DEL SISTEMA: {content.get('title')}. {content.get('description')}. Actualiza la UI."
                    target_cid = "universal_dashboard" 
                    full_context_str = json.dumps(self.orchestration_context["events"][-5:], default=str)
                    await self.reason_ui_generation(query, full_context_str, correlation_id=target_cid, tools=None)
                elif action == "final_narrative":
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/narrative",
                            "value": content.get("text")
                        }
                    }, correlation_id="universal_dashboard")

    async def on_message(self, message: Message):
        """Capturar eventos del workflow y disparar generación UI Iterativa."""
        msg_type = message.message_type.value if hasattr(message.message_type, 'value') else str(message.message_type)
        print(f"📩 DEBUG: Capturando mensaje type='{msg_type}' desde '{message.sender_id}' (CID: {message.correlation_id})")
        sys.stdout.flush()
        
        cid = message.correlation_id
        
        if message.message_type == MessageType.EVENT:
            content = message.content
            if isinstance(content, dict):
                context_event = {
                    "timestamp": datetime.now().isoformat(),
                    "sender": message.sender_id,
                    "data": content
                }
                self.orchestration_context["events"].append(context_event)
                self.save_context()
                print(f"📊 DEBUG: Evento registrado en RAM. Total: {len(self.orchestration_context['events'])}")
                sys.stdout.flush()
                
                # --- DESPACHADOR REACTIVO ÁGIL A2UI v0.9.1 (Cero LLM en Progreso) ---
                try:
                    # Normalización: los eventos del TaskManager empaquetan status dentro de payload
                    _inner_payload = content.get("payload", {}) if isinstance(content.get("payload"), dict) else {}
                    _event_type = content.get("event_type", "")
                    
                    progress_val = content.get("progress") or _inner_payload.get("progress")
                    # status puede estar en la raíz O en content["payload"]["status"] (task events)
                    status_val = content.get("status") or _inner_payload.get("status")
                    # Si es un evento task.paused, forzar status "paused" aunque no venga en raíz
                    if not status_val and _event_type == "task.paused":
                        status_val = "paused"
                    elif not status_val and _event_type == "task.completed":
                        status_val = "completed"
                    elif not status_val and _event_type == "task.failed":
                        status_val = "failed"
                    elif not status_val and _event_type in ("task.progress", "task.created"):
                        status_val = _inner_payload.get("status") or "running"

                    step_val = content.get("step") or content.get("message") or content.get("title") or _inner_payload.get("step") or ""
                    
                    # Normalización canónica L3 con UniversalPayloadUnwrapper
                    unwrapped_res = UniversalPayloadUnwrapper.extract_result(content)
                    result_text = UniversalPayloadUnwrapper.extract_text(unwrapped_res)
                    # Excluir como "resultado real" los eventos de ciclo de vida de tareas
                    _is_task_lifecycle = bool(_event_type and _event_type.startswith("task."))
                    has_result = bool(
                        not _is_task_lifecycle and
                        result_text and result_text != "{}" and
                        not (isinstance(unwrapped_res, dict) and "task_id" in unwrapped_res and len(unwrapped_res) <= 3)
                    )
                    
                    # 1. Mutar modelo de datos en tiempo real si hay progreso
                    if progress_val is not None:
                        try:
                            p_int = int(float(progress_val))
                            await self.broadcast_a2ui({
                                "version": "v0.9.1",
                                "updateDataModel": {
                                    "surfaceId": "universal_dashboard",
                                    "path": "/task_progress",
                                    "value": p_int
                                }
                            }, correlation_id=cid)
                            await self.broadcast_a2ui({
                                "version": "v0.9.1",
                                "updateDataModel": {
                                    "surfaceId": "universal_dashboard",
                                    "path": "/progress",
                                    "value": p_int
                                }
                            }, correlation_id=cid)
                        except (ValueError, TypeError):
                            pass
                            
                    # 2. Mutar mensaje de estado / paso actual
                    if step_val:
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/task_status",
                                "value": str(step_val)
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/current_step",
                                "value": str(step_val)
                            }
                        }, correlation_id=cid)

                    # 3. Manejar finalización o estado activo
                    if status_val in ["completed", "done", "success"] or (progress_val is not None and int(float(progress_val)) >= 100):
                        self.current_running_task_id = None

                        # Extraer nombre de la herramienta/operación si viene en el evento
                        op_name = content.get("operation") or (_inner_payload.get("operation") if isinstance(_inner_payload, dict) else None)
                        if op_name:
                            executed_list = self.orchestration_context.setdefault("executed_tools", [])
                            if op_name not in executed_list and op_name not in ("read_session_memory", "save_memory_fact"):
                                executed_list.append(op_name)
                                self.save_context()

                        last_goal = getattr(self, "last_user_goal", "")
                        raw_tools = getattr(self, "cached_raw_tools", [])
                        if not raw_tools:
                            raw_tools = await self._fetch_all_hub_tools()
                        is_plan_completed = False
                        if last_goal and raw_tools:
                            from rayrabbit.utils.delegate_tool import ProgressiveStageDelegator
                            plan = ProgressiveStageDelegator(raw_tools).resolve_stage_plan(last_goal, self.orchestration_context.get("executed_tools", []))
                            is_plan_completed = plan.is_completed

                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/task_badge",
                                "value": "COMPLETADO"
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/task_progress",
                                "value": 100
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/working",
                                "value": False
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/buttons/step_action/disabled",
                                "value": is_plan_completed
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/buttons/step_action/label",
                                "value": "✅ Pipeline Finalizado" if is_plan_completed else "► Continuar a la Siguiente Fase"
                            }
                        }, correlation_id=cid)
                        if has_result and result_text and not result_text.startswith("{") and not result_text.startswith("[{"):
                            await self.broadcast_a2ui({
                                "version": "v0.9.1",
                                "updateDataModel": {
                                    "surfaceId": "universal_dashboard",
                                    "path": "/narrative",
                                    "value": result_text
                                }
                            }, correlation_id=cid)
                        else:
                            # Intentar extraer resultado desde el payload interno del task event
                            _inner_result = UniversalPayloadUnwrapper.extract_result(_inner_payload) if _inner_payload else None
                            _inner_text = UniversalPayloadUnwrapper.extract_text(_inner_result) if _inner_result else None
                            if _inner_text and _inner_text not in ("{}", "") and not _inner_text.startswith("{"):
                                await self.broadcast_a2ui({
                                    "version": "v0.9.1",
                                    "updateDataModel": {
                                        "surfaceId": "universal_dashboard",
                                        "path": "/narrative",
                                        "value": _inner_text
                                    }
                                }, correlation_id=cid)
                        print(f"✨ [A2UI REACTIVO] Tarea finalizada y botón reactivado en UI (<5ms) desde {message.sender_id}.")
                        sys.stdout.flush()
                    elif status_val in ["failed", "error"]:
                        self.current_running_task_id = None
                        err_msg = content.get("error") or _inner_payload.get("error", "Fallo en la ejecución de la tarea")
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/working",
                                "value": False
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/buttons/step_action/disabled",
                                "value": False
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/buttons/step_action/label",
                                "value": "🔄 Reintentar Etapa"
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/narrative",
                                "value": f"⚠️ Error en la etapa: {err_msg}"
                            }
                        }, correlation_id=cid)
                    elif status_val == "paused":
                        # hitl_request puede estar en raíz O en _inner_payload (task events del TaskManager)
                        hitl_req = (
                            content.get("hitl_request") or
                            _inner_payload.get("hitl_request") or
                            {}
                        )
                        q_text = hitl_req.get("question", "⚠️ Se requiere autorización para continuar.")
                        d_text = hitl_req.get("details", "")
                        combined_text = f"{q_text}\n\n{d_text}" if d_text else q_text
                        # Inyectar task_id en el data model para que el frontend pueda usar resume_task
                        _task_id = content.get("task_id", "")
                        if _task_id:
                            await self.broadcast_a2ui({
                                "version": "v0.9.1",
                                "updateDataModel": {
                                    "surfaceId": "universal_dashboard",
                                    "path": "/current_task_id",
                                    "value": _task_id
                                }
                            }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/working",
                                "value": False
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/buttons/step_action/disabled",
                                "value": True
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/buttons/step_action/label",
                                "value": "⚠️ Esperando Aprobación..."
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/narrative",
                                "value": combined_text
                            }
                        }, correlation_id=cid)
                        print(f"⚠️ [A2UI HITL] Tarea pausada esperando autorización humana desde {message.sender_id}.")
                        sys.stdout.flush()
                    elif status_val in ["running", "pending"]:
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/working",
                                "value": True
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/buttons/step_action/disabled",
                                "value": True
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/buttons/step_action/label",
                                "value": "⏳ Procesando en segundo plano..."
                            }
                        }, correlation_id=cid)
                        print(f"⚡ [A2UI REACTIVO] Progreso ({progress_val}%) y botón bloqueado en UI (<5ms) desde {message.sender_id}.")
                        sys.stdout.flush()
                except Exception as e:
                    logger.error(f"Error en despacho reactivo de evento A2UI: {e}", exc_info=True)

        if message.message_type == MessageType.COMMAND:
            content = message.content
            if isinstance(content, dict):
                action = content.get("action", "")
                context_event = {
                    "timestamp": datetime.now().isoformat(),
                    "sender": message.sender_id,
                    "action": action,
                    "data": content
                }
                self.orchestration_context["events"].append(context_event)
                self.save_context()
                print(f"📊 DEBUG: COMMAND '{action}' registrado en RAM de {message.sender_id}. Total: {len(self.orchestration_context['events'])}")
                sys.stdout.flush()
                
                try:
                    if action == "final_narrative":
                        final_text = content.get("text", "Proceso completado.")
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/narrative",
                                "value": final_text
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/working",
                                "value": False
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/task_progress",
                                "value": 100
                            }
                        }, correlation_id=cid)
                        print(f"✨ DEBUG: Narrativa final inyectada en UI desde {message.sender_id}.")
                        sys.stdout.flush()
                    elif action in ["order_analyzed", "route_optimized", "vehicle_assigned", "step_completed", "ui_update"]:
                        title = content.get("title", "Actualización")
                        description = content.get("description", "")
                        step_text = f"{title}: {description}" if description else title
                        
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/current_step",
                                "value": step_text
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/task_status",
                                "value": step_text
                            }
                        }, correlation_id=cid)
                        print(f"⚡ [A2UI REACTIVO] Paso '{action}' inyectado en UI (<5ms) desde {message.sender_id}.")
                        sys.stdout.flush()
                    elif action == "task_completed":
                        res_text = UniversalPayloadUnwrapper.extract_text(content) or "Tarea completada exitosamente."
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/narrative",
                                "value": str(res_text)
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/working",
                                "value": False
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": "universal_dashboard",
                                "path": "/task_progress",
                                "value": 100
                            }
                        }, correlation_id=cid)
                        print(f"✨ [A2UI REACTIVO] Fin de tarea completado en UI desde {message.sender_id}.")
                        sys.stdout.flush()
                except Exception as e:
                    logger.error(f"Error en despacho reactivo de COMMAND: {e}", exc_info=True)

        if message.message_type == MessageType.REQUEST:
            content = message.content
            if isinstance(content, dict) and "action" in content:
                await self.handle_a2ui_action(content["action"], message)

    async def handle_a2ui_action(self, action: Any, original_message: Message):
        action_dict = action if isinstance(action, dict) else {"name": action}
        action_name = action_dict.get("name") or action_dict.get("action")
        cid = original_message.correlation_id
        
        logger.info(f"Acción A2UI recibida en {AGENT_ID}: {action_name} (CID: {cid})")

        if action_name == "get_dashboard":
            # --- DASHBOARD INICIAL ---
            # Si no hay workspace seleccionado, mostrar saludo genérico.
            # El workspace específico solo se carga tras selección explícita del usuario.
            if not self.current_use_case:
                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "surfaceUpdate": {
                        "surfaceId": "universal_dashboard",
                        "components": [
                            {
                                "id": "root",
                                "component": {
                                    "Column": {
                                        "children": ["welcome-card"]
                                    }
                                }
                            },
                            {
                                "id": "welcome-card",
                                "component": {
                                    "Card": {
                                        "variant": "glass",
                                        "children": ["welcome-title", "welcome-description"]
                                    }
                                }
                            },
                            {
                                "id": "welcome-title",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Bienvenido a RayRabbit A2UI"
                                        },
                                        "variant": "h1"
                                    }
                                }
                            },
                            {
                                "id": "welcome-description",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Selecciona un espacio de trabajo en el selector superior para comenzar, o escribe tu consulta directamente en el chat."
                                        },
                                        "variant": "body"
                                    }
                                }
                            }
                        ]
                    }
                }, correlation_id=cid)
                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {"surfaceId": "universal_dashboard", "path": "/working", "value": False}
                }, correlation_id=cid)
                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "beginRendering": {"surfaceId": "universal_dashboard", "catalogId": "standard"}
                }, correlation_id=cid)
                return

            # Workspace ya seleccionado: renderizar dashboard específico
            dashboard_json = self.load_dashboard(self.current_use_case)
            components = dashboard_json.get("components", [])

            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "surfaceUpdate": {
                    "surfaceId": "universal_dashboard",
                    "components": components
                }
            }, correlation_id=cid)

            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/working",
                    "value": False
                }
            }, correlation_id=cid)

            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "beginRendering": {
                    "surfaceId": "universal_dashboard",
                    "catalogId": "standard"
                }
            }, correlation_id=cid)

            return

        if action_name == "select_workspace":
            workspace_id = action_dict.get("params", {}).get("workspace_id")
            if workspace_id:
                self.current_use_case = workspace_id
                logger.info(f"Workspace A2UI seleccionado: {workspace_id}")
                
                dashboard_json = self.load_dashboard(workspace_id)
                components = dashboard_json.get("components", [])

                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "surfaceUpdate": {
                        "surfaceId": "universal_dashboard",
                        "components": components
                    }
                }, correlation_id=cid)

                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": "universal_dashboard",
                        "path": "/working",
                        "value": False
                    }
                }, correlation_id=cid)

                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "beginRendering": {
                        "surfaceId": "universal_dashboard",
                        "catalogId": "standard"
                    }
                }, correlation_id=cid)
        
        if action_name == "userAction" or action_dict.get("type") == "userAction":
            action_id = action_dict.get("id") or action_dict.get("params", {}).get("action_id")
            print(f"🖱️ [USER INTERACTION] Pulsado {action_id} (CID: {cid})")
            
            if action_id == "switch_workspace_logistics":
                self.current_use_case = "logistics"
                await self.handle_a2ui_action("get_dashboard", original_message)
                return
            elif action_id == "switch_workspace_crypto":
                self.current_use_case = "crypto"
                await self.handle_a2ui_action("get_dashboard", original_message)
                return


            # Guard de Seguridad Backend contra Clics Prematuros
            # Si hay una tarea en curso en TaskEngine, suspender avance y notificar
            if getattr(self, "current_running_task_id", None):
                try:
                    async with httpx.AsyncClient(timeout=3.0) as client:
                        task_chk = await client.get(f"{HUB_URL}/api/tasks/{self.current_running_task_id}")
                        if task_chk.status_code == 200:
                            t_info = task_chk.json()
                            t_st = (t_info.get("task", {}) or {}).get("status") or t_info.get("status")
                            if t_st in ["running", "pending"]:
                                logger.warning(f"A2UI Guard: Tarea {self.current_running_task_id} aún en curso. Rechazando avance prematuro.")
                                await self.broadcast_a2ui({
                                    "version": "v0.9.1",
                                    "updateDataModel": {
                                        "surfaceId": "universal_dashboard",
                                        "path": "/narrative",
                                        "value": "⏳ La etapa anterior aún se encuentra en ejecución en segundo plano. Por favor, aguarda a que finalice."
                                    }
                                }, correlation_id=cid)
                                return
                except Exception as e:
                    logger.debug(f"A2UI Guard task check fallback: {e}")

            # Bloqueo inmediato reactivo del botón
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/buttons/step_action/disabled",
                    "value": True
                }
            }, correlation_id=cid)
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/buttons/step_action/label",
                    "value": "⏳ Procesando en segundo plano..."
                }
            }, correlation_id=cid)

            last_goal = getattr(self, "last_user_goal", "")
            executed_list = self.orchestration_context.get("executed_tools", [])
            raw_tools = getattr(self, "cached_raw_tools", [])
            if not raw_tools:
                raw_tools = await self._fetch_all_hub_tools()

            if last_goal:
                executed_str = ", ".join(executed_list) if executed_list else "ninguna"
                from rayrabbit.utils.delegate_tool import ProgressiveStageDelegator
                plan = ProgressiveStageDelegator(raw_tools).resolve_stage_plan(last_goal, executed_list)

                # Si el pipeline ya está 100% completado, cerrar formalmente
                if plan.is_completed:
                    self.logger.info(f"✅ Pipeline '{last_goal}' completado al 100%. Cerrando ciclo interactivo.")
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/buttons/step_action/label",
                            "value": "✅ Pipeline Finalizado"
                        }
                    }, correlation_id=cid)
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/buttons/step_action/disabled",
                            "value": True
                        }
                    }, correlation_id=cid)
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/task_progress",
                            "value": 100
                        }
                    }, correlation_id=cid)
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/working",
                            "value": False
                        }
                    }, correlation_id=cid)
                    return

                query = (
                    f"ACCIÓN DE USUARIO: El usuario interactuó con '{action_id}' para avanzar a la siguiente etapa de la meta: '{last_goal}'.\n"
                    f"Herramientas cognitivas ya completadas en etapas previas: [{executed_str}].\n"
                    f"Evalúa las herramientas disponibles para esta etapa activa y despacha la que corresponda según la meta del usuario."
                )
            else:
                query = f"ACCIÓN DE USUARIO: El usuario hizo clic en '{action_id}'. Procesa y actualiza la UI."

            context_str = json.dumps(self.orchestration_context["events"][-5:], default=str)
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": { "surfaceId": "universal_dashboard", "path": "/working", "value": True }
            }, correlation_id=cid)
            tools_scoped = await self.get_a2ui_tools(query=query)
            await self.reason_ui_generation(query, context_str, correlation_id=cid, tools=tools_scoped)

            # Post-ejecución: Evaluar si el plan se completó tras la ejecución del turno
            post_executed = self.orchestration_context.get("executed_tools", [])
            if last_goal and raw_tools:
                from rayrabbit.utils.delegate_tool import ProgressiveStageDelegator
                post_plan = ProgressiveStageDelegator(raw_tools).resolve_stage_plan(last_goal, post_executed)
                if post_plan.is_completed:
                    self.logger.info(f"✅ Pipeline '{last_goal}' completado tras razonamiento. Actualizando UI a estado final.")
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/buttons/step_action/label",
                            "value": "✅ Pipeline Finalizado"
                        }
                    }, correlation_id=cid)
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/buttons/step_action/disabled",
                            "value": True
                        }
                    }, correlation_id=cid)
            return

        if action_name == "human_query":
            try:
                self.current_correlation_id = cid

                # --- VERIFICACIÓN QUIRÚRGICA DE MODO DRY-RUN / TEST (Costo $0 en CI y pruebas de transporte) ---
                is_dry_run = bool(
                    action_dict.get("dry_run")
                    or action_dict.get("test")
                    or (isinstance(action_dict.get("params"), dict) and (action_dict["params"].get("dry_run") or action_dict["params"].get("test")))
                )
                if is_dry_run:
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/working",
                            "value": False
                        }
                    }, correlation_id=cid)
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/narrative",
                            "value": "✅ [DRY-RUN] Transporte A2UI y enrutamiento MessageBus validados correctamente."
                        }
                    }, correlation_id=cid)
                    return

                query = action_dict.get("params", {}).get("query_input", "").strip()
                if not query: return

                self.last_user_goal = query
                self.orchestration_context["executed_tools"] = []
                self.save_context()

                # Interceptar comando /learn de Auto Apredisaje Pattern
                if query.startswith("/learn"):
                    learn_topic = query[6:].strip() or "general-workflow"
                    authoring_prompt = (
                        f"INSTRUCCIÓN /learn (Estándar RayRabbit Agent):\n"
                        f"El usuario desea que aprendas e inmortalices la siguiente habilidad/flujo: '{learn_topic}'.\n\n"
                        f"REGLAS OBLIGATORIAS DE AUTORÍA (_AUTHORING_STANDARDS):\n"
                        f"1. Nombre: minúsculas con guiones (máximo 64 caracteres, ej. '{learn_topic.lower().replace(' ', '-')[:30]}').\n"
                        f"2. Descripción: EXACTAMENTE 1 oración concisa (MÁXIMO 60 CARACTERES).\n"
                        f"3. Invocación: Utiliza la herramienta `skill_manage` con action='create' para guardar la habilidad.\n"
                    )
                    query = authoring_prompt

                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": "universal_dashboard",
                        "path": "/working",
                        "value": True
                    }
                }, correlation_id=cid)

                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": "universal_dashboard",
                        "path": "/narrative",
                        "value": "Procesando solicitud y coordinando agentes soberanos en tiempo real..."
                    }
                }, correlation_id=cid)

                # Renderizado preliminar instantáneo (< 5ms) con arquitectura separada (Pipeline + TaskEngine)
                preliminary_components = [
                    {
                        "id": "root",
                        "component": {
                            "Column": {
                                "children": ["pipeline-card", "task-engine-card"]
                            }
                        }
                    },
                    {
                        "id": "pipeline-card",
                        "component": {
                            "Card": {
                                "variant": "glass",
                                "children": ["pipeline-header-row", "pipeline-desc"]
                            }
                        }
                    },
                    {
                        "id": "pipeline-header-row",
                        "component": {
                            "Row": {
                                "align": "center",
                                "justify": "spaceBetween",
                                "children": ["pipeline-title", "pipeline-badge"]
                            }
                        }
                    },
                    {
                        "id": "pipeline-title",
                        "component": {
                            "Text": {
                                "text": {"literalString": "⚡ Orquestación de Pipeline Agéntico"},
                                "variant": "h2"
                            }
                        }
                    },
                    {
                        "id": "pipeline-badge",
                        "component": {
                            "Text": {
                                "text": {"literalString": "MULTI-AGENT-SYSTEM"},
                                "variant": "badge"
                            }
                        }
                    },
                    {
                        "id": "pipeline-desc",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Coordinación soberana de agentes, herramientas MCP y memoria L3 en tiempo real."},
                                "variant": "body"
                            }
                        }
                    },
                    {
                        "id": "task-engine-card",
                        "component": {
                            "Card": {
                                "variant": "flat",
                                "children": ["task-engine-header-row", "task-progress-bar", "pipeline-status"]
                            }
                        }
                    },
                    {
                        "id": "task-engine-header-row",
                        "component": {
                            "Row": {
                                "align": "center",
                                "justify": "spaceBetween",
                                "children": ["task-engine-title", "task-engine-badge"]
                            }
                        }
                    },
                    {
                        "id": "task-engine-title",
                        "component": {
                            "Text": {
                                "text": {"literalString": "⚙️ TaskEngine — Gestor de ciclo de vida de tareas asíncronas"},
                                "variant": "caption"
                            }
                        }
                    },
                    {
                        "id": "task-engine-badge",
                        "component": {
                            "Text": {
                                "text": {"path": "/task_badge"},
                                "variant": "badge badge-running"
                            }
                        }
                    },
                    {
                        "id": "task-progress-bar",
                        "component": {
                            "ProgressBar": {
                                "progress": {"path": "/task_progress"}
                            }
                        }
                    },
                    {
                        "id": "pipeline-status",
                        "component": {
                            "Text": {
                                "text": {"path": "/task_status"},
                                "variant": "body"
                            }
                        }
                    }
                ]
                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "surfaceUpdate": {
                        "surfaceId": "universal_dashboard",
                        "components": preliminary_components
                    }
                }, correlation_id=cid)
                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": "universal_dashboard",
                        "path": "/task_badge",
                        "value": "EN PROCESO"
                    }
                }, correlation_id=cid)
                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": "universal_dashboard",
                        "path": "/task_progress",
                        "value": 15
                    }
                }, correlation_id=cid)
                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": "universal_dashboard",
                        "path": "/task_status",
                        "value": "Paso 1: Inicializando despacho con el clúster federado..."
                    }
                }, correlation_id=cid)

                context_str = json.dumps(self.orchestration_context["events"][-5:], default=str)
                print(f"🧠 DEBUG: Iniciando razonamiento LLM con {len(self.orchestration_context['events'])} eventos de contexto...")
                sys.stdout.flush()
                
                a2ui_payload = await self.reason_ui_generation(query, context_str, correlation_id=cid, tools=await self.get_a2ui_tools(query=query))
                print(f"✨ DEBUG: LLM respondió. Payload obtenido: {'SI' if a2ui_payload else 'NO'}")
                sys.stdout.flush()
                
                # Actualizar el lienzo izquierdo con los componentes del workspace activo de forma 100% agnóstica
                if self.current_use_case:
                    dashboard_json = self.load_dashboard(self.current_use_case)
                    components = dashboard_json.get("components", [])
                    if components:
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "surfaceUpdate": {
                                "surfaceId": "universal_dashboard",
                                "components": components
                            }
                        }, correlation_id=cid)
                        await self.broadcast_a2ui({
                            "version": "v0.9.1",
                            "beginRendering": {
                                "surfaceId": "universal_dashboard",
                                "catalogId": "standard"
                            }
                        }, correlation_id=cid)
                
                if not a2ui_payload:
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/narrative",
                            "value": "Lo siento, tuve un problema procesando tu solicitud. Por favor intenta de nuevo."
                        }
                    }, correlation_id=cid)

            except Exception as e:
                logger.error(f"Error en razonamiento dinámico A2UI: {e}", exc_info=True)
                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": "universal_dashboard",
                        "path": "/narrative",
                        "value": f"Error técnico en el Agente: {e}. Por favor, verifica el estado del cluster soberano."
                    }
                }, correlation_id=cid)

            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/working",
                    "value": False
                }
            }, correlation_id=cid)
            executed_list = self.orchestration_context.get("executed_tools", [])
            last_goal = getattr(self, "last_user_goal", "")
            is_pipeline_done = False
            raw_tools = getattr(self, "cached_raw_tools", [])
            if not raw_tools:
                raw_tools = await self._fetch_all_hub_tools()
            if last_goal and raw_tools:
                from rayrabbit.utils.delegate_tool import ProgressiveStageDelegator
                plan = ProgressiveStageDelegator(raw_tools).resolve_stage_plan(last_goal, executed_list)
                is_pipeline_done = plan.is_completed

            btn_label = "✅ Pipeline Finalizado" if is_pipeline_done else "► Continuar a la Siguiente Fase"
            btn_disabled = is_pipeline_done

            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/buttons/step_action/disabled",
                    "value": btn_disabled
                }
            }, correlation_id=cid)
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/buttons/step_action/label",
                    "value": btn_label
                }
            }, correlation_id=cid)
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/task_badge",
                    "value": "COMPLETADO"
                }
            }, correlation_id=cid)
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/task_progress",
                    "value": 100
                }
            }, correlation_id=cid)

    async def ensure_mcp_connected(self):
        if not getattr(mcp_client, "is_connected", False):
            try:
                await mcp_client.connect()
            except Exception as e:
                logger.warning(f"Intento de reconexión MCP client: {e}")

    async def _fetch_all_hub_tools(self) -> List[Dict[str, Any]]:
        """Obtiene y cachea el catálogo completo de herramientas vivas del Hub sin filtros."""
        if getattr(self, "cached_raw_tools", None):
            return self.cached_raw_tools
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{HUB_URL}/api/mcp/tools/search",
                    json={"query": "", "top_k": 30, "agent_role": "orchestrator"}
                )
                if res.status_code == 200:
                    self.cached_raw_tools = res.json().get("tools", [])
                    return self.cached_raw_tools
        except Exception as e:
            logger.debug(f"Error obteniendo catálogo crudo del Hub: {e}")
        return []

    async def get_a2ui_tools(self, query: str = "", correlation_id: Optional[str] = None):
        """Retorna herramientas dinámicas obtenidas del Hub MCP vía REST usando Progressive Stage Gating (Hermes Pattern) + BM25."""
        try:
            search_query = query or getattr(self, "last_user_goal", "")
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{HUB_URL}/api/mcp/tools/search",
                    json={"query": search_query, "top_k": 30, "agent_role": "orchestrator"}
                )
                if res.status_code == 200:
                    tools_list = res.json().get("tools", [])
                    self.cached_raw_tools = list(tools_list)

            executed_list = self.orchestration_context.get("executed_tools", [])
            last_goal = getattr(self, "last_user_goal", "") or query

            # Aplicar Progressive Stage Delegator si hay meta multi-etapa
            if last_goal and tools_list:
                from rayrabbit.utils.delegate_tool import ProgressiveStageDelegator
                delegator = ProgressiveStageDelegator(tools_list)
                tools_list = delegator.get_scoped_tools_for_active_stage(
                    user_goal=last_goal,
                    executed_tools=executed_list,
                    top_k=5
                )

            mcp_tools = []
            self.cached_mcp_tools_map = {}
            executed = set(executed_list)
            for tool in tools_list:
                name = tool.get("name")
                if name in ("send_message", "publish_message"):
                    continue
                agent_id = tool.get("agent_id") or "hub"
                desc = tool.get("description", "")
                schema = tool.get("input_schema", {})
                category = tool.get("category") or schema.get("category") or "general"
                
                # Descarte agnóstico de herramientas ya ejecutadas en la sesión
                if name in executed and name not in ("read_session_memory", "save_memory_fact"):
                    continue
                
                enhanced_desc = f"[{category}] {desc}" if not desc.startswith("[") else desc
                
                params_schema = schema
                if not isinstance(params_schema, dict) or "type" not in params_schema:
                    params_schema = {
                        "type": "object",
                        "properties": schema.get("properties", {}) if isinstance(schema, dict) else {},
                        "required": schema.get("required", []) if isinstance(schema, dict) else []
                    }
                
                tool_entry = {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": enhanced_desc,
                        "category": category,
                        "parameters": params_schema
                    },
                    "agent_id": agent_id,
                    "category": category
                }
                mcp_tools.append(tool_entry)
                self.cached_mcp_tools_map[name] = tool_entry

            self.cached_mcp_tools = mcp_tools
            return mcp_tools
        except Exception as e:
            logger.error(f"Error listando herramientas MCP del Hub: {e}")
            return []

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Ejecuta una herramienta a través del Hub MCP con resolución dinámica del agente destinatario real."""
        self.logger.info(f"A2UI: Invocando herramienta MCP externa '{name}' vía Hub...")
        
        # Garantizar que el catálogo esté poblado para resolver agent_id sin fallbacks a 'hub'
        if not getattr(self, "cached_mcp_tools_map", {}) or name not in getattr(self, "cached_mcp_tools_map", {}):
            await self.get_a2ui_tools()
        
        tool_entry = getattr(self, "cached_mcp_tools_map", {}).get(name, {})
        target_agent_id = tool_entry.get("agent_id") or "hub"
        
        if target_agent_id == "hub" and hasattr(self, "cached_mcp_tools") and isinstance(self.cached_mcp_tools, list):
            for t in self.cached_mcp_tools:
                fn = t.get("function", {})
                if fn.get("name") == name:
                    target_agent_id = t.get("agent_id") or fn.get("agent_id") or "hub"
                    break

        tool_category = tool_entry.get("category")
        if tool_category and tool_category != "general":
            self.current_use_case = tool_category

        args_copy = dict(args)
        cid = getattr(self, "current_correlation_id", None) or str(uuid.uuid4())
        if cid:
            args_copy["_correlation_id"] = cid
            
        payload = {
            "sender_id": self.id,
            "sender_name": self.name,
            "recipient_id": target_agent_id,
            "operation": name,
            "params": args_copy,
            "correlation_id": cid
        }
        headers = jws_manager.get_jws_headers(payload, correlation_id=cid)
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(f"{HUB_URL}/api/execute-tool", json=payload, headers=headers)
                if resp.status_code == 200:
                    res_data = resp.json()
                    
                    if res_data.get("status") in ("accepted", "task_created") and "task_id" in res_data:
                        task_id = res_data["task_id"]
                        self.current_running_task_id = task_id
                        # Esperar asíncronamente a que el TaskEngine complete la tarea en segundo plano
                        max_wait_secs = 300
                        start_time = time.time()
                        while time.time() - start_time < max_wait_secs:
                            await asyncio.sleep(1.0)
                            try:
                                status_resp = await client.get(f"{HUB_URL}/api/tasks/{task_id}")
                                if status_resp.status_code == 200:
                                    task_state = status_resp.json()
                                    st = (task_state.get("task", {}) or {}).get("status") or task_state.get("status")
                                    if st == "completed":
                                        events = task_state.get("events", [])
                                        completed_event = next((e for e in reversed(events) if e.get("event_type") == "task.completed"), None) or (events[-1] if events else {})
                                        payload = completed_event.get("payload", {}) if isinstance(completed_event, dict) else {}
                                        response = UniversalPayloadUnwrapper.extract_result(payload.get("result", payload)) or UniversalPayloadUnwrapper.extract_result(task_state)
                                        # Registro dinámico al completarse exitosamente la tarea asíncrona
                                        executed_list = self.orchestration_context.setdefault("executed_tools", [])
                                        if name not in executed_list and name not in ("read_session_memory", "save_memory_fact"):
                                            executed_list.append(name)
                                            self.save_context()
                                            self.logger.info(f"✅ Tarea '{name}' completada en TaskEngine y registrada: {executed_list}")
                                        break
                                    elif st == "paused":
                                        # Mientras esté en pausa esperando HITL humano, renovar la ventana de espera
                                        start_time = time.time()
                                    elif st == "failed":
                                        events = task_state.get("events", [])
                                        failed_event = next((e for e in reversed(events) if e.get("event_type") == "task.failed"), None) or (events[-1] if events else {})
                                        err_res = failed_event.get("payload", {}).get("error", "Tarea fallida en TaskEngine") if isinstance(failed_event, dict) else "Tarea fallida en TaskEngine"
                                        response = {"error": err_res}
                                        # Fault tolerance: reactivar botón para reintento
                                        await self.broadcast_a2ui({
                                            "version": "v0.9.1",
                                            "updateDataModel": {
                                                "surfaceId": "universal_dashboard",
                                                "path": "/buttons/step_action/disabled",
                                                "value": False
                                            }
                                        }, correlation_id=cid)
                                        await self.broadcast_a2ui({
                                            "version": "v0.9.1",
                                            "updateDataModel": {
                                                "surfaceId": "universal_dashboard",
                                                "path": "/buttons/step_action/label",
                                                "value": "🔄 Reintentar Etapa"
                                            }
                                        }, correlation_id=cid)
                                        break
                            except Exception as poll_err:
                                self.logger.warning(f"Error consultando TaskEngine para task {task_id}: {poll_err}")
                        else:
                            response = UniversalPayloadUnwrapper.extract_result(res_data)
                        self.current_running_task_id = None
                    else:
                        # Registro para herramientas síncronas directas
                        executed_list = self.orchestration_context.setdefault("executed_tools", [])
                        if name not in executed_list and name not in ("read_session_memory", "save_memory_fact"):
                            executed_list.append(name)
                            self.save_context()
                            self.logger.info(f"✅ Herramienta síncrona '{name}' completada y registrada: {executed_list}")
                        response = UniversalPayloadUnwrapper.extract_result(res_data)
                        self.current_running_task_id = None
                else:
                    response = {"error": f"HTTP {resp.status_code}: {resp.text}"}
                    # Fault tolerance: reactivar botón para reintento
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/buttons/step_action/disabled",
                            "value": False
                        }
                    }, correlation_id=cid)
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "universal_dashboard",
                            "path": "/buttons/step_action/label",
                            "value": "🔄 Reintentar Etapa"
                        }
                    }, correlation_id=cid)
        except Exception as tool_err:
            self.logger.error(f"Error ejecutando herramienta {name}: {tool_err}")
            response = {"error": str(tool_err)}
            # Fault tolerance: reactivar botón para reintento
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/buttons/step_action/disabled",
                    "value": False
                }
            }, correlation_id=cid)
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "universal_dashboard",
                    "path": "/buttons/step_action/label",
                    "value": "🔄 Reintentar Etapa"
                }
            }, correlation_id=cid)

        await self.broadcast_a2ui({
            "version": "v0.9.1",
            "updateDataModel": {
                "surfaceId": "universal_dashboard",
                "path": f"/{name}_response",
                "value": response
            }
        }, correlation_id=getattr(self, "current_correlation_id", "default_dashboard"))
        return response

# Instancia global del agente
agent = UniversalA2UIAgent(AGENT_ID, AGENT_NAME)

@app.on_event("startup")
async def startup_event():
    """Realiza el Handshake formal con el Hub nada más iniciar."""
    logger.info(f"🚀 Iniciando {AGENT_NAME} en puerto {PORT}...")
    
    current_time = str(int(time.time()))
    challenge = f"REG-AUTH:{AGENT_ID}:{current_time}"
    signature = base64.b64encode(jws_manager.private_key.sign(
        challenge.encode('utf-8'),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )).decode('utf-8')

    handshake_payload = {
        "agent_id": AGENT_ID,
        "public_key_pem": jws_manager.public_key_pem,
        "timestamp": current_time,
        "signature": signature,
        "p2p_endpoint": ENDPOINT,
        "capabilities": ["a2ui_generation", "opal_design"]
    }
    
    max_retries = 10
    initial_delay = 0.1
    await asyncio.sleep(initial_delay)
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = jws_manager.get_jws_headers(handshake_payload)
                response = await client.post(
                    f"{HUB_URL}/api/security/register",
                    json=handshake_payload,
                    headers=headers
                )
                if response.status_code == 200:
                    logger.info(f"✅ Handshake OK con el Hub ({HUB_URL})")
                    return
                else:
                    logger.error(f"❌ Fallo en Handshake (Intento {attempt+1}/{max_retries}): {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"❌ Error conectando con el Hub para Handshake (Intento {attempt+1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            wait_time = 2 + attempt
            await asyncio.sleep(wait_time)
            
    logger.warning("⚠️ Hub no disponible tras reintentos prolongados. Operando en modo aislado.")

@app.post("/telemetry")
async def receive_telemetry(request: Request):
    """Endpoint de telemetría de alta velocidad (bypass de Hub)."""
    try:
        data = await request.json()
        sender_id = data.get("sender_id", "unknown")
        correlation_id = data.get("correlation_id", "unknown")
        content = data.get("content", {})
        asyncio.create_task(agent.ingest_telemetry(sender_id, content, correlation_id))
        return {"status": "accepted"}
    except Exception as e:
        print(f"❌ [TELEMETRY ERROR] {e}")
        logger.error(f"Error en ingestión de telemetría: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/a2ui")
async def a2ui_handler(request: Request):
    """Endpoint oficial para recibir mensajes A2A (JSON-RPC) del Hub y derivarlos al agente."""
    try:
        body = await request.json()
        print(f"DEBUG: /a2ui recibido cuerpo JSON-RPC")
        sys.stdout.flush()
        
        params = body.get("params", {})
        if not params and "action" in body: 
            params = body
            
        correlation_id = str(body.get("id") or params.get("correlation_id") or uuid.uuid4())
        
        msg = Message(
            sender_id=params.get("sender_id", "hub"),
            sender_name=params.get("sender_name", "Hub"),
            recipient_id=params.get("agent_id", AGENT_ID),
            message_type=MessageType(params.get("message_type", "request").lower()),
            content=params if "action" in params else params.get("content", params),
            correlation_id=correlation_id
        )
        
        asyncio.create_task(agent.on_message(msg))
        return {"jsonrpc": "2.0", "result": "accepted", "id": correlation_id}
    except Exception as e:
        logger.error(f"FATAL A2UI: Error en handler: {e}")
        print(f"FATAL ERROR A2UI: {e}")
        sys.stdout.flush()
        return {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "A2UI Sovereign Service"}

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Deteniendo cliente MCP...")
    try:
        await mcp_client.disconnect()
    except Exception as e:
        logger.error(f"Error desconectando cliente MCP: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
