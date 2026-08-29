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
import datetime
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from ..utils.logger import get_logger
from ..utils.agents_md_parser import AgentsMdParser
from ..protocols.a2a_router import AgentCard, A2ARouter
from ..security.auditing import AuditManager, AuditEvent

class DiscoveryService:
    """
    Servicio de descubrimiento AAIF para RayRabbit.
    Garantiza que la infraestructura sea consciente de todos los agentes disponibles,
    sus protocolos soportados y sus capacidades.
    """
    
    def __init__(self, a2a_router: A2ARouter, search_paths: Optional[List[str]] = None, audit_manager: Optional[AuditManager] = None):
        self.a2a_router = a2a_router
        self.audit_manager = audit_manager
        self.search_paths = search_paths or []
        self.parser = AgentsMdParser()
        self.logger = get_logger("DiscoveryService")
        self.is_running = False

    async def start(self):
        """Inicia el escaneo periódico de agentes."""
        self.is_running = True
        self.logger.info("Servicio de descubrimiento AAIF iniciado.")
        asyncio.create_task(self._discovery_loop())

    async def stop(self):
        """Detiene el servicio de descubrimiento."""
        self.is_running = False
        self.logger.info("Servicio de descubrimiento AAIF detenido.")

    async def scan_now(self):
        """Realiza un escaneo inmediato de las rutas configuradas."""
        self.logger.info(f"Escaneando agentes en: {self.search_paths}")
        for path_str in self.search_paths:
            path = Path(path_str)
            if not path.exists():
                continue
            
            # Buscar archivos NODOS.md recursivamente
            for agents_file in path.rglob("NODOS.md"):
                await self._process_agent_file(agents_file)

    async def _discovery_loop(self):
        """Bucle de descubrimiento en segundo plano."""
        while self.is_running:
            try:
                await self.scan_now()
            except Exception as e:
                self.logger.error(f"Error en bucle de descubrimiento: {e}")
            await asyncio.sleep(60) # Escanear cada minuto

    async def _process_agent_file(self, file_path: Path):
        """Procesa un archivo NODOS.md y registra los agentes en el router."""
        agents_metadata = self.parser.parse_file(str(file_path))
        
        for metadata in agents_metadata:
            if not metadata.get("id"):
                continue

            card = AgentCard(
                agent_id=metadata["id"],
                name=metadata["name"],
                protocols=metadata["protocols"],
                capabilities=metadata["capabilities"],
                endpoints=metadata["endpoints"],
                description=metadata.get("description", "")
            )
            
            # Registrar en el router (lo cual habilita routing inteligente)
            await self.a2a_router.register_agent(card)
            
            # Auditar descubrimiento
            if self.audit_manager:
                from ..security.auditing import AuditLevel, EventCategory
                self.audit_manager.log_event(
                    level=AuditLevel.INFO,
                    category=EventCategory.AGENT_ACTION,
                    event_type="AGENT_DISCOVERED",
                    agent_id="discovery_service",
                    action="scan_agents_md",
                    result="SUCCESS",
                    details={"agent_id": card.agent_id, "protocols": card.protocols}
                )
                
            self.logger.info(f"Agente discovered y registrado: {card.agent_id} ({card.name})")

    async def register_remote_agent(self, agents_md_url: str):
        """
        Descubrimiento dinámico de un agente remoto vía URL.
        En una implementación futura, esto podría usar MCP para auto-discovery.
        """
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(agents_md_url)
                response.raise_for_status()
                metadata = self.parser.parse(response.text)
                await self._process_metadata(metadata)
        except Exception as e:
            self.logger.error(f"Error al registrar agente remoto desde {agents_md_url}: {e}")

    async def _process_metadata(self, metadata: Dict[str, Any]):
        """Procesa metadata cruda y la registra en el router."""
        if not metadata.get("id"): return
        card = AgentCard(
            agent_id=metadata["id"],
            name=metadata["name"],
            protocols=metadata["protocols"],
            capabilities=metadata["capabilities"],
            endpoints=metadata["endpoints"]
        )
        await self.a2a_router.register_agent(card)
