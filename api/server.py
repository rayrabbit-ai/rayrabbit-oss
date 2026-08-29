import asyncio
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import importlib.metadata
from typing import cast
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
import json

# --- Importaciones de RayRabbit ---
from rayrabbit.communication.message import Message, MessageType
from rayrabbit.core.project import BaseProject
from rayrabbit.security.encryption_defs import KeyType 
from rayrabbit.utils.logger import get_logger 
from rayrabbit.utils.config import ConfigManager, RayRabbitConfig
from rayrabbit.core.agent import Agent
from rayrabbit.core.framework import RayRabbitFramework
from rayrabbit.core.runtime_context import RuntimeContext
from rayrabbit.protocols.a2ui.agent import SovereignA2UIAgent
from rayrabbit.utils.tool_search_engine import match_top_k_tools
from rayrabbit.utils.tool_result_storage import maybe_persist_tool_result
from rayrabbit.version import __version__
import os 
import sys
import threading
import platform
import urllib.parse
import httpx
from typing import Any
from datetime import datetime

logger = get_logger(__name__)

async def _discover_p2p_mcp_tools(agent_id: str, p2p_endpoint: str, infrastructure: Any) -> None:
    """
    Consulta asíncronamente GET <p2p_base_url>/mcp/tools para descubrir las herramientas MCP
    expuestas por un servicio P2P e inscribirlas dinámicamente en mcp_protocol.tools.
    """
    try:
        parsed = urllib.parse.urlparse(p2p_endpoint)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        mcp_tools_url = f"{base_url}/mcp/tools"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(mcp_tools_url)
            if resp.status_code == 200:
                data = resp.json()
                tools_list = data.get("tools", [])
                mcp_proto = getattr(infrastructure.message_bus, "mcp_protocol", None)
                if mcp_proto and isinstance(tools_list, list):
                    for tool in tools_list:
                        tool_name = tool.get("name") if isinstance(tool, dict) else getattr(tool, "name", None)
                        if tool_name:
                            schema = dict(tool) if isinstance(tool, dict) else {}
                            mcp_proto.register_tool(tool_name, agent_id, schema)
                            logger.info(f"HUB: Herramienta P2P MCP '{tool_name}' auto-descubierta y registrada para '{agent_id}'.")
    except Exception as e:
        logger.debug(f"HUB: No se pudieron auto-descubrir herramientas P2P en {p2p_endpoint} para '{agent_id}' (puede ser normal si el agente no expone MCP): {e}")


# === Fábrica de Proyectos (rayrabbit.projects) ===
_project_instances: dict[str, BaseProject] = {}
def project_factory(project_name: str) -> BaseProject:
    """Obtiene la instancia única de un proyecto (patrón Singleton)."""
    if project_name not in _project_instances:
        logger.info(f"[ProjectFactory] Creando nueva instancia para '{project_name}'.")
        try:
            for entry_point in importlib.metadata.entry_points(group='rayrabbit.projects'):
                if entry_point.name == project_name:
                    project_class = entry_point.load()
                    _project_instances[project_name] = cast(BaseProject, project_class(project_name=project_name))
                    break
            if project_name not in _project_instances:
                raise ProjectNotFound(f"No se encontró el proyecto '{project_name}'.")
        except Exception as e:
            logger.error(f"Fábrica: Error al cargar '{project_name}'. {e}", exc_info=True)
            raise
    return _project_instances[project_name]

class ProjectNotFound(Exception): pass

# === Modelos Pydantic ===
class UserQuery(BaseModel):
    project: str
    payload: dict

from typing import Optional, Dict, Any, List
import uuid

class BridgeTestPayload(BaseModel):
    prompt: str = "Escribe un haiku sobre la interoperabilidad de agentes de IA."

class PublishMessagePayload(BaseModel):
    sender_id: str
    sender_name: str
    recipient_id: str
    message_type: MessageType
    correlation_id: Optional[str] = None
    content: Dict[str, Any]

class A2UIUserActionPayload(BaseModel):
    agent_id: str
    surface_id: str # Añadido para contexto
    action: Dict[str, Any]

class RegisterPublicKeyPayload(BaseModel): # Nuevo modelo para Identidad Soberana
    agent_id: str
    public_key_pem: str
    timestamp: str          # OSS: Handshake (PoP)
    signature: str          # OSS: Handshake (PoP)
    p2p_endpoint: Optional[str] = None # NUEVO: Para registro dinámico de ruteo
    openapi_url: Optional[str] = None  # NUEVO: Para registro dinámico de Bridges

class SearchToolsPayload(BaseModel):
    query: str = ""
    top_k: int = 4
    target_category: Optional[str] = None
    target_tools: Optional[str] = None
    agent_role: str = "cognitive_framework"



# === Agente UI Nativo: Corre como servicio soberano en Puerto 8006 ===
# Ver: rayrabbit/examples/logistics_use_case/native_a2ui_logistics.py

# === Creación de la Aplicación FastAPI ===
app = FastAPI(
    title="RayRabbit Core Infrastructure API",
    description="API Core que gestiona el ciclo de vida de la Infraestructura y orquesta la ejecución de entidades de IA.",
    version=__version__
)

# === Memoria L3: Global Infrastructure State ===
class InfrastructureMemoryL3:
    """Gestiona hechos globales persistentes (Facts) independientes de los agentes."""
    def __init__(self):
        self.brain_dir = RuntimeContext.get_agent_data_path("hub", "brain")
        os.makedirs(self.brain_dir, exist_ok=True)
        self.state_path = os.path.join(self.brain_dir, "global_state.json")
        self.facts: Dict[str, Any] = self._load()
        self._lock = threading.Lock()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"L3: Error cargando estado global: {e}")
        return {}

    def save(self):
        with self._lock:
            try:
                # Asegurar que el directorio existe antes de guardar
                os.makedirs(self.brain_dir, exist_ok=True)
                with open(self.state_path, "w", encoding="utf-8") as f:
                    json.dump(self.facts, f, indent=2)
            except Exception as e:
                logger.error(f"L3: Error persistiendo estado global: {e}")

    def update_fact(self, key: str, value: Any):
        self.facts[key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }
        self.save()

# Instancia global de Memoria L3 para el Hub
global_memory_l3 = InfrastructureMemoryL3()

# === Monitor de Componentes en Tiempo Real ===
def monitor_active_components():
    """Mapea y loguea los componentes cargados en el Hub (OSS Audit)."""
    try:
        internal_modules = [m for m in sys.modules if "rayrabbit" in m]
        external_modules = [m for m in sys.modules if "rayrabbit" not in m and not m.startswith("_")]
        
        audit_dir = Path("funcionalidad")
        audit_dir.mkdir(exist_ok=True)
        audit_log = audit_dir / "oss_audit.log"
        
        with open(audit_log, "a", encoding="utf-8") as f:
            f.write(f"\n--- AUDIT START: {uuid.uuid4()} ---\n")
            f.write(f"INTERNAL: {', '.join(internal_modules[:20])}... (Total: {len(internal_modules)})\n")
            f.write(f"EXTERNAL: {', '.join(external_modules[:20])}... (Total: {len(external_modules)})\n")
            f.write("--- AUDIT END ---\n")
        logger.info(f"AUDIT: Componentes activos mapeados en {audit_log}")
    except Exception as e:
        logger.error(f"AUDIT: Fallo en monitor de componentes: {e}")

# === Gestión de Archivos Estáticos (Dashboard y A2UI) ===
# Portar renderers y assets a rutas servibles
app.mount("/static/a2ui", StaticFiles(directory="rayrabbit/resources/a2ui-renderer"), name="a2ui_renderer")
app.mount("/dashboard", StaticFiles(directory="rayrabbit/resources/a2ui-dashboard", html=True), name="a2ui_dashboard")
if Path("rayrabbit/resources/assets").exists():
    app.mount("/static/assets", StaticFiles(directory="rayrabbit/resources/assets"), name="assets")

# === Gestión del Ciclo de Vida de la Infraestructura (Patrón Contenedor de Servicios) ===

@app.on_event("startup")
async def startup_event() -> None:
    """
    Crea e inicia la instancia Singleton de la Infraestructura RayRabbit.
    
    Utiliza el ConfigManager para cargar la configuración desde 'config.yaml' y
    la superpone con variables de entorno. Inicia todos los servicios y adaptadores
    configurados, que estarán disponibles durante todo el ciclo de vida del servidor.
    """
    logger.info("Evento de arranque: Iniciando Contenedor de Servicios de la Infraestructura RayRabbit...")
    
    # 1. Inicializar el gestor de configuración. Carga defaults y variables de entorno.
    config_manager = ConfigManager()
    
    # --- ACTIVACIÓN MEMORIA L3 ---
    logger.info(f"L3 Memory: Cargada con {len(global_memory_l3.facts)} hechos globales.")
    global_memory_l3.update_fact("system_status", "starting")
    global_memory_l3.update_fact("startup_node", platform.node())

    # 2. Cargar la configuración base desde el fichero YAML.
    try:
        config_manager.load_from_file("config.yaml")
        logger.info("Cargada configuración desde config.yaml")
    except FileNotFoundError:
        logger.warning("No se encontró 'config.yaml'. Se utilizará la configuración por defecto y las variables de entorno.")
    except Exception as e:
        logger.error(f"Error al cargar 'config.yaml': {e}", exc_info=True)
        # Decide si quieres abortar el inicio en caso de un config malformado
        raise

    # 3. Obtener el objeto de configuración final y validado.
    master_config: RayRabbitConfig = config_manager.data
    if not config_manager.validate():
        logger.error("La configuración cargada no es válida. Revisa los valores.")
        # Podrías querer abortar el inicio aquí también
        # raise ValueError("Configuración inválida")

    # 4. Iniciar la infraestructura con la configuración cargada en una tarea en segundo plano.
    # Esto permite que el servidor FastAPI se inicie rápidamente mientras los bridges
    # intentan conectar con los servicios externos de forma asíncrona.
    infrastructure = RayRabbitFramework(config=master_config)
    app.state.infrastructure = infrastructure # Hacer la infraestructura disponible inmediatamente
    
    # Crear una tarea en segundo plano para iniciar la infraestructura
    app.state.infrastructure_startup_task = asyncio.create_task(infrastructure.start())
    
    # Iniciar el Relay A2UI (Gestiona la conexión WebSocket para el protocolo)
    await setup_a2ui_relay(infrastructure)
    
    # === Agente UI Nativo DESACTIVADO en el Hub (ID Collision Prevention) ===
    # El Agente Logístico ahora corre como un servicio soberano independiente (Puerto 8006).
    # logger.info("[A2UI] Diseñador nativo omitido en el Hub (Uso de Servicio Soberano).")

    # Iniciar Memoria L3
    app.state.memory_l3 = InfrastructureMemoryL3()
    
    # Lanzar Monitor de Componentes
    monitor_active_components()

    logger.info("Infraestructura RayRabbit: Tarea de inicio lanzada. Relay A2UI activo.")

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Detiene de forma segura la instancia de la Infraestructura RayRabbit."""
    logger.info("Evento de apagado: Deteniendo Infraestructura RayRabbit...")
    
    # Cancelar la tarea de inicio en segundo plano si aún está activa
    if hasattr(app.state, 'infrastructure_startup_task') and not app.state.infrastructure_startup_task.done():
        app.state.infrastructure_startup_task.cancel()
        try:
            await app.state.infrastructure_startup_task # Esperar a que la tarea se cancele
        except asyncio.CancelledError:
            logger.info("Tarea de inicio de infraestructura en segundo plano cancelada.")

    if hasattr(app.state, 'infrastructure') and app.state.infrastructure:
        await app.state.infrastructure.stop()
    logger.info("Infraestructura RayRabbit detenida.")

# === Endpoints REST (Sin cambios en la lógica, solo en el tipado y acceso al estado) ===

@app.get("/health", tags=["Health"])
async def health_check(request: Request) -> Dict[str, Any]:
    infrastructure = getattr(request.app.state, 'infrastructure', None)
    is_running = infrastructure.is_running if infrastructure else False
    return {"status": "ok", "infrastructure_running": is_running}

@app.get("/api/bridges/readiness", tags=["Health"])
async def get_bridge_readiness(request: Request) -> Dict[str, bool]:
    """
    Devuelve el estado de preparación de todos los bridges registrados en la infraestructura.
    Indica si cada bridge ha inicializado correctamente su conexión con el servicio externo
    y ha procesado su contrato OpenAPI.
    """
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="La Infraestructura RayRabbit no está iniciada.")
    
    return infrastructure.get_bridge_readiness_status()

@app.post("/api/v1/test-bridge", tags=["Testing"])
async def test_declarative_bridge(payload: BridgeTestPayload, request: Request) -> Dict[str, str]:
    """
    Endpoint de prueba para validar la arquitectura del DeclarativeBridge.
    
    Publica un mensaje en el topic configurado para el langchain_service y
    devuelve una confirmación. La respuesta del servicio se verá en los logs.
    """
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="La Infraestructura RayRabbit no está iniciada.")

    logger.info("API: Recibida solicitud para probar el DeclarativeBridge.")
    
    # Construir el mensaje de prueba
    test_message = Message(
        sender_id="api_server",
        sender_name="APIServer",
        recipient_id="langchain_service_bridge", # ID del bridge, no el topic
        message_type=MessageType.REQUEST,
        content={
            "operation": "invoke_chain",
            "prompt": payload.prompt,
            "input_variables": ["prompt"] # <-- CAMPO AÑADIDO
        }
    )

    try:
        # Publicar el mensaje en el bus
        await infrastructure.message_bus.publish(test_message)
        logger.info(f"API: Mensaje de prueba {test_message.message_id} publicado en el topic '{test_message.recipient_id}'.")
        return {
            "status": "success",
            "message": "Mensaje de prueba enviado. Revisa los logs para ver la respuesta del servicio.",
            "message_id": test_message.message_id
        }
    except Exception as e:
        logger.error(f"API: Error al publicar mensaje de prueba: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al publicar el mensaje en el MessageBus.")

@app.post("/api/publish-message", tags=["Messaging"])
async def publish_message(payload: PublishMessagePayload, request: Request) -> Dict[str, str]:
    """
    Publica un mensaje genérico en el MessageBus de RayRabbit.
    Este endpoint permite a clientes externos enviar mensajes a cualquier agente o topic.
    """
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="La Infraestructura RayRabbit no está iniciada.")

    logger.info(f"API: Recibida solicitud para publicar mensaje a '{payload.recipient_id}'.")

    message = Message(
        sender_id=payload.sender_id,
        sender_name=payload.sender_name,
        recipient_id=payload.recipient_id,
        message_type=payload.message_type,
        correlation_id=payload.correlation_id if payload.correlation_id else str(uuid.uuid4()),
        content=payload.content
    )

    try:
        # --- VERIFICACIÓN DE SEGURIDAD CRIPTOGRÁFICA (HUB - OSS & ENTERPRISE) ---
        # Soporta dos modos:
        # 1. JWS (JSON Web Signature): Estándar moderno RFC 7515 (Preferido en OSS).
        # 2. X-RayRabbit-Signature: Legacy/Propietario. Firma raw del payload.
        
        jws_signature = request.headers.get("X-RayRabbit-JWS")
        signature_hex = request.headers.get("X-RayRabbit-Signature")
        
        sender_id = payload.sender_id
        
        # OSS: Resolución de Keystore vía RuntimeContext (Elimina acoplamiento PROJECT_ROOT)
        keystore_dir = RuntimeContext.get_keystore_dir()
        public_key_filename = f"{sender_id}_public.pem" 
        public_key_path = os.path.join(keystore_dir, public_key_filename)

        is_local = getattr(request.client, "host", "") in ["127.0.0.1", "localhost", "::1"]
        
        # --- NUEVO: Preservar JWS Universalmente (Requerido para renderizado A2UI) ---
        if jws_signature:
            if not message.metadata: message.metadata = {}
            message.metadata["jws"] = jws_signature

        if is_local:
            logger.info(f"SEGURIDAD: Política de Confianza Local (LTP) aplicada para agente '{sender_id}' (IP: {getattr(request.client, 'host', 'desconocido')}).")
        elif jws_signature:
            # --- MODO 1: JWS COMPACT SERIALIZATION (RFC 7515) ---
            try:
                import base64
                
                # JWS es: header.payload.signature (base64url encoded)
                parts = jws_signature.split('.')
                if len(parts) != 3:
                    raise ValueError("JWS debe tener 3 partes (header.payload.signature)")
                
                header_b64, payload_b64, signature_b64 = parts
                
                # Reconstruir el "signing input" (header.payload)
                signing_input = f"{header_b64}.{payload_b64}"
                
                # Decodificar la firma desde base64url
                # Añadir padding si es necesario (base64url puede omitir '=')
                signature_b64_padded = signature_b64 + '=' * (4 - len(signature_b64) % 4)
                signature_bytes = base64.urlsafe_b64decode(signature_b64_padded)
                
                # Cargar clave pública para verificar
                header_pub_key_pem = request.headers.get("X-RayRabbit-Bridge-Public-Key-PEM")
                
                public_key = None
                if os.path.exists(public_key_path):
                    with open(public_key_path, "rb") as key_file:
                        public_key = serialization.load_pem_public_key(key_file.read())
                    logger.debug(f"SEGURIDAD: Usando clave pública local para '{sender_id}'.")
                elif header_pub_key_pem:
                    try:
                        # Re-envolver en formato PEM si viene limpio
                        if "BEGIN PUBLIC KEY" not in header_pub_key_pem:
                            full_pem = f"-----BEGIN PUBLIC KEY-----\n{header_pub_key_pem}\n-----END PUBLIC KEY-----"
                        else:
                            full_pem = header_pub_key_pem
                        
                        public_key = serialization.load_pem_public_key(full_pem.encode('utf-8'))
                        logger.info(f"SEGURIDAD: Usando clave pública dinámica desde header para '{sender_id}'.")
                    except Exception as pe:
                        logger.error(f"SEGURIDAD: Error cargando clave pública del header: {pe}")

                if not public_key:
                    logger.error(f"SEGURIDAD: Recibido JWS de '{sender_id}' pero NO hay clave pública (local ni header).")
                    raise HTTPException(status_code=401, detail="Clave pública no encontrada para verificar JWS.")
                
                # Verificar firma JWS
                public_key.verify(
                    signature_bytes,
                    signing_input.encode('utf-8'),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                logger.info(f"SEGURIDAD: JWS Validado exitosamente para agente '{sender_id}'.")
                
                # JWS ya preservado arriba para LTP/Universal
                pass

            except ValueError as e:
                logger.error(f"SEGURIDAD: JWS mal formado: {e}")
                raise HTTPException(status_code=400, detail=f"JWS inválido: {e}")
            except InvalidSignature:
                logger.error(f"SEGURIDAD: Firma JWS inválida para '{sender_id}'.")
                raise HTTPException(status_code=403, detail="Firma JWS inválida.")
            except Exception as e:
                logger.error(f"SEGURIDAD: Error validando JWS: {e}")
                raise HTTPException(status_code=403, detail=f"Error validando JWS: {e}")

        elif signature_hex:
            # --- MODO 2: LEGACY SIGNATURE (Compatibilidad) ---
            try:
                if os.path.exists(public_key_path):
                    with open(public_key_path, "rb") as key_file:
                        public_key = serialization.load_pem_public_key(
                            key_file.read()
                        )
                    
                    # Reconstruir payload bytes
                    payload_dict = payload.dict()
                    payload_bytes = json.dumps(payload_dict, sort_keys=True).encode('utf-8')
                    signature = bytes.fromhex(signature_hex)
                    
                    # Verificar firma
                    public_key.verify(
                        signature,
                        payload_bytes,
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )
                    logger.info(f"SEGURIDAD: Firma digital (Legacy) VERIFICADA para agente '{sender_id}'.")
                    
                    # Preservar firma en metadatos para relay
                    if not message.metadata: message.metadata = {}
                    message.metadata["signature"] = signature_hex
                else:
                    logger.warning(f"SEGURIDAD: Recibida firma de '{sender_id}' pero no se encontró clave pública en {public_key_path}.")
            except InvalidSignature:
                logger.error(f"SEGURIDAD: Firma digital INVÁLIDA para agente '{payload.sender_id}'.")
                raise HTTPException(status_code=403, detail="Firma digital inválida perimetral.")
            except Exception as e:
                logger.error(f"SEGURIDAD: Error verificando firma: {e}")
        else:
            logger.error(f"SEGURIDAD: Rechazada petición de '{payload.sender_id}' sin credenciales JWS/Firma.")
            raise HTTPException(status_code=401, detail="Se requiere autenticación JWS o Firma Digital para publicar mensajes.")

        logger.info(f"API: Publicando mensaje de {message.sender_id} para {message.recipient_id} (Type: {message.message_type}, CorrID: {message.correlation_id})")
        await infrastructure.message_bus.publish(message)
        
        # Verificar si el destinatario está registrado
        if message.recipient_id in infrastructure.message_bus.agents:
            logger.info(f"API: Destinatario '{message.recipient_id}' confirmado en el MessageBus.")
        else:
            logger.warning(f"API: Destinatario '{message.recipient_id}' NO encontrado en los agentes del MessageBus.")

        logger.info(f"API: Mensaje {message.message_id} publicado en el topic '{message.recipient_id}'.")
        return {
            "status": "success",
            "message": "Mensaje publicado exitosamente.",
            "message_id": message.message_id,
            "correlation_id": message.correlation_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Error al publicar mensaje: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al publicar mensaje: {e}")

@app.post("/api/flush-audit-logs", tags=["Auditing"])
async def flush_audit_logs(request: Request) -> Dict[str, str]:
    """
    Fuerza al AuditManager a escribir todos los eventos pendientes a disco.
    Útil para scripts de prueba o para asegurar la persistencia inmediata de los logs.
    """
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="La Infraestructura RayRabbit no está iniciada.")
    
    logger.info("API: Recibida solicitud para forzar el vaciado de logs de auditoría.")
    await infrastructure.audit_manager.flush()
    logger.info("API: Logs de auditoría vaciados exitosamente.")
    return {"status": "success", "message": "Logs de auditoría vaciados exitosamente."}

@app.get("/api/mcp/tools", tags=["MCP"])
async def list_mcp_tools(request: Request) -> Dict[str, Any]:
    """Retorna la lista unificada de herramientas MCP registradas en la infraestructura."""
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        return {"tools": []}
        
    mcp_proto = getattr(infrastructure.message_bus, "mcp_protocol", None)
    if not mcp_proto:
        return {"tools": []}
        
    tools_list = []
    for tool_name, tool_data in mcp_proto.tools.items():
        schema = tool_data.get("schema", {})
        inp_schema = schema.get("inputSchema") or schema.get("input_schema") or schema.get("parameters") or (schema if "properties" in schema else {})
        tools_list.append({
            "name": tool_name,
            "agent_id": tool_data.get("agent_id", "hub"),
            "description": schema.get("description", ""),
            "category": schema.get("category") or tool_data.get("category", "general"),
            "input_schema": inp_schema,
            "inputSchema": inp_schema
        })
    return {"tools": tools_list}

@app.post("/api/mcp/tools/search", tags=["MCP"])
async def search_mcp_tools(payload: SearchToolsPayload, request: Request) -> Dict[str, Any]:
    """Descubre dinámicamente herramientas MCP desde el Hub usando BM25 server-side."""
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        return {"tools": []}
        
    mcp_proto = getattr(infrastructure.message_bus, "mcp_protocol", None)
    if not mcp_proto:
        return {"tools": []}
        
    tools_list = []
    for tool_name, tool_data in mcp_proto.tools.items():
        schema = tool_data.get("schema", {})
        inp_schema = schema.get("inputSchema") or schema.get("input_schema") or schema.get("parameters") or (schema if "properties" in schema else {})
        tools_list.append({
            "name": tool_name,
            "agent_id": tool_data.get("agent_id", "hub"),
            "description": schema.get("description", ""),
            "category": schema.get("category") or tool_data.get("category", "general"),
            "input_schema": inp_schema,
            "inputSchema": inp_schema
        })
        
    selected_info_list = match_top_k_tools(
        prompt=payload.query,
        tools_list=tools_list,
        top_k=payload.top_k,
        target_category=payload.target_category,
        target_tools=payload.target_tools,
        agent_role=payload.agent_role
    )
    return {"tools": selected_info_list}

@app.post("/api/execute-tool", tags=["MCP"])
async def execute_tool_endpoint(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """
    Ejecuta una herramienta MCP de forma síncrona mediante MessageBus.send_and_wait.
    Espera la respuesta del agente soberano registrador o proxy SDK antes de retornar.
    """
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="Infraestructura no disponible.")

    tool_name = payload.get("operation") or payload.get("name")
    params = payload.get("params") or payload.get("args") or {}
    recipient_id = payload.get("recipient_id")
    sender_id = payload.get("sender_id", "universal_a2ui_agent")

    task_id_in_payload = payload.get("_task_id") or (params.get("_task_id") if isinstance(params, dict) else None)
    correlation_id = payload.get("correlation_id")
    if not correlation_id and task_id_in_payload and hasattr(infrastructure, "task_manager") and infrastructure.task_manager:
        try:
            state = await infrastructure.task_manager.store.get_task_state(task_id_in_payload)
            if state and "task" in state:
                correlation_id = state["task"].get("correlation_id")
        except Exception:
            pass
    if not correlation_id:
        correlation_id = "default_dashboard"

    mcp_proto = getattr(infrastructure.message_bus, "mcp_protocol", None)
    if (not recipient_id or recipient_id == "hub") and mcp_proto and tool_name in mcp_proto.tools:
        recipient_id = mcp_proto.tools[tool_name].get("agent_id")

    # ── Short-circuit genérico para herramientas nativas del Hub (hub_native) ──────────────
    # Las herramientas con agent_id == "hub_native" tienen handlers directos en MCPProtocol.
    # NO se enrutan por el MessageBus (mcp_protocol no es un Agent registrado).
    # Resolución dinámica: getattr evita hardcodear nombres de herramientas (AGENTS.md rule).
    if recipient_id == "hub_native" and mcp_proto:
        native_handler = getattr(mcp_proto, f"_handle_{tool_name}", None)
        if native_handler and callable(native_handler):
            try:
                logger.info(f"HUB: Invocando handler nativo hub_native para herramienta '{tool_name}' directamente.")
                native_result = await native_handler(params)
                raw_res = str(native_result.get("result") if isinstance(native_result, dict) else native_result)
                persisted_res = maybe_persist_tool_result(raw_res, tool_name)
                return {"status": "success", "result": persisted_res, "sender_id": "hub_native", "correlation_id": correlation_id}
            except Exception as native_err:
                logger.error(f"HUB: Error en handler nativo '{tool_name}': {native_err}")
                return {"status": "error", "error": str(native_err), "correlation_id": correlation_id}
        else:
            logger.warning(f"HUB: Herramienta '{tool_name}' marcada como hub_native pero no tiene handler '_handle_{tool_name}' en MCPProtocol.")
            raise HTTPException(status_code=501, detail=f"Handler nativo no implementado para '{tool_name}'.")
    # ── Fin short-circuit hub_native ──────────────────────────────────────────────────────

    if not recipient_id or recipient_id == "hub":
        raise HTTPException(status_code=404, detail=f"No se encontró un agente registrador para la herramienta '{tool_name}'.")

    req_msg = Message(
        sender_id=sender_id,
        sender_name=sender_id,
        recipient_id=recipient_id,
        message_type=MessageType.REQUEST,
        content={"operation": tool_name, "params": params},
        correlation_id=correlation_id
    )

    # Determinar si la herramienta pertenece a la categoría cognitiva (larga duración)
    tool_category = ""
    if mcp_proto and tool_name in mcp_proto.tools:
        tool_meta = mcp_proto.tools[tool_name]
        schema = tool_meta.get("schema", {})
        tool_category = schema.get("category") or tool_meta.get("category", "")
        if not tool_category and isinstance(schema.get("inputSchema"), dict):
            tool_category = schema["inputSchema"].get("category", "")
        if not tool_category and isinstance(schema.get("input_schema"), dict):
            tool_category = schema["input_schema"].get("category", "")

    is_cognitive = tool_category in ("cognitive", "framework")

    # Canalización Asíncrona TaskEngine (MCP v2 Task Engine) según contrato OpenSpec
    if is_cognitive and hasattr(infrastructure, "task_manager") and infrastructure.task_manager:
        try:
            task_id = await infrastructure.task_manager.create_task(
                payload={
                    "type": "cognitive_task",
                    "tool_name": tool_name,
                    "recipient_id": recipient_id,
                    "params": params,
                    "sender_id": sender_id
                },
                correlation_id=correlation_id
            )
            
            # Inyectar _task_id para que el framework cognitivo sepa su identidad
            req_msg.content["_task_id"] = task_id

            async def _run_cognitive_task_bg():
                try:
                    logger.info(f"HUB TaskEngine BG: Iniciando ejecución asíncrona de '{tool_name}' para Task ID: {task_id}")
                    
                    # Nombre amigable del framework/nodo ejecutado
                    raw_framework = tool_name.replace("execute_", "").replace("start_", "").replace("run_", "")
                    raw_framework = raw_framework.replace("_task", "").replace("_chat", "").replace("_chain", "").upper()
                    framework_display = raw_framework if raw_framework else "COGNITIVO"
                    
                    # 1. Emisión inicial de avance por SSE (Fase 1: 33%)
                    await infrastructure.message_bus.publish(Message(
                        sender_id="task_manager",
                        sender_name="TaskManager",
                        recipient_id=sender_id,
                        message_type=MessageType.EVENT,
                        content={
                            "task_id": task_id,
                            "event_type": "task.progress",
                            "step": f"Paso 1/3: Despacho a {framework_display} — Ejecutando tarea en segundo plano...",
                            "progress": 33,
                            "payload": {"status": "running", "message": f"Iniciando {framework_display} ({tool_name})..."}
                        },
                        correlation_id=correlation_id
                    ))

                    # 2. Ejecución A2A del servicio cognitivo principal
                    resp_msg = await infrastructure.message_bus.send_and_wait(req_msg, timeout=300)
                    logger.info(f"HUB TaskEngine BG: Tarea '{tool_name}' ({task_id}) fase 1 completada exitosamente.")

                    # 3. Emisión de avance de fase intermedia por SSE (Fase 2: 66%)
                    await infrastructure.message_bus.publish(Message(
                        sender_id="task_manager",
                        sender_name="TaskManager",
                        recipient_id=sender_id,
                        message_type=MessageType.EVENT,
                        content={
                            "task_id": task_id,
                            "event_type": "task.progress",
                            "step": "Paso 2/3: Sincronización y persistencia en Memoria Soberana L3...",
                            "progress": 66,
                            "payload": {"status": "running", "message": "Sincronizando memoria declarativa L3..."}
                        },
                        correlation_id=correlation_id
                    ))

                    final_result = resp_msg.content
                    # Ahora el TaskEngine retorna la finalización y el Agente A2UI orquesta dinámicamente 
                    # el siguiente framework según el prompt y el evento de telemetría.

                    # 4. Guardar evento final y emitir task.completed (Fase 3: 100%)
                    await infrastructure.task_manager.store.save_task_event(
                        task_id=task_id,
                        tenant_id="default",
                        correlation_id=correlation_id,
                        parent_task_id=None,
                        status="completed",
                        event_type="task.completed",
                        step=f"Paso 3/3: {framework_display} completado exitosamente.",
                        payload={"result": final_result},
                        signature="",
                        nonce=str(uuid.uuid4()),
                        policy_decision="ALLOW",
                        hash_chain="",
                        checkpoint_ref=None
                    )
                    await infrastructure.message_bus.publish(Message(
                        sender_id="task_manager",
                        sender_name="TaskManager",
                        recipient_id=sender_id,
                        message_type=MessageType.EVENT,
                        content={
                            "task_id": task_id,
                            "event_type": "task.completed",
                            "step": f"Paso 3/3: {framework_display} completado exitosamente.",
                            "progress": 100,
                            "payload": {"status": "completed", "result": final_result}
                        },
                        correlation_id=correlation_id
                    ))
                except Exception as err:
                    logger.error(f"HUB TaskEngine BG: Error en tarea '{tool_name}' ({task_id}): {err}")
                    await infrastructure.task_manager.store.save_task_event(
                        task_id=task_id,
                        tenant_id="default",
                        correlation_id=correlation_id,
                        parent_task_id=None,
                        status="failed",
                        event_type="task.failed",
                        step="failed",
                        payload={"error": str(err)},
                        signature="",
                        nonce=str(uuid.uuid4()),
                        policy_decision="ALLOW",
                        hash_chain="",
                        checkpoint_ref=None
                    )

            asyncio.create_task(_run_cognitive_task_bg())

            logger.info(f"HUB: Tarea cognitiva '{tool_name}' canalizada a TaskEngine (Task ID: {task_id}). Retornando HTTP 202 Accepted en <10ms.")
            return {
                "status": "task_created",
                "task_id": task_id,
                "result": f"Tarea cognitiva '{tool_name}' iniciada asíncronamente en TaskEngine (Task ID: {task_id}).",
                "sender_id": recipient_id,
                "correlation_id": correlation_id
            }
        except Exception as task_err:
            logger.error(f"HUB: Error creando tarea en TaskEngine para '{tool_name}': {task_err}")

    # Determinar si la herramienta requiere aprobación (HITL)
    tool_requires_approval = False
    if mcp_proto and tool_name in mcp_proto.tools:
        tool_meta = mcp_proto.tools[tool_name]
        schema = tool_meta.get("schema", {})
        annotations = schema.get("annotations", {})
        tool_requires_approval = annotations.get("requires_approval", False)

    try:
        # Si la herramienta requiere aprobación humana (MCP annotations), pausar ANTES de enviar al Nodo
        if not is_cognitive and tool_requires_approval and hasattr(infrastructure, "task_manager") and infrastructure.task_manager:
            # Obtener task_id inyectado por servicio cognitivo, o crear uno ad-hoc
            approval_task_id = payload.get("params", {}).get("_task_id") or payload.get("_task_id")
            if not approval_task_id:
                approval_task_id = await infrastructure.task_manager.create_task(
                    payload={
                        "type": "hitl_approval",
                        "tool_name": tool_name,
                        "recipient_id": recipient_id,
                        "params": params,
                        "sender_id": sender_id
                    },
                    correlation_id=correlation_id
                )
                logger.info(f"HUB: Tarea ad-hoc {approval_task_id} creada para aprobación de '{tool_name}'.")

            params_clean = {k: v for k, v in params.items() if not k.startswith("_") and v is not None} if isinstance(params, dict) else params
            params_formatted = ", ".join(f"{k}={v}" for k, v in params_clean.items()) if isinstance(params_clean, dict) else str(params_clean)
            user_input = await infrastructure.task_manager.pause_for_approval(
                task_id=approval_task_id,
                step="waiting_human_approval",
                request_payload={
                    "question": f"⚠️ Autorización requerida: {tool_name}",
                    "details": f"Parámetros: {params_formatted or 'predeterminados'}",
                    "options": ["Aprobar", "Rechazar"],
                    "tool_name": tool_name,
                    "sender_id": sender_id,
                    "params": params
                },
                correlation_id=correlation_id
            )
            if user_input and str(user_input).lower() in ("rechazar", "reject", "denied"):
                logger.info(f"HUB: Usuario rechazó la ejecución de '{tool_name}' (Task {approval_task_id}).")
                return {"status": "rejected", "result": f"Ejecución de '{tool_name}' rechazada por el usuario.", "correlation_id": correlation_id}
            logger.info(f"HUB: Usuario aprobó la ejecución de '{tool_name}' (Task {approval_task_id}). Procediendo.")

        response_msg = await infrastructure.message_bus.send_and_wait(req_msg, timeout=120)
        raw_res = str(response_msg.content.get("result") if isinstance(response_msg.content, dict) else response_msg.content)
        persisted_res = maybe_persist_tool_result(raw_res, tool_name)
        return {
            "status": "success",
            "result": persisted_res,
            "sender_id": response_msg.sender_id,
            "correlation_id": correlation_id
        }
    except asyncio.TimeoutError:
        logger.error(f"API: Timeout esperando respuesta de '{recipient_id}' para la herramienta '{tool_name}'.")
        return {"status": "error", "error": f"Timeout esperando respuesta del agente '{recipient_id}'"}
    except Exception as e:
        logger.error(f"API: Error ejecutando herramienta síncrona '{tool_name}': {e}")
        return {"status": "error", "error": str(e)}

# --- ENDPOINTS REALTIME MCP SSE TRANSPORT (Anthropic MCP Standard / MCPv2) ---

_mcp_sse_sessions: Dict[str, asyncio.Queue] = {}

async def _broadcast_mcp_sse(event_data: Dict[str, Any], event_name: str = "message") -> None:
    """Envía un evento SSE a todas las sesiones activas."""
    payload_str = json.dumps(event_data, ensure_ascii=False)
    raw_event = f"event: {event_name}\ndata: {payload_str}\n\n"
    for session_id, queue in list(_mcp_sse_sessions.items()):
        try:
            queue.put_nowait(raw_event)
        except Exception as e:
            logger.debug(f"HUB SSE: Error enviando evento a sesión {session_id}: {e}")

@app.get("/api/mcp/sse", tags=["MCP"])
async def mcp_sse_endpoint(request: Request) -> StreamingResponse:
    """
    Endpoint Server-Sent Events (SSE) estándar de Anthropic MCP / MCPv2.
    Inicia un stream reactivo para clientes de codificación (Claude Code, Antigravity, Codex/Cursor).
    """
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _mcp_sse_sessions[session_id] = queue
    logger.info(f"HUB MCP SSE: Nueva sesión SSE iniciada (session_id={session_id}). Sesiones activas: {len(_mcp_sse_sessions)}")

    async def sse_event_generator():
        try:
            # Evento inicial obligatorio según la especificación Anthropic MCP SSE:
            # 'endpoint' con la ruta relativa donde el cliente enviará sus peticiones POST.
            yield f"event: endpoint\ndata: /api/mcp/messages?session_id={session_id}\n\n"
            
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield data
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat (comentario SSE)
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _mcp_sse_sessions.pop(session_id, None)
            logger.info(f"HUB MCP SSE: Sesión SSE finalizada (session_id={session_id}). Sesiones activas: {len(_mcp_sse_sessions)}")

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/mcp/messages", tags=["MCP"])
async def mcp_messages_endpoint(request: Request, session_id: Optional[str] = None) -> Any:
    """
    Endpoint de recepción de mensajes JSON-RPC 2.0 estándar de Anthropic MCP.
    Procesa métodos: initialize, notifications/initialized, ping, tools/list, tools/call.
    """
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="Infraestructura RayRabbit no iniciada.")

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cuerpo JSON inválido: {e}")

    reqs = [body] if isinstance(body, dict) else (body if isinstance(body, list) else [])
    responses = []

    mcp_proto = getattr(infrastructure.message_bus, "mcp_protocol", None)

    for req in reqs:
        if not isinstance(req, dict):
            continue
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # 1. initialize
        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": True}
                    },
                    "serverInfo": {
                        "name": "RayRabbit-L3-Hub",
                        "version": __version__
                    }
                }
            }
            responses.append(resp)

        # 2. notifications/initialized
        elif method == "notifications/initialized":
            logger.info(f"HUB MCP SSE: Cliente completó handshake 'notifications/initialized' (session_id={session_id})")
            continue

        # 3. ping
        elif method == "ping":
            responses.append({"jsonrpc": "2.0", "id": req_id, "result": {}})

        # 4. tools/list
        elif method == "tools/list":
            tools_list = []
            if mcp_proto:
                for tool_name, tool_data in mcp_proto.tools.items():
                    schema = tool_data.get("schema", {})
                    inp_schema = schema.get("inputSchema") or schema.get("input_schema") or schema.get("parameters") or (schema if "properties" in schema else {})
                    tools_list.append({
                        "name": tool_name,
                        "description": schema.get("description", f"Herramienta distribuida {tool_name}"),
                        "inputSchema": inp_schema
                    })
            responses.append({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": tools_list}
            })

        # 5. tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            try:
                exec_payload = {
                    "operation": tool_name,
                    "params": arguments,
                    "sender_id": f"mcp_client_{session_id[:8] if session_id else 'direct'}"
                }
                exec_result = await execute_tool_endpoint(exec_payload, request)
                res_content = exec_result.get("result", exec_result)
                text_out = json.dumps(res_content, ensure_ascii=False) if isinstance(res_content, (dict, list)) else str(res_content)
                responses.append({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": text_out}],
                        "isError": exec_result.get("status") == "error"
                    }
                })
            except Exception as call_err:
                logger.error(f"HUB MCP SSE: Error ejecutando tools/call '{tool_name}': {call_err}")
                responses.append({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error ejecutando herramienta '{tool_name}': {str(call_err)}"}],
                        "isError": True
                    }
                })

        # Desconocido
        else:
            if req_id is not None:
                responses.append({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Método no encontrado: '{method}'"}
                })

    # Si hay una sesión SSE activa, emitir cada respuesta también al stream SSE
    if session_id and session_id in _mcp_sse_sessions:
        q = _mcp_sse_sessions[session_id]
        for r in responses:
            try:
                q.put_nowait(f"event: message\ndata: {json.dumps(r, ensure_ascii=False)}\n\n")
            except Exception:
                pass

    if len(responses) == 1 and isinstance(body, dict):
        return responses[0]
    elif responses:
        return responses
    return {"status": "accepted"}

@app.post("/api/tasks/{task_id}/cancel", tags=["TaskEngine"])
async def cancel_task_endpoint(task_id: str, request: Request):
    """Cancela una tarea activa en el TaskEngine."""
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not hasattr(infrastructure, "task_manager") or not infrastructure.task_manager:
        raise HTTPException(status_code=503, detail="TaskEngine no disponible.")
    try:
        ok = await infrastructure.task_manager.cancel_task(task_id)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Tarea '{task_id}' no encontrada o ya finalizada.")
        return {"status": "success", "task_id": task_id, "action": "cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/{task_id}/resume", tags=["TaskEngine"])
async def resume_task_endpoint(task_id: str, payload: Dict[str, Any], request: Request):
    """Reanuda una tarea pausada (HITL) en el TaskEngine enviando el input del usuario."""
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not hasattr(infrastructure, "task_manager") or not infrastructure.task_manager:
        raise HTTPException(status_code=503, detail="TaskEngine no disponible.")
    user_input = payload.get("user_input") or payload.get("input") or payload
    try:
        ok = await infrastructure.task_manager.resume_task(task_id, user_input)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Tarea '{task_id}' no encontrada o no está en estado 'paused'.")
        return {"status": "success", "task_id": task_id, "action": "resumed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/{task_id}/pause", tags=["TaskEngine"])
async def pause_task_endpoint(task_id: str, payload: Dict[str, Any], request: Request):
    """Pausa una tarea activa en el TaskEngine esperando aprobación humana."""
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not hasattr(infrastructure, "task_manager") or not infrastructure.task_manager:
        raise HTTPException(status_code=503, detail="TaskEngine no disponible.")
    try:
        user_input = await infrastructure.task_manager.pause_for_approval(
            task_id=task_id,
            step="awaiting_human_decision",
            request_payload=payload
        )
        return {"status": "success", "task_id": task_id, "action": "resumed", "user_input": user_input}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/history", tags=["TaskEngine"])
async def get_tasks_history_endpoint(request: Request):
    """Retorna la lista de tareas activas e históricas para el dashboard A2UI y controles TaskEngine."""
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not hasattr(infrastructure, "task_manager") or not infrastructure.task_manager:
        return {"tasks": []}
    try:
        tasks = await infrastructure.task_manager.store.list_tasks(tenant_id="default")
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error listando tareas en /api/tasks/history: {e}")
        return {"tasks": []}

@app.get("/api/tasks/{task_id}", tags=["TaskEngine"])
async def get_task_status_endpoint(task_id: str, request: Request):
    """Recupera el estado persistido de una tarea en el TaskEngine."""
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not hasattr(infrastructure, "task_manager") or not infrastructure.task_manager:
        raise HTTPException(status_code=503, detail="TaskEngine no disponible.")
    state = await infrastructure.task_manager.get_task_status(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Tarea '{task_id}' no encontrada.")
    return state

# --- ENDPOINT A2UI: Stream de Eventos Soberanos (SSE) ---

@app.get("/api/a2ui/events/{agent_id}", tags=["A2UI"])
async def stream_a2ui_events(agent_id: str, request: Request):
    """
    Relay SSE para eventos A2UI. Se conecta a la cola de eventos del agente soberano
    y pulsa las actualizaciones (JWS signed) hacia el cliente web.
    """
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="Infraestructura RayRabbit no iniciada.")

    agent = infrastructure.message_bus.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agente {agent_id} no encontrado.")

    if not isinstance(agent, SovereignA2UIAgent):
        raise HTTPException(status_code=400, detail=f"El agente {agent_id} no es un Agente A2UI soberano.")

    logger.info(f"A2UI: Iniciando stream SSE para el cliente desde el agente '{agent_id}'.")
    
    return StreamingResponse(
        agent.stream_ui_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Para Nginx
        }
    )

@app.post("/api/a2ui/action", tags=["A2UI"])
async def a2ui_user_action(payload: A2UIUserActionPayload, request: Request):
    """
    Recibe una acción del usuario desde la UI web y la enruta al agente soberano
    correspondiente a través del MessageBus de RayRabbit.
    """
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="Infraestructura RayRabbit no iniciada.")

    logger.info(f"A2UI: Recibida acción '{payload.action.get('name')}' para el agente '{payload.agent_id}'.")

    # Enviar mensaje de tipo REQUEST al agente con la acción
    message = Message(
        sender_id="web_ui_bridge",
        sender_name="WebUI",
        recipient_id=payload.agent_id,
        message_type=MessageType.REQUEST,
        content={
            "action": "user_action",
            "surface_id": payload.surface_id,
            "data": payload.action
        }
    )

    try:
        await infrastructure.message_bus.publish(message)
        return {"status": "success", "message_id": message.message_id}
    except Exception as e:
        logger.error(f"A2UI: Error al publicar acción: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- NUEVOS ENDPOINTS DE IDENTIDAD SOBERANA (OSS) ---

@app.post("/api/security/register", tags=["Security"])
async def register_public_key(payload: RegisterPublicKeyPayload, request: Request) -> Dict[str, Any]:
    """
    Registra una clave pública para un agente. 
    OSS Handshake (PoP): Valida que el agente posea la llave privada firmando un reto.
    NUEVO: Handshake Bidireccional (envía PK del Hub al servicio).
    """
    import time
    import base64
    
    current_time = int(time.time())
    try:
        payload_time = int(payload.timestamp)
        # Validar frescura del timestamp (ventana de 5 minutos / 300s)
        if abs(current_time - payload_time) > 300:
            raise ValueError("El timestamp del registro ha expirado o es inválido (Anti-Replay).")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="Infraestructura no disponible.")

    # Obtener llave pública del Hub para el Handshake bidireccional
    hub_public_key_obj = infrastructure.framework_security.get_identity_key(KeyType.PUBLIC)

    keystore_dir = RuntimeContext.get_keystore_dir()
    key_path = keystore_dir / f"{payload.agent_id}_public.pem"
    
    try:
        # --- VERIFICACIÓN DE HANDSHAKE (PoP) ---
        # 1. Cargar la llave pública enviada para verificar la firma
        public_key = serialization.load_pem_public_key(payload.public_key_pem.encode('utf-8'))
        
        # 2. Reconstruir el reto (Exactamente igual que el agente)
        challenge = f"REG-AUTH:{payload.agent_id}:{payload.timestamp}"
        
        # 3. Verificar la firma
        signature_bytes = base64.b64decode(payload.signature)
        public_key.verify(
            signature_bytes,
            challenge.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Si llegamos aquí, la firma es válida y el agente posee la llave privada
        with open(key_path, "w") as f:
            f.write(payload.public_key_pem)
        
        logger.info(f"[SUCCESS] Identidad vinculada y verificada (Handshake OK) para: {payload.agent_id}")
        
        # NUEVO: Registro dinámico en el Beacon/Discovery del Hub (Federación Ad-hoc)
        if payload.p2p_endpoint:
             logger.info(f"HUB: Registrando ruteo dinámico para {payload.agent_id} -> {payload.p2p_endpoint}")
             from rayrabbit.protocols.a2a_router import AgentCard
             
             # Creamos una 'Ficha de Agente' (AgentCard) dinámica
             card = AgentCard(
                 agent_id=payload.agent_id,
                 name=payload.agent_id,
                 protocols=["a2a"], # El handshake básico asume A2A
                 endpoints={"a2a": payload.p2p_endpoint},
                 public_key_pem=payload.public_key_pem
             )
             
             # Registramos en el Router del Hub para habilitar el Relay (Fallback)
             if hasattr(infrastructure.message_bus, "a2a_protocol"):
                 await infrastructure.message_bus.a2a_protocol.router.register_agent(card)
                 logger.info(f"HUB: Agente {payload.agent_id} activado en el Router dinámico.")

             # Registro formal en el BUSINESS BUS (Hub local)
             # Esto habilita la resolución inmediata por el MessageBus sin ir al outbox/relay
             if payload.agent_id not in infrastructure.message_bus.agents:
                 # Creamos un ProxyAgent o simplemente registramos el ID para visibilidad
                 # En OSS, permitimos que el MessageBus vea al agente remoto como un peer válido
                 infrastructure.message_bus.agents[payload.agent_id] = None # Placeholder de agente externo
                 logger.info(f"HUB: Agente soberano '{payload.agent_id}' registrado formalmente en el Business Bus.")

             # Auto-descubrimiento asíncrono de herramientas MCP P2P
             asyncio.create_task(_discover_p2p_mcp_tools(payload.agent_id, payload.p2p_endpoint, infrastructure))

        # Obtener llave pública y privada del Hub para el Handshake bidireccional
        hub_public_key_pem = None
        hub_signature_b64 = None
        hub_ts = str(current_time)

        try:
            hub_public_key_obj = infrastructure.framework_security.get_identity_key(KeyType.PUBLIC)
            hub_private_key_obj = infrastructure.framework_security.get_identity_key(KeyType.PRIVATE)
            
            if hub_public_key_obj and hub_public_key_obj.key_data:
                hub_public_key_pem = hub_public_key_obj.key_data.decode('utf-8')
            
            if hub_private_key_obj and hub_private_key_obj.key_data:
                private_key = serialization.load_pem_private_key(
                    hub_private_key_obj.key_data,
                    password=None
                )
                hub_challenge = f"HUB-AUTH:{payload.agent_id}:{hub_ts}".encode('utf-8')
                sig_bytes = private_key.sign(
                    hub_challenge,
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256()
                )
                hub_signature_b64 = base64.b64encode(sig_bytes).decode('utf-8')
        except Exception as ex:
            logger.warning(f"HUB: No se pudo generar firma bidireccional del Hub: {ex}")

        return {
            "status": "success", 
            "message": f"Identidad registrada para {payload.agent_id}",
            "hub_public_key": hub_public_key_pem,
            "hub_signature": hub_signature_b64,
            "hub_timestamp": hub_ts
        }
        
    except InvalidSignature:
        logger.error(f"❌ Fallo de Handshake para {payload.agent_id}: Firma inválida.")
        raise HTTPException(status_code=403, detail="Fallo de Handshake: Firma RSA inválida.")
    except Exception as e:
        logger.error(f"Error registrando llave: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# === A2UI WebSocket Relay (Streaming Infrastructure) ===

class A2UIConnectionManager(Agent):
    """
    Gestiona conexiones WebSocket para el stream de UI A2UI.
    Actúa como un Agente de RayRabbit para poder suscribirse al MessageBus.
    """
    def __init__(self, agent_id: str = "a2ui_client"):
        super().__init__(agent_id, name="A2UI Relay Manager", description="Relay de mensajes A2UI hacia WebSockets")
        # correlation_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.infrastructure: Optional[Any] = None # Se inyecta en el setup

    async def connect(self, websocket: WebSocket, correlation_id: str):
        try:
            await websocket.accept()
            if correlation_id not in self.active_connections:
                self.active_connections[correlation_id] = []
            self.active_connections[correlation_id].append(websocket)
            logger.info(f"A2UI: [HANDSHAKE OK] Browser conectado al stream: {correlation_id}")
        except Exception as e:
            logger.error(f"A2UI: Fallo crítico al aceptar WebSocket {correlation_id}: {e}")
            raise e

    def disconnect(self, websocket: WebSocket, correlation_id: str):
        if correlation_id in self.active_connections:
            self.active_connections[correlation_id].remove(websocket)
            if not self.active_connections[correlation_id]:
                del self.active_connections[correlation_id]
        logger.info(f"A2UI: Cliente desconectado del stream {correlation_id}")

    async def receive_message(self, message: Message):
        """Relay agnóstico L3 desde el MessageBus hacia WebSockets activos.
        
        Reenvía cualquier mensaje a conexiones WebSocket cuyo correlation_id,
        recipient_id o surfaceId coincida con las suscripciones activas del cliente.
        """
        cid = message.correlation_id
        target_connections = set()
        
        # 1. Enrutamiento directo por Correlation ID (Estándar A2A)
        if cid and cid in self.active_connections:
            target_connections.update(self.active_connections[cid])
            
        # 2. Enrutamiento directo por Recipient ID (ej: ui_client, default_dashboard)
        if message.recipient_id and message.recipient_id in self.active_connections:
            target_connections.update(self.active_connections[message.recipient_id])
            
        # 3. Enrutamiento por Surface ID (Protocolos A2UI v0.9.1 / v0.10)
        if isinstance(message.content, dict):
            content = message.content
            target_surface = None
            if "surfaceUpdate" in content:
                target_surface = content["surfaceUpdate"].get("surfaceId")
            elif "updateDataModel" in content:
                target_surface = content["updateDataModel"].get("surfaceId")
            elif "beginRendering" in content:
                target_surface = content["beginRendering"].get("surfaceId")
                
            if target_surface and target_surface in self.active_connections:
                target_connections.update(self.active_connections[target_surface])

        # 4. Fallback para eventos de TaskEngine, HITL y Telemetría del Sistema hacia Dashboards activos
        if not target_connections:
            is_system_event = (
                message.sender_id in ("task_manager", "Task Worker") or
                message.recipient_id in ("a2ui_client", "default_dashboard", "*") or
                (isinstance(message.content, dict) and any(k in message.content for k in ("task_id", "event_type", "hitl_request", "step")))
            )
            if is_system_event or "default_dashboard" in self.active_connections:
                for c_id, conns in self.active_connections.items():
                    target_connections.update(conns)

        if not target_connections:
            return  # Nadie escuchando este flujo ni esta superficie

        relay_payload = {
            "a2ui": message.content,
            "jws": message.metadata.get("jws") if message.metadata else None,
            "sender_id": message.sender_id,
            "timestamp": message.timestamp.isoformat() if hasattr(message.timestamp, 'isoformat') else str(message.timestamp)
        }
        
        # Broadcast a todas las conexiones recolectadas (Surgical Loop)
        for connection in target_connections:
            try:
                await connection.send_json(relay_payload)
            except Exception as e:
                logger.error(f"A2UI: Error enviando a WS (Adv Relay): {e}")
                # Limpieza inmediata de conexión rota
                self.disconnect(connection, cid)

    async def broadcast(self, correlation_id: str, message: Any):
        if correlation_id in self.active_connections:
            for connection in self.active_connections[correlation_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"A2UI: Error enviando a WS {correlation_id}: {e}")
                    # Limpieza inmediata de conexión rota
                    self.disconnect(connection, correlation_id)

a2ui_manager = A2UIConnectionManager()

@app.websocket("/ws/a2ui/{correlation_id}")
async def a2ui_websocket_endpoint(websocket: WebSocket, correlation_id: str):
    """
    Endpoint WebSocket para recibir actualizaciones A2UI v0.10 en tiempo real.
    El cliente se suscribe a un flujo específico vía correlation_id.
    """
    await a2ui_manager.connect(websocket, correlation_id)
    infrastructure: RayRabbitFramework = app.state.infrastructure
    
    try:
        while True:
            # Verificación preventiva de estado de la conexión Starlette/FastAPI
            if websocket.client_state.value != 1: # 1 == CONNECTED
                logger.warning(f"A2UI: WebSocket {correlation_id} no está en estado CONNECTED. Abortando loop.")
                break

            # Esperar mensajes del cliente (User Input / Actions)
            data = await websocket.receive_text()
            try:
                action_payload = json.loads(data)
                logger.info(f"A2UI: Recibida acción desde WS para {correlation_id}")
                
                # Determinar el agente soberano objetivo (ej: universal_a2ui_agent en puerto 8006)
                target_agent_id = (
                    action_payload.get("agent_id")
                    or websocket.query_params.get("agent_id")
                    or "universal_a2ui_agent"
                )
                
                msg = Message(
                    sender_id="ui_client",
                    sender_name="WebUI",
                    recipient_id=target_agent_id,
                    message_type=MessageType.REQUEST,
                    content={"action": action_payload},
                    correlation_id=correlation_id
                )
                
                # Ruteo Inteligente: Preferir ruta P2P (A2A) si el agente está en el A2ARouter
                router = getattr(infrastructure.message_bus, "a2a_protocol", None)
                if router and hasattr(router, "router"):
                    await router.router.route_message(
                        sender_id="ui_client",
                        recipient_id=target_agent_id,
                        content={"action": action_payload},
                        message_type=MessageType.REQUEST,
                        correlation_id=correlation_id
                    )
                    logger.info(f"A2UI: Acción ruteada vía A2A a '{target_agent_id}' (Stream: {correlation_id})")
                else:
                    await infrastructure.message_bus.publish(msg)
                    logger.info(f"A2UI: Acción publicada al MessageBus (Fallback)")

            except json.JSONDecodeError:
                logger.error("A2UI: Error decodificando acción JSON de WS")
            except Exception as e:
                logger.error(f"A2UI: Error procesando acción de WS: {e}")
                
    except WebSocketDisconnect:
        a2ui_manager.disconnect(websocket, correlation_id)

# === WebSocket Ingress for Sovereign SDK Nodes (ws://127.0.0.1:8005/ws) ===

class SovereignWebSocketProxy(Agent):
    """
    Proxy dinámico en el Hub para Nodos SDK soberanos conectados vía WebSocket persistente.
    Registra sus herramientas MCP en la infraestructura L3 y reenvía solicitudes 'tools/call'.
    """
    def __init__(self, agent_id: str, websocket: WebSocket, tools: List[Dict[str, Any]], infrastructure: Any):
        super().__init__(agent_id, name=f"SovereignWebSocketProxy({agent_id})", description=f"WebSocket Proxy para {agent_id}")
        self.websocket = websocket
        self.tools = tools
        self.infrastructure = infrastructure
        self.pending_calls: Dict[int, asyncio.Future] = {}
        self.call_counter = 0

    async def receive_message(self, message: Message) -> None:
        """
        Intercepta mensajes del MessageBus dirigidos a este agente soberano WebSocket
        y reenvía la llamada a la herramienta remota vía JSON-RPC sobre la conexión WebSocket.
        """
        self.metrics["messages_received"] += 1
        if isinstance(message.content, dict) and message.content.get("operation"):
            tool_name = message.content["operation"]
            tool_args = message.content.get("params", {})
            try:
                result = await self.call_remote_tool(tool_name, tool_args)
                response_msg = Message(
                    sender_id=self.id,
                    sender_name=self.name,
                    recipient_id=message.sender_id,
                    message_type=MessageType.RESPONSE,
                    content=result,
                    correlation_id=message.message_id
                )
                await self.infrastructure.message_bus.publish(response_msg)
            except Exception as e:
                logger.error(f"HUB: Error ejecutando herramienta remota {tool_name} en {self.id}: {e}")
                error_msg = Message(
                    sender_id=self.id,
                    sender_name=self.name,
                    recipient_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    content={"error": str(e)},
                    correlation_id=message.message_id
                )
                await self.infrastructure.message_bus.publish(error_msg)

    async def call_remote_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        self.call_counter += 1
        req_id = self.call_counter
        future: asyncio.Future = asyncio.Future()
        self.pending_calls[req_id] = future
        
        rpc_req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        await self.websocket.send_text(json.dumps(rpc_req))
        
        try:
            return await asyncio.wait_for(future, timeout=300.0)
        except Exception as e:
            if req_id in self.pending_calls:
                self.pending_calls.pop(req_id)
            raise e

    def handle_rpc_response(self, response_data: Dict[str, Any]):
        req_id = response_data.get("id")
        if req_id in self.pending_calls:
            future = self.pending_calls.pop(req_id)
            if "result" in response_data:
                result = response_data["result"]
                if isinstance(result, dict) and "content" in result:
                    content_list = result["content"]
                    if content_list and content_list[0].get("type") == "json":
                        future.set_result(content_list[0].get("json"))
                    else:
                        future.set_result(result)
                else:
                    future.set_result(result)
            elif "error" in response_data:
                future.set_exception(RuntimeError(response_data["error"].get("message", "Remote tool execution error")))


@app.websocket("/ws")
async def sdk_node_websocket_ingress(websocket: WebSocket):
    """
    Endpoint Ingress WebSocket para Nodos SDK Soberanos (ws://127.0.0.1:8005/ws).
    """
    await websocket.accept()
    infrastructure: RayRabbitFramework = app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        await websocket.close(code=1011, reason="Hub not ready")
        return

    proxy = None
    try:
        init_raw = await websocket.receive_text()
        init_data = json.loads(init_raw)
        
        agent_id = init_data.get("agent_id") or f"node_{uuid.uuid4().hex[:8]}"
        tools = init_data.get("tools", [])
        
        proxy = SovereignWebSocketProxy(agent_id=agent_id, websocket=websocket, tools=tools, infrastructure=infrastructure)
        await infrastructure.register_agent(proxy)
        
        mcp_proto = getattr(infrastructure.message_bus, "mcp_protocol", None)
        if mcp_proto:
            for tool_spec in tools:
                tool_name = tool_spec.get("name")
                if tool_name:
                    mcp_proto.register_tool(
                        tool_name=tool_name,
                        agent_id=agent_id,
                        schema=tool_spec
                    )
                    logger.info(f"HUB: Herramienta MCP '{tool_name}' registrada para el agente '{agent_id}'.")
                    
        a2a_proto = getattr(infrastructure.message_bus, "a2a_protocol", None)
        if a2a_proto and hasattr(a2a_proto, "router"):
            from rayrabbit.protocols.a2a_router import AgentCard
            card = AgentCard(
                agent_id=agent_id,
                name=agent_id,
                capabilities=[t.get("name") for t in tools if isinstance(t, dict) and t.get("name")],
                endpoints={"ws": f"ws://{agent_id}"}
            )
            await a2a_proto.router.register_agent(card)
        
        await websocket.send_json({"status": "registered", "agent_id": agent_id})
        logger.info(f"HUB: Agente SDK WebSocket '{agent_id}' registrado y activo.")

        while True:
            msg_raw = await websocket.receive_text()
            try:
                msg_data = json.loads(msg_raw)
                proxy.handle_rpc_response(msg_data)
            except json.JSONDecodeError:
                logger.error(f"HUB: Trama JSON inválida recibida de {agent_id}")

    except WebSocketDisconnect:
        logger.info(f"HUB: Nodo SDK WebSocket '{proxy.id if proxy else 'unknown'}' desconectado.")
    except Exception as e:
        logger.error(f"HUB: Error en Ingress WebSocket de Nodo SDK: {e}")
    finally:
        if proxy and infrastructure and hasattr(infrastructure, "message_bus"):
            infrastructure.message_bus.agents.pop(proxy.id, None)

# --- Listener del MessageBus para Relay A2UI ---

async def setup_a2ui_relay(infrastructure: RayRabbitFramework):
    """Registra el a2ui_manager como agente interno del Hub para el relay WebSocket."""
    # 1. Inyectar referencia a la infraestructura para ruteo A2A
    a2ui_manager.infrastructure = infrastructure
    
    # 2. Registrar en el framework y suscribir
    await infrastructure.register_agent(a2ui_manager)
    infrastructure.message_bus.subscribe("*", a2ui_manager.id)
    
    # 3. Registrar alias para 'ui_client' y 'default_dashboard' apuntando a a2ui_manager
    # para que respuestas A2A destinadas a 'ui_client' se entreguen directamente al Relay Manager.
    infrastructure.message_bus.agents["ui_client"] = a2ui_manager
    infrastructure.message_bus.agents["default_dashboard"] = a2ui_manager
    
    logger.info(f"A2UI: Relay Gateway '{a2ui_manager.id}' registrado y activo para ruteo dinámico.")

@app.post("/api/execute-project", tags=["Orchestration"])
async def execute_project(user_query: UserQuery, request: Request) -> Any:
    """
    Ejecuta la lógica de un proyecto, inyectando la infraestructura core.
    """
    infrastructure: RayRabbitFramework = request.app.state.infrastructure
    if not infrastructure or not infrastructure.is_running:
        raise HTTPException(status_code=503, detail="La Infraestructura RayRabbit no está iniciada.")

# === Endpoints de Autenticación ===

@app.get("/auth/{project_name}/login", tags=["Authentication"])
async def auth_login(project_name: str) -> RedirectResponse:
    """Inicia el flujo de autenticación OAuth 2.0 para un proyecto."""
    try:
        project_instance = project_factory(project_name)
        if not hasattr(project_instance, 'auth_manager') or not project_instance.auth_manager:
            raise HTTPException(status_code=404, detail=f"El proyecto '{project_name}' no soporta autenticación.")
        
        auth_url = await project_instance.auth_manager.get_authorization_url()
        return RedirectResponse(url=auth_url)
    except ProjectNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/auth/{project_name}/callback", tags=["Authentication"])
async def auth_callback(project_name: str, request: Request) -> Dict[str, str]:
    """Maneja la devolución de llamada (callback) del proveedor de OAuth."""
    try:
        project_instance = project_factory(project_name)
        if not hasattr(project_instance, 'auth_manager') or not project_instance.auth_manager:
            raise HTTPException(status_code=404, detail=f"El proyecto '{project_name}' no soporta autenticación.")

        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state:
            raise HTTPException(status_code=400, detail="Faltan los parámetros 'code' o 'state' en la devolución de llamada.")

        await project_instance.auth_manager.fetch_token_from_callback(code, state)
        return {"status": "success", "message": "Autenticación completada."}
    except ProjectNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))