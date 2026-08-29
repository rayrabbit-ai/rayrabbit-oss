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
from pathlib import Path
import importlib.metadata
import sys
from typing import Dict, Any, List, Optional
import os # Added for environment variable access

from .agent import Agent
from .message_bus import MessageBus
from ..utils.logger import get_logger
from ..utils.config import RayRabbitConfig
from ..security.encryption_defs import KeyType
from ..security.maestro import MAESTROSecurity
from ..security.auditing import AuditManager
from ..security.sqlite_audit_provider import SQLiteAuditProvider
from .bridge import DeclarativeBridge


class RayRabbitFramework:
    def __init__(self, config: RayRabbitConfig) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.config = config
        
        if not config.security:
            raise ValueError("La configuración de seguridad no puede ser nula al inicializar el framework.")

        # 1. Crear el AuditManager
        self.audit_manager = AuditManager()

        # 2. Crear la instancia de seguridad principal, inyectando el AuditManager
        self.framework_security = MAESTROSecurity("rayrabbit_core", config=config.security, audit_manager=self.audit_manager)

        # 3. Configurar el proveedor de auditoría dinámicamente
        auditing_config = self.config.auditing # Acceder a la nueva sección de auditoría
        
        if auditing_config.enable_audit: # Access attribute directly
            storage_provider_type = auditing_config.storage_provider # Access attribute directly
            if storage_provider_type == "sqlite":
                # Obtener db_path de la configuración o de la variable de entorno
                db_path_from_config = auditing_config.sqlite_db_path # Access attribute directly
                db_path = os.getenv("RAYRABBIT_AUDIT_DB_PATH", db_path_from_config)
                
                audit_provider = SQLiteAuditProvider(db_path, self.framework_security)
                self.audit_manager.set_storage_provider(audit_provider)
                self.logger.info(f"AuditManager configurado con SQLiteAuditProvider en: {db_path}")
            else:
                self.logger.warning(f"Proveedor de almacenamiento de auditoría '{storage_provider_type}' no soportado o no especificado. La auditoría estará deshabilitada.")
        else:
            self.logger.info("La auditoría está deshabilitada según la configuración.")
        
        self.message_bus = MessageBus(config.message_bus, security_module=self.framework_security)
        
        self.is_running = False
        self.agents: Dict[str, "Agent"] = {}
        self.bridge_startup_tasks: List[asyncio.Task] = []
        self._bridge_readiness_status: Dict[str, bool] = {} # Added to track bridge readiness

    def set_bridge_ready(self, bridge_id: str, is_ready: bool) -> None:
        """Actualiza el estado de preparación de un bridge."""
        self._bridge_readiness_status[bridge_id] = is_ready
        self.logger.info(f"Estado de preparación del bridge '{bridge_id}' actualizado a {is_ready}.")

    def get_bridge_readiness_status(self) -> Dict[str, bool]:
        """Devuelve el estado de preparación actual de todos los bridges."""
        return self._bridge_readiness_status

    async def start(self) -> None:
        self.logger.info("Iniciando RayRabbit Infraestructura...")
        # Solo iniciar el AuditManager si tiene un proveedor configurado
        if self.audit_manager.storage_provider:
            await self.audit_manager.start() # Iniciar el gestor de auditoría
        else:
            self.logger.warning("AuditManager no tiene un proveedor de almacenamiento configurado, no se iniciará.")
            
        await self.message_bus.start()
        
        # Iniciar TaskEngine (MCP v2 Task Engine)
        try:
            from .task_engine import TaskStore, TaskManager
            task_db_dir = Path(".rayrabbit_data")
            task_db_dir.mkdir(parents=True, exist_ok=True)
            self.task_store = TaskStore(db_path=task_db_dir / "tasks.db")
            self.task_manager = TaskManager(store=self.task_store, message_bus=self.message_bus)
            self.logger.info("HUB: TaskEngine (MCP v2 Task Engine) iniciado y respaldado en SQLite.")
        except Exception as e:
            self.logger.error(f"HUB: Error iniciando TaskEngine: {e}")
        
        # Registrar componentes del sistema
        await self._register_declarative_bridges()
        await self._register_internal_agents_from_config()

        self.is_running = True
        self.logger.info("RayRabbit Infraestructura iniciado y listo.")

    async def stop(self) -> None:
        self.logger.info("Deteniendo RayRabbit Infraestructura...")
        # Detener en orden inverso al de arranque
        # Cancelar las tareas de tareas de inicio de bridges en segundo plano
        for task in self.bridge_startup_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task # Esperar a que la tarea se cancele
                except asyncio.CancelledError:
                    self.logger.info("Tarea de inicio de bridge en segundo plano cancelada.")

        for agent in list(self.agents.values()):
            await agent.stop()
        
        await self.message_bus.stop()
        # Solo detener el AuditManager si tiene un proveedor configurado
        if self.audit_manager.storage_provider:
            await self.audit_manager.stop() # Detener el gestor de auditoría principal
        self.is_running = False
        self.logger.info("RayRabbit Infraestructura detenido.")
        
    async def register_agent(self, agent: Agent) -> None:
        if agent.id in self.agents and self.agents[agent.id] is not None:
            self.logger.warning(f"El agente con ID '{agent.id}' ya está registrado.")
            return
        
        agent.set_message_bus(self.message_bus)

        security_config = self.config.security
        if security_config and security_config.enable_auth:
            # --- Arquitectura Shared Nothing: Auditoría por Agente ---
            # Cada agente tiene su propio AuditManager y su propia base de datos cifrada.
            agent_audit_manager = AuditManager()
            
            # Definir la ruta de la base de datos para este agente específico usando Path
            agent_db_dir = Path("audit_logs")
            agent_db_dir.mkdir(parents=True, exist_ok=True)
            agent_db_path = str(agent_db_dir / f"agent_{agent.id}_audit.db")
            
            # El proveedor utiliza la seguridad del framework para el cifrado persistente
            # pero apunta a un archivo específico del agente.
            agent_provider = SQLiteAuditProvider(db_path=agent_db_path, maestro=self.framework_security)
            agent_audit_manager.set_storage_provider(agent_provider)
            
            # Iniciar el gestor de auditoría del agente
            await agent_audit_manager.start()
            
            # Inyectar MAESTRO al agente con su gestor de auditoría dedicado
            agent.maestro = MAESTROSecurity(agent.id, config=security_config, audit_manager=agent_audit_manager)
            self.logger.info(f"Auditoría 'Shared Nothing' configurada para el agente '{agent.id}' en: {agent_db_path}")

        self.agents[agent.id] = agent
        await self.message_bus.register_agent(agent)
        
        await agent.start()

        self.logger.info(f"Agente '{agent.id}' registrado, configurado y asegurado por MAESTRO.")

        # Actualizar el caché de claves de todos los agentes
        await self._update_all_agent_caches()

    async def _register_declarative_bridges(self) -> None:
        """Lee la config y registra un DeclarativeBridge por cada servicio externo."""
        self.logger.info("Registrando Bridges Declarativos desde la configuración...")
        
        # Corregido: Leer desde self.config.custom
        discovery_config = self.config.custom.get('discovery', {})
        strategy = discovery_config.get('strategy', 'none')
        
        # NUEVO: Soporte para modo P2P (sin bridges, solo handshake directo)
        communication_mode = discovery_config.get('communication_mode', 'bridge')  # Default: bridge
        
        if communication_mode == 'p2p':
            self.logger.info("Modo P2P activo. Bridges deshabilitados. Solo acepta registro vía Handshake.")
            return  # No crear bridges en modo P2P

        if strategy == 'static':
            # Leer desde la nueva sección semánticamente correcta: declarative_bridges
            declarative_bridges = self.config.custom.get('declarative_bridges', [])
            
            # Fallback legacy para retrocompatibilidad
            if not declarative_bridges:
                declarative_bridges = self.config.custom.get('external_services', [])
                if declarative_bridges:
                    self.logger.warning("Usando 'external_services' obsoleto. Mueva sus bridges a 'declarative_bridges:' en config.yaml")

            self.logger.info(f"Estrategia de descubrimiento 'static' seleccionada. Encontrados {len(declarative_bridges)} bridges declarativos.")

            
            for service_config in declarative_bridges:
                service_name = service_config.get('name')
                if not service_name:
                    self.logger.warning("Se encontró una definición de servicio sin nombre, saltando...")
                    continue
                
                bridge_id = f"{service_name}_bridge"
                self.logger.info(f"Creando bridge declarativo con ID: {bridge_id}")
                
                try:
                    # Inicializar el estado de preparación del bridge a False
                    self.set_bridge_ready(bridge_id, False)
                    bridge = DeclarativeBridge(agent_id=bridge_id, service_config=service_config, framework=self) # Pass framework reference
                    # Lanzar la registración del bridge como una tarea en segundo plano
                    # Esto permite que el framework se inicie completamente sin esperar
                    # a que los bridges se conecten a sus servicios externos.
                    self.bridge_startup_tasks.append(asyncio.create_task(self.register_agent(bridge)))
                    self.logger.info(f"Tarea de inicio para el bridge '{bridge_id}' lanzada en segundo plano.")
                except Exception as e:
                    self.logger.error(f"Error al crear o lanzar la tarea de inicio para el bridge '{bridge_id}': {e}", exc_info=True)
        else:
            self.logger.info(f"Estrategia de descubrimiento '{strategy}' seleccionada. No se registrarán bridges estáticos.")

    async def _register_internal_agents_from_config(self) -> None:
        """
        Lee la configuración y registra agentes internos definidos en 'custom.internal_agents'.
        """
        self.logger.info("Registrando agentes internos desde la configuración...")
        internal_agents_config = self.config.custom.get('internal_agents', [])

        for agent_def in internal_agents_config:
            agent_id = agent_def.get('id')
            agent_name = agent_def.get('name', agent_id)
            agent_config = agent_def.get('config', {}) # Configuración adicional para el constructor del agente

            module_name = agent_def.get('module')
            class_name = agent_def.get('class')
            agent_type_str = agent_def.get('type') # Mantener para compatibilidad si se usa 'type'

            if not agent_id:
                self.logger.warning(f"Definición de agente interno sin 'id', saltando: {agent_def}")
                continue

            try:
                if agent_type_str: # Si se usa la definición 'type'
                    module_name, class_name = agent_type_str.rsplit('.', 1)
                elif module_name and class_name: # Si se usa 'module' y 'class'
                    pass # Ya tenemos module_name y class_name
                else:
                    self.logger.warning(f"Definición de agente interno incompleta (falta 'type' o 'module'/'class'), saltando: {agent_def}")
                    continue

                # Importar dinámicamente la clase del agente
                module = importlib.import_module(module_name)
                agent_class = getattr(module, class_name)

                # Instanciar el agente. Asumimos que el constructor acepta agent_id, name y config.
                # Si el constructor es diferente, esto necesitará ser más flexible.
                agent_instance = agent_class(agent_id=agent_id, name=agent_name, **agent_config)
                
                await self.register_agent(agent_instance)
                self.logger.info(f"Agente interno '{agent_name}' ({agent_id}) registrado exitosamente.")
            except Exception as e:
                self.logger.error(f"Error al registrar agente interno '{agent_id}' de tipo '{agent_type_str}': {e}", exc_info=True)

    async def _update_all_agent_caches(self) -> None:
        """Recolecta todas las claves públicas y las distribuye a todos los agentes."""
        self.logger.info("Actualizando cachés de claves públicas para todos los agentes...")
        full_public_key_cache = {}
        for agent_in_system in self.agents.values():
            if agent_in_system.maestro:
                public_key = agent_in_system.maestro.get_identity_key(KeyType.PUBLIC)
                if public_key:
                    full_public_key_cache[agent_in_system.id] = public_key
        
        if not full_public_key_cache:
            self.logger.warning("No se encontraron claves públicas para distribuir.")
            return

        for agent_to_update in self.agents.values():
            if agent_to_update.maestro:
                agent_to_update.maestro.update_public_key_cache(full_public_key_cache)

    def get_agent(self, agent_id: str) -> Agent | None:
        return self.agents.get(agent_id)