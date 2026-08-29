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
Caso de Uso Logístico: Generative A2UI Sovereign Service
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
from rayrabbit.security.sovereign_identity import SovereignIdentity

# --- Configuración del Servicio ---
AGENT_ID = "logistics_ui_manager"
AGENT_NAME = "RayRabbit A2UI Assistant"
PORT = 8006
ENDPOINT = f"http://127.0.0.1:{PORT}/a2ui"
HUB_URL = os.environ.get("RAYRABBIT_HUB_URL", "http://127.0.0.1:8005")

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
class LogisticsSovereignAgent(SovereignA2UIAgent):
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name)
        
        # Patrón de Memoria L2
        self.brain_dir = Path(".rayrabbit_data/brain") / self.id
        self.brain_dir.mkdir(parents=True, exist_ok=True)
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
    
    def _load_context(self) -> Dict[str, Any]:
        path = self.brain_dir / "orchestration_context.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return {"events": []}
        return {"events": []}

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
                    target_cid = "logistics_dashboard" 
                    full_context_str = json.dumps(self.orchestration_context["events"][-5:], default=str)
                    await self.reason_ui_generation(query, full_context_str, correlation_id=target_cid, tools=None)
                elif action == "final_narrative":
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "logistics_dashboard",
                            "path": "/narrative",
                            "value": content.get("text")
                        }
                    }, correlation_id="logistics_dashboard")

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
                
                try:
                    query = f"NUEVO EVENTO DEL SISTEMA Recibido de {message.sender_id}. Modifica la UI si es necesario para reflejar este nuevo estado vivo."
                    diff_context_str = json.dumps([context_event], default=str)
                    print(f"🧠 DEBUG: Gatillando UI Dinámica con {self.model} para {message.sender_id}...")
                    sys.stdout.flush()
                    # Desactivar tools para eventos en segundo plano para evitar bucles de inferencia lentos
                    a2ui_payload = await self.reason_ui_generation(query, diff_context_str, correlation_id=cid, tools=None)
                    if a2ui_payload:
                        print(f"✨ DEBUG: UI actualizada iterativamente tras evento de {message.sender_id}.")
                        sys.stdout.flush()
                except Exception as e:
                    logger.error(f"Error en iteración dinámica UI por evento: {e}", exc_info=True)

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
                                "surfaceId": "logistics_dashboard",
                                "path": "/narrative",
                                "value": final_text
                            }
                        }, correlation_id=cid)
                        print(f"✨ DEBUG: Narrativa final inyectada en UI desde {message.sender_id}.")
                        sys.stdout.flush()
                    elif action == "ui_update":
                        title = content.get("title", "Actualización")
                        description = content.get("description", "")
                        query = f"PROGRESO DEL SISTEMA: {title}. {description}. Actualiza la UI para reflejar este avance."
                        diff_context_str = json.dumps([context_event], default=str)
                        print(f"🧠 DEBUG: Gatillando UI Dinámica con {self.model} por COMMAND de {message.sender_id}...")
                        sys.stdout.flush()
                        a2ui_payload = await self.reason_ui_generation(query, diff_context_str, correlation_id=cid, tools=None)
                        if a2ui_payload:
                            print(f"✨ DEBUG: UI actualizada iterativamente tras COMMAND de {message.sender_id}.")
                            sys.stdout.flush()
                except Exception as e:
                    logger.error(f"Error en iteración dinámica UI por COMMAND: {e}", exc_info=True)

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
            # --- DASHBOARD ESTÁTICO PRE-CONSTRUIDO (Renderizado Instantáneo) ---
            # Elimina la llamada LLM (~97s) enviando un layout premium pre-definido.
            # El LLM solo se invoca para consultas del usuario (human_query).
            
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "surfaceUpdate": {
                    "surfaceId": "logistics_dashboard",
                    "components": [
                        {
                            "id": "root",
                            "component": { "Column": { "children": ["header-row", "status-card", "services-card", "actions-card", "footer-text"] } }
                        },
                        {
                            "id": "header-row",
                            "component": { "Column": { "children": ["title", "subtitle"] } }
                        },
                        {
                            "id": "title",
                            "component": { "Text": { "text": { "literalString": "🚀 Dashboard Logístico — Monitoreo Activo" }, "variant": "h1" } }
                        },
                        {
                            "id": "subtitle",
                            "component": { "Text": { "text": { "literalString": "Sistema de monitoreo en tiempo real de la cadena logística con análisis de datos reales del sistema. La interfaz proporciona una visión integral del estado operativo de todos los servicios críticos." }, "variant": "body" } }
                        },
                        {
                            "id": "status-card",
                            "component": { "Card": { "children": ["status-title", "status-body", "status-nodes"] } }
                        },
                        {
                            "id": "status-title",
                            "component": { "Text": { "text": { "literalString": "📡 Infraestructura de Red A2A & MCP" }, "variant": "h3" } }
                        },
                        {
                            "id": "status-body",
                            "component": { "Text": { "text": { "literalString": "Todos los servicios críticos están federados y comunicándose a través del MessageBus soberano de RayRabbit:" }, "variant": "body" } }
                        },
                        {
                            "id": "status-nodes",
                            "component": { "Row": { "children": ["node-lc", "node-cr", "node-ag"] } }
                        },
                        {
                            "id": "node-lc",
                            "component": { "Text": { "text": { "literalString": "🟢 Global Logistics Manager (8002)" }, "variant": "caption" } }
                        },
                        {
                            "id": "node-cr",
                            "component": { "Text": { "text": { "literalString": "🟢 DeepRoute Optimizer (8001)" }, "variant": "caption" } }
                        },
                        {
                            "id": "node-ag",
                            "component": { "Text": { "text": { "literalString": "🟢 Autonomous Fleet Commander (8003)" }, "variant": "caption" } }
                        },
                        {
                            "id": "services-card",
                            "component": { "Card": { "children": ["services-title", "services-body"] } }
                        },
                        {
                            "id": "services-title",
                            "component": { "Text": { "text": { "literalString": "🚚 Flujos de Coordinación y Telemetría" }, "variant": "h3" } }
                        },
                        {
                            "id": "services-body",
                            "component": { "Text": { "text": { "literalString": "Monitoree la optimización dinámica de rutas y despacho de vehículos. Envíe consultas directamente desde la barra de chat, por ejemplo: \"¿Cuál es el estado del paquete PKG-1234?\"" }, "variant": "body" } }
                        },
                        {
                            "id": "actions-card",
                            "component": { "Card": { "children": ["actions-title", "actions-row"] } }
                        },
                        {
                            "id": "actions-title",
                            "component": { "Text": { "text": { "literalString": "⚡ Acciones Rápidas de Monitoreo" }, "variant": "h3" } }
                        },
                        {
                            "id": "actions-row",
                            "component": { "Row": { "children": ["btn-tracking", "btn-fleet", "btn-routes"] } }
                        },
                        {
                            "id": "btn-tracking",
                            "component": { "Button": { "text": { "literalString": "📦 Consultar Tracking" }, "variant": "primary", "action": { "type": "userAction", "id": "quick-tracking" } } }
                        },
                        {
                            "id": "btn-fleet",
                            "component": { "Button": { "text": { "literalString": "🚛 Estado de Flota" }, "variant": "secondary", "action": { "type": "userAction", "id": "quick-fleet" } } }
                        },
                        {
                            "id": "btn-routes",
                            "component": { "Button": { "text": { "literalString": "🗺️ Optimizar Ruta" }, "variant": "secondary", "action": { "type": "userAction", "id": "quick-routes" } } }
                        },
                        {
                            "id": "footer-text",
                            "component": { "Text": { "text": { "literalString": "Conectado al Hub Soberano — Puerto 8005 | A2UI v0.9.1 | Cifrado E2E Activo" }, "variant": "caption" } }
                        }
                    ]
                }
            }, correlation_id=cid)

            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "logistics_dashboard",
                    "path": "/working",
                    "value": False
                }
            }, correlation_id=cid)

            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "beginRendering": {
                    "surfaceId": "logistics_dashboard",
                    "catalogId": "logistics_premium"
                }
            }, correlation_id=cid)

            return

        if action_name == "userAction" or action_dict.get("type") == "userAction":
            action_id = action_dict.get("id") or action_dict.get("params", {}).get("action_id")
            print(f"🖱️ [USER INTERACTION] Pulsado {action_id} (CID: {cid})")
            query = f"ACCIÓN DE USUARIO: El usuario hizo clic en el componente '{action_id}'. Responde y actualiza la UI en consecuencia."
            context_str = json.dumps(self.orchestration_context["events"][-5:], default=str)
            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": { "surfaceId": "logistics_dashboard", "path": "/working", "value": True }
            }, correlation_id=cid)
            await self.reason_ui_generation(query, context_str, correlation_id=cid, tools=self.get_a2ui_tools())
            return

        if action_name == "human_query":
            try:
                query = action_dict.get("params", {}).get("query_input", "")
                if not query: return

                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": "logistics_dashboard",
                        "path": "/working",
                        "value": True
                    }
                }, correlation_id=cid)

                context_str = json.dumps(self.orchestration_context["events"][-5:], default=str)
                print(f"🧠 DEBUG: Iniciando razonamiento LLM con {len(self.orchestration_context['events'])} eventos de contexto...")
                sys.stdout.flush()
                
                a2ui_payload = await self.reason_ui_generation(query, context_str, correlation_id=cid, tools=self.get_a2ui_tools())
                print(f"✨ DEBUG: LLM respondió. Payload obtenido: {'SI' if a2ui_payload else 'NO'}")
                sys.stdout.flush()
                
                if not a2ui_payload:
                    await self.broadcast_a2ui({
                        "version": "v0.9.1",
                        "updateDataModel": {
                            "surfaceId": "logistics_dashboard",
                            "path": "/narrative",
                            "value": "Lo siento, tuve un problema procesando tu solicitud. Por favor intenta de nuevo."
                        }
                    }, correlation_id=cid)

            except Exception as e:
                logger.error(f"Error en razonamiento dinámico A2UI: {e}", exc_info=True)
                await self.broadcast_a2ui({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": "logistics_dashboard",
                        "path": "/narrative",
                        "value": f"Error técnico en el Agente: {e}. Por favor, verifica el estado del cluster soberano."
                    }
                }, correlation_id=cid)

            await self.broadcast_a2ui({
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "logistics_dashboard",
                    "path": "/working",
                    "value": False
                }
            }, correlation_id=cid)

    def get_a2ui_tools(self, correlation_id: Optional[str] = None):
        """Retorna las herramientas nativas distribuidas resolviendo URLs dinámicamente."""
        
        def get_service_url(service_name: str, default: str) -> str:
            services = self.config_mgr.data.custom.get("external_services", [])
            for s in services:
                if s.get("name") == service_name:
                    return s.get("address", default)
            return default

        url_langchain = get_service_url("langchain_service", "http://127.0.0.1:8002")
        url_crewai = get_service_url("crewai_service", "http://127.0.0.1:8001")
        url_autogen = get_service_url("autogen_service", "http://127.0.0.1:8003")

        async def get_order_tracking(order_id: str) -> str:
            """Tool MCP Distribuido: Consulta el nodo logístico maestro buscando información estructurada del pedido."""
            try:
                payload = {"name": "analyze_order", "arguments": {"order_id": order_id}}
                async with httpx.AsyncClient() as client:
                    headers = jws_manager.get_jws_headers(payload, correlation_id=correlation_id)
                    resp = await client.post(f"{url_langchain}/mcp/call", json=payload, headers=headers)
                    if resp.status_code == 200:
                        return str(resp.json().get("content", [{"text": "Not found"}])[0].get("text"))
                    return "Order details unavailable."
            except Exception as e:
                return f"MCP Network Error ({url_langchain}): {e}"

        async def get_routing_plan(package_id: str) -> str:
            """Tool MCP Distribuido: Consulta el nodo de optimización (CrewAI) buscando el plan de ruteo vigente."""
            try:
                payload = {"name": "get_routing_plan", "arguments": {"package_id": package_id}}
                async with httpx.AsyncClient() as client:
                    headers = jws_manager.get_jws_headers(payload, correlation_id=correlation_id)
                    resp = await client.post(f"{url_crewai}/mcp/call", json=payload, headers=headers)
                    if resp.status_code == 200:
                        return str(resp.json().get("content", [{"text": "Routing plan not found"}])[0].get("text"))
                    return "Routing plan unavailable."
            except Exception as e:
                return f"MCP Network Error ({url_crewai}): {e}"

        async def get_fleet_assignments(package_id: Optional[str] = None) -> str:
            """Tool MCP Distribuido: Consulta el nodo de flota (AutoGen) buscando asignaciones vigentes para un paquete."""
            try:
                args = {"package_id": package_id} if package_id else {}
                payload = {"name": "get_fleet_assignment", "arguments": args}
                async with httpx.AsyncClient() as client:
                    headers = jws_manager.get_jws_headers(payload, correlation_id=correlation_id)
                    resp = await client.post(f"{url_autogen}/mcp/call", json=payload, headers=headers)
                    if resp.status_code == 200:
                        return str(resp.json().get("content", [{"text": "Fleet assignment not found"}])[0].get("text"))
                    return "Fleet assignment unavailable."
            except Exception as e:
                return f"MCP Network Error ({url_autogen}): {e}"

        async def search_fleet_availability(cargo_type: str, weight: int) -> str:
            """Tool de Acción: Dispara un flujo en AutoGen para BUSCAR recursos reales en SAP TM."""
            try:
                prompt = f"Busca disponibilidad en SAP TM para carga {cargo_type} con peso {weight}kg."
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tasks/create",
                    "params": {"prompt": prompt},
                    "id": correlation_id or str(uuid.uuid4())
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    headers = jws_manager.get_jws_headers(payload, correlation_id=correlation_id)
                    resp = await client.post(f"{url_autogen}/a2a", json=payload, headers=headers)
                    if resp.status_code == 200:
                        return resp.json().get("result", {}).get("output", "Búsqueda completada exitosamente.")
                    return f"Error en búsqueda de flota ({url_autogen}): {resp.status_code}"
            except Exception as e:
                return f"Fleet Search Exception: {e}"

        async def assign_fleet_driver(vehicle_id: str, driver_name: str) -> str:
            """Tool de Acción: Dispara un flujo en AutoGen para ASIGNAR un conductor a un vehículo."""
            try:
                prompt = f"Asigna al conductor {driver_name} al vehículo {vehicle_id} en SAP TM."
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tasks/create",
                    "params": {"prompt": prompt},
                    "id": correlation_id or str(uuid.uuid4())
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    headers = jws_manager.get_jws_headers(payload, correlation_id=correlation_id)
                    resp = await client.post(f"{url_autogen}/a2a", json=payload, headers=headers)
                    if resp.status_code == 200:
                        return resp.json().get("result", {}).get("output", "Asignación completada.")
                    return f"Error en asignación de conductor ({url_autogen}): {resp.status_code}"
            except Exception as e:
                return f"Fleet Assignment Exception: {e}"

        async def check_inventory_stock(product_name: str) -> str:
            """Tool de Consulta: Busca stock real del producto en el nodo LangChain (WMS)."""
            try:
                payload = {"name": "get_product_info", "arguments": {"name": product_name}}
                async with httpx.AsyncClient() as client:
                    headers = jws_manager.get_jws_headers(payload, correlation_id=correlation_id)
                    resp = await client.post(f"{url_langchain}/mcp/call", json=payload, headers=headers)
                    if resp.status_code == 200:
                        return str(resp.json().get("content", [{"text": "Not found"}])[0].get("text"))
                    return f"Inventory info unavailable ({url_langchain}): {resp.status_code}"
            except Exception as e:
                return f"Inventory Check Exception: {e}"

        async def run_routing_optimization(package_id: str, prompt: str = "Optimizar ruta de entrega") -> str:
            """Tool MCP Distribuido: DISPARA una ejecución real de CrewAI para optimizar una ruta."""
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tasks/create",
                    "params": {"prompt": prompt, "package_id": package_id},
                    "id": correlation_id or str(uuid.uuid4())
                }
                async with httpx.AsyncClient(timeout=60.0) as client:
                    headers = jws_manager.get_jws_headers(payload, correlation_id=correlation_id)
                    resp = await client.post(f"{url_crewai}/a2a", json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        result = data.get("result", {})
                        output = result.get("output") or result.get("detail", {}).get("final_summary")
                        return f"SUCCESS: Optimization triggered. CrewAI Output: {output}"
                    return f"Error triggering optimization: {resp.status_code}"
            except Exception as e:
                return f"Optimization Trigger Exception: {e}"

        return [
            get_order_tracking,
            get_routing_plan,
            get_fleet_assignments,
            search_fleet_availability,
            assign_fleet_driver,
            check_inventory_stock,
            run_routing_optimization
        ]

# Instancia global del agente
agent = LogisticsSovereignAgent(AGENT_ID, AGENT_NAME)

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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
