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
import json
from typing import Dict, Any, Optional

import aiohttp

from .agent import Agent, AgentStatus
from ..communication.message import Message, MessageType
from ..utils.exceptions import RayRabbitError
from ..security.auditing import AuditLevel, EventCategory
from ..security.encryption_defs import KeyType # AÑADIDO: Importar KeyType


class DeclarativeBridge(Agent):
    """
    Un agente que actúa como un puente declarativo a un servicio externo.

    Este puente se configura con los detalles de un servicio externo y utiliza
    su contrato OpenAPI para descubrir dinámicamente los endpoints y traducir
    los mensajes del MessageBus de RayRabbit en llamadas HTTP a ese servicio.
    """

    def __init__(self, agent_id: str, service_config: Dict[str, Any], framework: Any): # Added framework
        """
        Inicializa el DeclarativeBridge.

        Args:
            agent_id: El ID único para esta instancia del bridge.
            service_config: El diccionario de configuración para el servicio externo
                            extraído de 'external_services' en config.yaml.
            framework: Una referencia a la instancia de RayRabbitFramework para actualizar el estado del bridge.
        """
        name = service_config.get("name", agent_id)
        description = service_config.get("description", f"Bridge para el servicio {name}")
        
        super().__init__(agent_id=agent_id, name=name, description=description)

        self.service_address = service_config.get("address")
        self.topics_to_subscribe = service_config.get("topics", [])
        self.framework = framework # Store framework reference
        self.service_config = service_config # Guardar config completa

        # Extraer configuración de red con fallbacks
        self.network_config = service_config.get("network", {})
        self.openapi_contract: Optional[Dict[str, Any]] = None
        self.http_client: Optional[aiohttp.ClientSession] = None
        # Diccionario para mapear operationId a detalles del endpoint
        self.path_handlers: Dict[str, Any] = {}
        self.MAX_RETRIES = self.network_config.get("max_retries", service_config.get("max_retries", 30))
        self.RETRY_DELAY_SECONDS = self.network_config.get("retry_delay_seconds", service_config.get("retry_delay_seconds", 2))
        
        self.logger.info(f"DeclarativeBridge para el servicio '{name}' inicializado.")
        self.logger.info(f"Dirección del servicio: {self.service_address}")
        self.logger.info(f"Topics a suscribir: {self.topics_to_subscribe}")

    async def start(self) -> None:
        """
        Inicia el bridge y lanza la tarea de monitoreo de salud en segundo plano.
        """
        await super().start()
        self.logger.info(f"Iniciando lógica resiliente del DeclarativeBridge para '{self.name}'...")

        if not self.service_address:
            self.logger.error("No se ha configurado una dirección para el servicio externo.")
            self.status = AgentStatus.ERROR
            self.framework.set_bridge_ready(self.id, False)
            return

        # Extraer parámetros de red dinámicos de config.yaml section 'network'
        net = self.network_config
        timeout_total = net.get("timeout_total", 60)
        timeout_connect = net.get("timeout_connect", 10)
        timeout_read = net.get("timeout_read", 60)
        keepalive = net.get("keepalive_timeout", 60)

        # Configurar TCP connector para soporte cross-platform y federación
        connector = aiohttp.TCPConnector(
            limit=30,                    # Max total connections
            limit_per_host=10,           # Max per host
            ttl_dns_cache=300,           # DNS cache (cross-cloud safe)
            keepalive_timeout=keepalive,  # Dinámico (default 60s)
            enable_cleanup_closed=True,  # Auto-cleanup
            force_close=False            # Reusar conexiones
        )

        # Configurar timeouts agnósticos de plataforma
        timeout = aiohttp.ClientTimeout(
            total=timeout_total,         # Dinámico (default 60s)
            connect=timeout_connect,     # Dinámico (default 10s)
            sock_read=timeout_read,       # Dinámico (default 60s)
            sock_connect=timeout_connect # Usar connect timeout para socket tmb
        )

        # Crear sesión HTTP con configuración robusta y dinámica
        self.http_client = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        self.logger.info(
            f"Bridge '{self.name}' inicializado: timeout={timeout.total}s, "
            f"keepalive={connector._keepalive_timeout}s, retries={self.MAX_RETRIES}"
        )
        
        # Suscribirse a los topics inmediatamente
        if self.message_bus:
            for topic in self.topics_to_subscribe:
                self.message_bus.subscribe(topic, self.id)
                self.logger.info(f"Suscrito al topic: {topic}")

        # Lanzar monitoreo de salud en segundo plano
        self._health_check_task = asyncio.create_task(self._monitor_service_health())

    async def _monitor_service_health(self) -> None:
        """Tarea en segundo plano que monitorea la disponibilidad del servicio externo."""
        contract_url = f"{self.service_address}/openapi.json"
        is_first_check = True
        
        while self.is_running:
            try:
                if not self.openapi_contract:
                    self.logger.info(f"Intentando conectar con el servicio en {contract_url}...")
                    async with self.http_client.get(contract_url, timeout=30) as response:
                        if response.status == 200:
                            self.openapi_contract = await response.json()
                            self._register_handlers_from_contract()
                            self.framework.set_bridge_ready(self.id, True)
                            self.logger.info(f"¡CONECTADO! Servicio '{self.name}' está listo y contrato cargado.")
                        else:
                            self.framework.set_bridge_ready(self.id, False)
                else:
                    # Si ya tenemos contrato, solo verificamos que el servicio siga vivo
                    async with self.http_client.get(f"{self.service_address}/health", timeout=10) as response:
                        if response.status != 200:
                            self.logger.warning(f"Servicio '{self.name}' no responde a health check. Marcando como NO LISTO.")
                            self.framework.set_bridge_ready(self.id, False)
                            self.openapi_contract = None # Forzar recarga si vuelve
                        else:
                            self.framework.set_bridge_ready(self.id, True)
            
            except Exception as e:
                if is_first_check:
                    self.logger.info(f"Servicio '{self.name}' aún no disponible (|{type(e).__name__}|), reintentando de fondo...")
                    is_first_check = False
                self.framework.set_bridge_ready(self.id, False)
                self.openapi_contract = None

            await asyncio.sleep(5) # Verificar cada 5 segundos

    def _register_handlers_from_contract(self) -> None:
        """Registra handlers dinámicamente desde el contrato OpenAPI."""
        if not self.openapi_contract or "paths" not in self.openapi_contract:
            return
            
        self.path_handlers.clear()
        for path, path_item in self.openapi_contract["paths"].items():
            for method, operation in path_item.items():
                if "operationId" in operation:
                    op_id = operation["operationId"]
                    self.path_handlers[op_id] = {
                        "path": path,
                        "method": method.upper()
                    }
                    self.logger.debug(f"Handler registrado: {op_id} -> {method.upper()} {path}")

    async def stop(self) -> None:
        """
        Detiene el bridge, cerrando la sesión HTTP.
        """
        self.logger.info(f"Deteniendo DeclarativeBridge para '{self.name}'...")
        if self.http_client and not self.http_client.closed:
            await self.http_client.close()
            self.logger.info("Sesión HTTP cerrada.")
        self.framework.set_bridge_ready(self.id, False) # Mark as not ready on stop
        await super().stop()

    async def _load_openapi_contract(self) -> None:
        """
        Descarga y procesa el contrato OpenAPI para registrar los handlers dinámicamente.
        Implementa un mecanismo de reintento con backoff exponencial.
        """
        if not self.http_client:
            raise RayRabbitError("El cliente HTTP no está inicializado.")

        contract_url = f"{self.service_address}/openapi.json"
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            self.logger.info(f"Intento {attempt}/{self.MAX_RETRIES}: Descargando contrato OpenAPI desde: {contract_url}")
            try:
                async with self.http_client.get(contract_url) as response:
                    response.raise_for_status()
                    self.openapi_contract = await response.json()
                    self.logger.info("Contrato OpenAPI descargado y parseado con éxito.")

                # Registrar handlers dinámicamente desde el contrato
                self.logger.info("Registrando handlers desde el contrato OpenAPI...")
                if "paths" in self.openapi_contract:
                    for path, path_item in self.openapi_contract["paths"].items():
                        for method, operation in path_item.items():
                            if "operationId" in operation:
                                op_id = operation["operationId"]
                                self.path_handlers[op_id] = {
                                    "path": path,
                                    "method": method.upper()
                                }
                                self.logger.info(f"Handler registrado para operación '{op_id}': {method.upper()} {path}")
                if not self.path_handlers:
                    self.logger.warning("No se encontraron operaciones con 'operationId' en el contrato OpenAPI.")
                
                self.framework.set_bridge_ready(self.id, True) # Mark as ready
                return # Exit if successful

            except aiohttp.ClientError as e:
                self.logger.warning(f"Error de red al descargar el contrato OpenAPI (intento {attempt}): {e}")
            except Exception as e:
                self.logger.warning(f"Error al procesar el contrato OpenAPI (intento {attempt}): {e}")
            
            if attempt < self.MAX_RETRIES:
                delay = self.RETRY_DELAY_SECONDS * (2 ** (attempt - 1)) # Exponential backoff
                self.logger.info(f"Reintentando en {delay:.1f} segundos...")
                await asyncio.sleep(delay)
            else:
                self.logger.error(f"Fallaron todos los {self.MAX_RETRIES} intentos para descargar el contrato OpenAPI desde {contract_url}.")
                self.framework.set_bridge_ready(self.id, False) # Mark as not ready
                raise RayRabbitError(f"No se pudo descargar el contrato OpenAPI después de {self.MAX_RETRIES} intentos.")
    async def _handle_request(self, message: Message) -> Optional[Message]:
        """
        Maneja dinámicamente los mensajes de tipo REQUEST basándose en el contrato OpenAPI,
        añadiendo auditoría y firma de seguridad.
        """
        if not self.http_client or not self.path_handlers:
            error_msg = "El bridge no está operativo (sin cliente HTTP o sin handlers registrados)."
            self.logger.error(error_msg)
            return self._create_error_response(message, error_msg)

        # 1. Validar contenido del mensaje y obtener la operación
        if not isinstance(message.content, dict) or "operation" not in message.content:
            return self._create_error_response(message, "El contenido del mensaje debe ser un diccionario con el campo 'operation'.")
        
        operation_id = message.content["operation"]
        self.logger.info(f"Procesando request para la operación '{operation_id}' en el servicio '{self.name}'")

        # 2. Encontrar el handler para la operación solicitada
        if operation_id not in self.path_handlers:
            return self._create_error_response(message, f"Operación desconocida: '{operation_id}'. Operaciones disponibles: {list(self.path_handlers.keys())}")
            
        handler_info = self.path_handlers[operation_id]
        target_path = handler_info["path"]
        http_method = handler_info["method"]
        target_url = f"{self.service_address}{target_path}"

        # 3. Preparar y enviar la petición HTTP
        # 3. Preparar y enviar la petición HTTP con reintentos
        for attempt in range(1, self.MAX_RETRIES + 1): # Añadir bucle de reintentos
            try:
                payload = {k: v for k, v in message.content.items() if k != 'operation'}
                # Inyectar correlation_id en el payload para que el servicio pueda propagarlo
                payload['correlation_id'] = message.correlation_id
                headers = {}

                # --- INICIO: Auditoría y Firma (MAESTRO Security) ---
                if self.maestro:
                    # 3.1. Registrar el evento de auditoría ANTES de la acción
                    self.maestro.audit_manager.log_event(
                        level=AuditLevel.INFO,
                        category=EventCategory.AGENT_ACTION,
                        event_type="EXTERNAL_API_CALL",
                        action="REQUEST",
                        result="PENDING",
                        agent_id=self.id,
                        correlation_id=message.correlation_id,
                        details={
                            "target_service": self.name,
                            "operation_id": operation_id,
                            "target_url": target_url,
                            "payload_preview": str(payload)[:256]
                        }
                    )

                    # 3.2. Obtener cabeceras de seguridad OO
                    headers = self.maestro.get_jws_headers(payload, correlation_id=message.correlation_id)
                    self.logger.info(f"BRIDGE OO: Cabeceras de seguridad generadas para {self.name}.")
                    self.logger.debug(f"Petición a '{self.name}' firmada con JWS empresarial ({self.id}).")
                # --- FIN: Auditoría y Firma ---

                self.logger.debug(f"Ejecutando {http_method} a {target_url}. Intento {attempt}/{self.MAX_RETRIES}")
                self.logger.info(f"Payload enviado a servicio externo: {json.dumps(payload, indent=2)}") # <-- Añadir este log

                async with self.http_client.request(http_method, target_url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    service_response_data = await response.json()

                    self.logger.info(f"Respuesta recibida del servicio externo para la operación '{operation_id}'.")
                    self.logger.debug(f"Datos de respuesta: {service_response_data}")

                    # --- INICIO: Auditoría SUCCESS (MAESTRO Security) ---
                    if self.maestro:
                        self.maestro.audit_manager.log_event(
                            level=AuditLevel.INFO,
                            category=EventCategory.AGENT_ACTION,
                            event_type="EXTERNAL_API_CALL",
                            action="RESPONSE",
                            result="SUCCESS",
                            agent_id=self.id,
                            correlation_id=message.correlation_id, # Usar el ID de correlación del flujo
                            details={
                                "target_service": self.name,
                                "operation_id": operation_id,
                                "status_code": response.status
                            }
                        )
                    # --- FIN: Auditoría SUCCESS ---

                    # 4. Crear y devolver el mensaje de respuesta de RayRabbit
                    return Message(
                        sender_id=self.id,
                        sender_name=self.name,
                        recipient_id=message.sender_id,
                        message_type=MessageType.RESPONSE,
                        content=service_response_data,
                        correlation_id=message.correlation_id
                    )

            except aiohttp.ClientError as e:
                self.logger.warning(f"Error de red al comunicarse con el servicio externo (intento {attempt}): {e}")
            except Exception as e:
                self.logger.warning(f"Error inesperado al comunicarse con el servicio externo (intento {attempt}): {e}")
            
            if attempt < self.MAX_RETRIES:
                delay = self.RETRY_DELAY_SECONDS * (2 ** (attempt - 1)) # Exponential backoff
                self.logger.info(f"Reintentando en {delay:.1f} segundos...")
                await asyncio.sleep(delay)
            else:
                error_msg = f"Fallaron todos los {self.MAX_RETRIES} intentos para comunicarse con el servicio externo para la operación '{operation_id}'."
                self.logger.error(error_msg, exc_info=True)
                return self._create_error_response(message, error_msg)

        # Si el bucle termina sin éxito, se devuelve un error.
        error_msg = f"Error final al comunicarse con el servicio externo para la operación '{operation_id}' después de {self.MAX_RETRIES} intentos."
        self.logger.error(error_msg)
        return self._create_error_response(message, error_msg)

    def _create_error_response(self, original_message: Message, error: str) -> Message:
        """Crea un mensaje de error estandarizado."""
        return Message(
            sender_id=self.id,
            sender_name=self.name,
            recipient_id=original_message.sender_id,
            message_type=MessageType.ERROR,
            content={"error": error, "source": self.name},
            correlation_id=original_message.message_id
        )

