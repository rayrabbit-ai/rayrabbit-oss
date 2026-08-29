"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import os
import asyncio
from typing import Dict, Any, List
from ..core.message_bus import MessageBus
from ..protocols.a2a_router import A2ARouter
from ..security.auditing import AuditManager
from ..utils.logger import get_logger

class DashboardService:
    """
    Dashboard de Interoperabilidad Lite.
    Proporciona una vista consolidada del estado del ecosistema AAIF.
    """
    
    def __init__(self, bus: MessageBus, router: A2ARouter, audit_manager: AuditManager):
        self.bus = bus
        self.router = router
        self.audit_manager = audit_manager
        self.logger = get_logger("Dashboard")
        self.is_running = False

    def render_cli(self):
        """Renderiza una vista de consola del estado actual."""
        print("\n" + "="*80)
        print(" RAYRABBIT INTEROPERABILITY DASHBOARD (Lite) ".center(80, "="))
        print("="*80)
        
        # 1. Agentes Descubiertos
        print(f"\n[ AGENTES DESCUBIERTOS ({len(self.router.registry)}) ]")
        print(f"{'ID':<20} | {'Nombre':<30} | {'Protocolos':<25}")
        print("-" * 80)
        for agent_id, card in self.router.registry.items():
            protocols = ", ".join(card.protocols)
            print(f"{agent_id:<20} | {card.name[:30]:<30} | {protocols:<25}")
            
        # 2. Herramientas MCP
        mcp_tools = self.bus.mcp_protocol.mcp_factory.registered_services
        print(f"\n[ SERVICIOS MCP ACTIVOS ({len(mcp_tools)}) ]")
        print(f"{'Servicio':<20} | {'Herramientas':<55}")
        print("-" * 80)
        for service_id, data in mcp_tools.items():
            tools = ", ".join([t["name"] for t in data["tools"]])
            print(f"{service_id:<20} | {tools[:55]:<55}")

        # 3. Resiliencia (Circuit Breakers)
        print(f"\n[ MOTOR DE RESILIENCIA (Coolers) ]")
        print(f"{'Recurso/P2P':<35} | {'Estado':<15} | {'Fallos'}")
        print("-" * 80)
        for name, cooler in self.router.coolers.items():
            print(f"{name[-35:]:<35} | {cooler.state.value.upper():<15} | {cooler.failure_count}")

        # 4. Estadísticas del Bus y P2P
        print(f"\n[ MÉTRICAS DE MENSAJERÍA ]")
        metrics = self.bus.metrics
        p2p = self.router.metrics
        print(f"Hub  -> Enviados: {metrics['messages_sent']} | Recibidos: {metrics['messages_received']} | Errores: {metrics['errors']}")
        print(f"P2P  -> Enviados: {p2p['p2p_sent']} | Recibidos: {p2p['p2p_received']} | Errores: {p2p['p2p_errors']} | Fallbacks: {p2p['hub_fallback']}")
        
        print("\n" + "="*80)

    async def start_periodic_refresh(self, interval: int = 5):
        """Inicia el refresco periódico del dashboard en consola."""
        self.is_running = True
        while self.is_running:
            # En un entornos productivos usar una librería de TUI como rich o curses
            # Aquí limpiamos pantalla de forma sencilla
            os.system('cls' if os.name == 'nt' else 'clear')
            self.render_cli()
            await asyncio.sleep(interval)

    def stop(self):
        self.is_running = False
