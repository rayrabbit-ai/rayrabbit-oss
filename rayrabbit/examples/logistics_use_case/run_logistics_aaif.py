"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import asyncio
import os
import sys

# Forzar UTF-8 en Windows para que soporte emojis
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import logging
import uuid
import json
import time
import httpx
from datetime import datetime
from typing import Dict, Any, List

from rayrabbit.utils.logger import get_logger, configure_logging

# --- Visuals ---
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
    H_COLOR = Fore.CYAN + Style.BRIGHT
    STEP_COLOR = Fore.BLUE + Style.BRIGHT
    OK_COLOR = Fore.GREEN
    WARN_COLOR = Fore.YELLOW
    ROUTING_COLOR = Fore.MAGENTA
    META_COLOR = Fore.LIGHTBLACK_EX
    RESET = Style.RESET_ALL
except ImportError:
    # Fallback sin colores
    H_COLOR = STEP_COLOR = OK_COLOR = WARN_COLOR = ROUTING_COLOR = META_COLOR = RESET = ""

logger = get_logger("AAIF_E2E")

from rayrabbit.core.runtime_context import RuntimeContext

from rayrabbit.core.message_bus import MessageBus
from rayrabbit.core.discovery import DiscoveryService
from rayrabbit.protocols.a2a_router import A2ARouter
from rayrabbit.communication.message import Message, MessageType
from rayrabbit.utils.config import MessageBusConfig, SecurityConfig
from rayrabbit.security.maestro import MAESTROSecurity
from rayrabbit.security.auditing import AuditManager
from rayrabbit.security.sqlite_audit_provider import SQLiteAuditProvider
from rayrabbit.utils.dashboard import DashboardService


async def run_federated_logistics_aaif():
    # Intentar cargar .env local
    from pathlib import Path
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    name, value = line.strip().split("=", 1)
                    os.environ[name] = value.strip('"').strip("'")
        logger.info(f"Cargadas variables de entorno desde {env_path}")

    print("\n" + H_COLOR + "="*80)
    print(f"{H_COLOR} RAYRABBIT FEDERATED LOGISTICS: REAL E2E (V2.1) ".center(88, "="))
    print(H_COLOR + "="*80 + RESET + "\n")
    
    try:
        # 1. Setup Infrastructure and Config
        from rayrabbit.utils.config import get_config_manager
        config_mgr = get_config_manager()
        config_mgr.load_from_file("config.yaml")
        
        # 2. Setup Infrastructure (Logical Hub & Discovery)
        print(f"{STEP_COLOR}[STEP 1] Inicializando Infraestructura RayRabbit (Remote-First)...{RESET}")

        audit_manager = AuditManager()
        
        cfg_sec = config_mgr.data.security
        MASTER_SECRET = cfg_sec.master_secret or os.getenv("RAYRABBIT_MASTER_SECRET") or "emergency_secret_change_me_immediately"
        SALT = cfg_sec.salt or os.getenv("RAYRABBIT_SECURITY_SALT") or "emergency_salt_change_me"

        print(f"{META_COLOR}  -> Master Secret Used: {MASTER_SECRET[:5]}...{RESET}")
        print(f"{META_COLOR}  -> Salt Used: {SALT[:5]}...{RESET}")

        # Usar rutas absolutas para el keystore
        abs_keystore_path = RuntimeContext.get_keystore_dir()
        sec_config = SecurityConfig(
            keystore_path=abs_keystore_path,
            master_secret=MASTER_SECRET,
            salt=SALT
        )
        security = MAESTROSecurity("rayrabbit_framework_core", config=sec_config, audit_manager=audit_manager)
        
        # Producir certificados si no existen
        security._ensure_identity_key()
        
        # Inyectar proveedor de almacenamiento para evitar AttributeError
        provider = SQLiteAuditProvider(db_path="audit_logs/audit.db", maestro=security)
        audit_manager.set_storage_provider(provider)
        
        bus = MessageBus(config=MessageBusConfig(), security_module=security)
        router = bus.a2a_protocol.router 
        discovery = DiscoveryService(a2a_router=router, search_paths=["."], audit_manager=audit_manager)
        dashboard = DashboardService(bus=bus, router=router, audit_manager=audit_manager)
        
        await audit_manager.start()
        await bus.start()
        
        # 3. Discovery Real y Registro de Identidades en el Bus
        print(f"\n{STEP_COLOR}[STEP 2] Discovery: Sincronizando Ecosistema...{RESET}")
        await discovery.scan_now()
        
        from rayrabbit.core.agent import Agent
        for agent_id, profile in router.registry.items():
            if agent_id not in bus.agents:
                proxy_agent = Agent(agent_id=agent_id, name=profile.name or agent_id)
                bus.agents[agent_id] = proxy_agent
                bus.subscribe(agent_id, agent_id)
                print(f"{ROUTING_COLOR}   [A2A] Discovery: Agente federado sincronizado -> {Style.BRIGHT}'{agent_id}'{RESET}")
        
        # Telemetry Bridge para A2UI
        print(f"   {STEP_COLOR}[EXTRA] Iniciando Telemetry Bridge hacia el Hub...{RESET}")
        class TelemetryBridgeAgent(Agent):
            def __init__(self, agent_id: str, name: str, security_manager):
                super().__init__(agent_id, name)
                self.security_manager = security_manager

            async def on_message(self, message: Message):
                if message.sender_id != "telemetry_bridge" and message.sender_id != "hub" and message.sender_id != "ui_client":
                    try:
                        hub_url = os.getenv("RAYRABBIT_API_URL", "http://127.0.0.1:8005")
                        publish_url = f"{hub_url}/api/publish-message"
                        headers = self.security_manager.get_jws_headers(message.to_dict()) if self.security_manager else {}
                        async with httpx.AsyncClient() as client:
                            await client.post(publish_url, json=message.to_dict(), headers=headers, timeout=2.0)
                    except Exception as e:
                        print(f"   [TelemetryBridge] Error enviando a Hub: {e}")

        telemetry_bridge = TelemetryBridgeAgent("telemetry_bridge", "Dashboard Relay", security if 'security' in locals() else None)
        await bus.register_agent(telemetry_bridge)
        bus.subscribe("*", telemetry_bridge.id)

        print(f"   {OK_COLOR}✅ INFO: Logistics UI Manager operando nativamente en el Hub.{RESET}")
        
        # 4. Routing P2P Real (HTTP) - CASCADA MULTI-AGENTE (A2A + MCP)
        print(f"\n{STEP_COLOR}[STEP 3] Ejecutando CASCADA AAIF (Producción: A2A + MCP)...{RESET}")
        
        # Parsear comando del usuario
        customer_query = " ".join(sys.argv[1:])
        if not customer_query or not customer_query.strip():
            print("Debe ingresar un comando valido")
            sys.exit(1)

        print(f"\n{Style.BRIGHT}[PASO A]{RESET} Invocando {H_COLOR}'logistics_manager'{RESET} (MCP: analyze_order)...")
        
        def create_mcp_payload(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
            """Genera una carga útil MCP JSON-RPC 2.0 compatible con AAIF 2026."""
            return {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                },
                "id": f"mcp-{uuid.uuid4().hex[:8]}"
            }

        step0_correlation_id = str(uuid.uuid4())
        
        analysis_res = await router.route_message(
            sender_id="customer_bot",
            recipient_id="logistics_manager",
            content={
                "prompt": customer_query
            },
            message_type=MessageType.REQUEST,
            correlation_id=step0_correlation_id
        )
        
        analysis_text = "Analysis completed."
        if analysis_res and "result" in analysis_res:
            res_content = analysis_res.get("result", {})
            if isinstance(res_content, dict):
                analysis_text = res_content.get("output", analysis_text)
                content_list = res_content.get("content", [])
                if content_list and isinstance(content_list, list):
                    analysis_text = content_list[0].get("text", content_list[0].get("json", analysis_text))
            print(f"   {OK_COLOR}✅ OK: LangChain analizó la solicitud (LLM Call #1).{RESET}")
        
        print(f"\n{Style.BRIGHT}[PASO B]{RESET} Invocando {H_COLOR}'route_optimizer'{RESET} (A2A: tasks/create)...")
        route_res = await router.route_message(
            sender_id="logistics_manager",
            recipient_id="route_optimizer",
            content={
                "prompt": f"Optimizar ruta basada en el análisis: {str(analysis_text)[:150]}...",
                "package_id": "ORD-2025-001"
            },
            message_type=MessageType.REQUEST,
            correlation_id=step0_correlation_id
        )
        
        route_text = "Route planned."
        if route_res and "result" in route_res:
             res_content = route_res.get("result", {})
             route_text = res_content.get("output", "Route optimized.")
             print(f"   {OK_COLOR}✅ OK: Tarea A2A 'route_planning' completada.{RESET}")

        print(f"\n{Style.BRIGHT}[PASO C]{RESET} Invocando {H_COLOR}'fleet_commander'{RESET} (A2A: Fleet Assignment)...")
        fleet_res = await router.route_message(
            sender_id="route_optimizer",
            recipient_id="fleet_commander",
            content={
                "prompt": f"Asignar flota para la ruta: {str(route_text)[:150]}...",
                "package_id": "ORD-2025-001"
            },
            message_type=MessageType.REQUEST,
            correlation_id=step0_correlation_id
        )
        
        fleet_text = "Fleet assigned."
        if fleet_res and "result" in fleet_res:
            fleet_res_content = fleet_res.get("result", {})
            fleet_text = fleet_res_content.get("output", "Fleet assignment completed.") if isinstance(fleet_res_content, dict) else "Fleet assigned."
            print(f"   {OK_COLOR}✅ OK: Flota asignada correctamente.{RESET}")
            print(f"\n{H_COLOR}[FINAL REPORT] Carga útil de respuesta final recibida con éxito.{RESET}")
            
        # 5. Validación de Resiliencia (Captura en Outbox)
        print(f"\n{STEP_COLOR}[STEP 4] Validación de Resiliencia (Outbox Pattern)...{RESET}")
        
        offline_target = "non_existent_emergency_backup"
        print(f"  Enviando mensaje a agente desconectado '{offline_target}'...")
        
        correlation_id = "logistics_dashboard"
        await router.route_message(
            sender_id="logistics_manager",
            recipient_id=offline_target,
            content={"alert": "System connectivity heartbeat test"},
            message_type=MessageType.REQUEST,
            correlation_id=correlation_id
        )
        
        from rayrabbit.resilience.offline_tolerance import OutboxStore
        store = OutboxStore()
        pending = await store.get_pending_messages()
        if any(m.recipient_id == offline_target for m in pending):
            print(f"   {OK_COLOR}✅ VERIFICADO: El mensaje a '{offline_target}' fue capturado en el OUTBOX exitosamente.{RESET}")

        # 6. Dashboard Final
        print(f"\n{STEP_COLOR}[STEP 5] Estado Final del Ecosistema:{RESET}")
        dashboard.render_cli()

        print(f"\n{META_COLOR}[WAIT] Esperando consolidación final de auditoría...{RESET}")
        await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"Fallo en la prueba de orquestación: {e}", exc_info=True)
    finally:
        print("\n[CLEANUP] Deteniendo infraestructura local...")
        if 'a2a_server' in locals() and a2a_server is not None:
            await a2a_server.stop()
        if 'bus' in locals() and bus is not None:
            await bus.stop()
        if 'discovery' in locals() and discovery is not None: await discovery.stop()
        if 'audit_manager' in locals() and audit_manager is not None: await audit_manager.stop()
        
        print(f"{OK_COLOR}[CLEANUP] Infraestructura detenida correctamente.{RESET}")

    print("\n" + H_COLOR + "="*80)
    print(f"{H_COLOR} E2E AAIF VALIDATION COMPLETED ".center(88, "="))
    print(H_COLOR + "="*80 + RESET)

if __name__ == "__main__":
    asyncio.run(run_federated_logistics_aaif())
