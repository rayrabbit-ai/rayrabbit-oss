import os
import asyncio
from dotenv import load_dotenv
import json
import logging
import sys
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from fastapi import FastAPI, HTTPException, Request, Body
from pydantic import BaseModel, Field
import uvicorn
import httpx
from pathlib import Path
import inspect

# --- Inyección de Soberanía Local (OSS: 100% Desacoplado) ---
service_dir = Path(__file__).parent.resolve()
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from sovereign import RuntimeContext, SovereignIdentity

# --- Inicialización del Servicio ---
AGENT_ID = "autogen_service"
runtime_context = RuntimeContext()

# Configuración del Logger
logger = logging.getLogger("autogen_service")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')

LOG_DIR = runtime_context.get_agent_data_path(AGENT_ID, "audit_logs")
os.makedirs(LOG_DIR, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "autogen_service_internal.log"), encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

DOTENV_PATH = runtime_context.resolve_env_path(".env")
load_dotenv(DOTENV_PATH)
logger.info(f"Cargando .env desde: {DOTENV_PATH}")

# --- Protocolos Locales (Agnósticos) ---
from protocols import (
    JSONRPCRequest, JSONRPCResponse, MCPTool,
    MCPToolsListResponse, MCPToolCallRequest, MCPResponse
)

# --- Dependencias de AutoGen v0.10+ ---
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination, TimeoutTermination
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from autogen_core.models import ModelInfo
    AUTOGEN_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error de dependencias AutoGen: {e}")
    AUTOGEN_AVAILABLE = False

# --- Utilidades de Mensajería y Transporte Declarativo ---
class MessageType(Enum):
    request = "request"
    response = "response"
    event = "event"

class Message:
    def __init__(self, sender_id: str, sender_name: str, recipient_id: str, message_type: Any, content: Dict[str, Any], correlation_id: str = None, timestamp: str = None):
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.recipient_id = recipient_id
        if isinstance(message_type, str):
            try:
                self.message_type = MessageType[message_type.lower()]
            except (KeyError, ValueError):
                self.message_type = MessageType.event
        else:
            self.message_type = message_type
        self.content = content
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self):
        return {
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp
        }

class HTTPClientTransport:
    """Implementación agnóstica de transporte sin dependencias de RayRabbit."""
    def __init__(self):
        self.client = httpx.AsyncClient()

    async def start(self):
        self.client = httpx.AsyncClient()

    async def stop(self):
        if self.client:
            await self.client.aclose()

    async def send(self, message: Message, endpoint: str, headers: Optional[Dict[str, str]] = None) -> bool:
        if not self.client:
            raise RuntimeError("Transporte no iniciado.")
        try:
            resp = await self.client.post(endpoint, json=message.to_dict(), headers=headers or {})
            return resp.status_code in [200, 202, 204]
        except Exception:
            return False

_rr_api_url = os.getenv("RAYRABBIT_API_URL")
if not _rr_api_url:
    _rr_api_url = "http://127.0.0.1:8005"
RAYRABBIT_API_URL = _rr_api_url
MESSAGE_BUS_ENDPOINT = f"{RAYRABBIT_API_URL}/api/publish-message"

class InvokeRequest(BaseModel):
    operation: str = "run_autogen_chat"
    actions: Optional[List[Dict[str, Any]]] = None
    callback_topic: Optional[str] = "autogen_update_listener"
    package_id: Optional[str] = None
    prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    correlation_id: Optional[str] = None

class InvokeResponse(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

# --- Utilidades de Seguridad Integradas ---
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64

class LocalJWSManager:
    """Gestor de JWS para el agente soberano (OSS)."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.identity = SovereignIdentity(agent_id)
        self.identity.ensure_identity()
        self.private_key_path = self.identity.private_key_path
        self.public_key_path = self.identity.public_key_path
        
        with open(self.private_key_path, "rb") as key_file:
            self.private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
        with open(self.public_key_path, "r") as key_file:
            self.public_key_pem = key_file.read()
    
    def _b64url(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    def sign_message(self, message: Dict[str, Any]) -> str:
        header = {"alg": "RS256", "typ": "JWS"}
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

    def get_public_key_pem(self) -> str:
        pem = self.public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        return pem.replace('\n', '').replace('-----BEGIN PUBLIC KEY-----', '').replace('-----END PUBLIC KEY-----', '').strip()

    def get_jws_headers(self, message: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "X-RayRabbit-JWS": self.sign_message(message),
            "X-RayRabbit-Agent-ID": self.agent_id,
            "X-RayRabbit-Bridge-Public-Key-PEM": self.get_public_key_pem()
        }
        if correlation_id:
            headers["X-RayRabbit-Correlation-ID"] = correlation_id
        return headers

jws_manager = LocalJWSManager(AGENT_ID)

async def verify_signature(request: Request, payload_dict: Dict[str, Any]):
    sender_id = request.headers.get("X-RayRabbit-Agent-ID")
    jws_signature = request.headers.get("X-RayRabbit-JWS")
    header_pub_key_pem = request.headers.get("X-RayRabbit-Bridge-Public-Key-PEM")
    cid = request.headers.get("X-RayRabbit-Correlation-ID")
    
    if not jws_signature:
        logger.error(f"Acceso denegado de '{sender_id}': JWS ausente.")
        raise HTTPException(status_code=401, detail="Se requiere JWS.")

    try:
        public_key = None
        if header_pub_key_pem:
            clean_key = header_pub_key_pem.replace('\r', '').replace('\n', '')
            pem_data = f"-----BEGIN PUBLIC KEY-----\n{clean_key}\n-----END PUBLIC KEY-----"
            public_key = serialization.load_pem_public_key(pem_data.encode('utf-8'))
        
        if not public_key:
             raise RuntimeError("No se pudo obtener la clave pública dinámica.")

        parts = jws_signature.split('.')
        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature_bytes = base64.urlsafe_b64decode(signature_b64 + '=' * (4 - len(signature_b64) % 4))

        public_key.verify(
            signature_bytes,
            signing_input,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        logger.info(f"✅ JWS Verificado en AutoGen (CID: {cid}): {sender_id}")
        return cid
        
    except Exception as e:
        logger.error(f"❌ FALLO DE SEGURIDAD en AutoGen: {e}")
        raise HTTPException(status_code=403, detail=f"Firma JWS inválida: {str(e)}")


def _create_autogen_tool(t_name: str, t_desc: str, input_schema: Dict[str, Any], hub_url: str, task_id: Optional[str] = None):
    """Fábrica dinámica de herramientas FunctionTool para AutoGen con firma tipada explícita."""
    properties = input_schema.get("properties", {}) if isinstance(input_schema, dict) else {}
    required_fields = set(input_schema.get("required", [])) if isinstance(input_schema, dict) else set()
    props_keys = list(properties.keys()) if properties else []

    async def dynamic_hub_tool(**kwargs) -> str:
        try:
            payload = {"name": t_name, "params": kwargs, "sender_id": "autogen_service"}
            if task_id:
                payload["_task_id"] = task_id
                kwargs["_task_id"] = task_id
                
            async with httpx.AsyncClient(timeout=600.0) as c:
                r = await c.post(
                    f"{hub_url}/api/execute-tool",
                    json=payload
                )
                if r.status_code == 200:
                    res_data = r.json()
                    return str(res_data.get("result") or res_data)
                return f"Error HTTP {r.status_code}: {r.text}"
        except Exception as ex:
            return f"Error ejecutando herramienta {t_name}: {ex}"

    dynamic_hub_tool.__name__ = t_name
    dynamic_hub_tool.__doc__ = t_desc

    if props_keys:
        type_mapping = {
            "string": str, "integer": int, "number": float, "boolean": bool, "array": list, "object": Union[dict, str, Any]
        }
        annotations = {}
        params = []
        # Ordenar: Parámetros requeridos primero, opcionales después para evitar ValueError en Signature
        sorted_keys = [k for k in props_keys if k in required_fields] + [k for k in props_keys if k not in required_fields]
        for pk in sorted_keys:
            p_info = properties.get(pk, {}) if isinstance(properties.get(pk), dict) else {}
            p_type_str = p_info.get("type", "string")
            if p_type_str in ("object", "any") or p_type_str not in type_mapping:
                py_type = Union[dict, str, Any]
            else:
                py_type = type_mapping.get(p_type_str, Any)
            annotations[pk] = py_type
            is_req = pk in required_fields
            default_val = inspect.Parameter.empty if is_req else None
            params.append(inspect.Parameter(pk, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=default_val, annotation=py_type))

        annotations["return"] = str
        dynamic_hub_tool.__annotations__ = annotations
        dynamic_hub_tool.__signature__ = inspect.Signature(params, return_annotation=str)
    else:
        dynamic_hub_tool.__annotations__ = {"return": str}
        dynamic_hub_tool.__signature__ = inspect.Signature([], return_annotation=str)

    try:
        from autogen_core.tools import FunctionTool
        return FunctionTool(dynamic_hub_tool, description=t_desc, name=t_name)
    except Exception:
        return dynamic_hub_tool

async def _fetch_hub_mcp_tools(prompt: str = "", target_category: Optional[str] = None, target_tools: Optional[str] = None, task_id: Optional[str] = None) -> List[Any]:
    """Descubre e inscribe dinámicamente herramientas MCP desde el Hub usando BM25."""
    hub_url = os.getenv("RAYRABBIT_API_URL")
    if not hub_url:
        logger.warning("⚠️  RAYRABBIT_API_URL no definida. Usando fallback local http://127.0.0.1:8005")
        hub_url = "http://127.0.0.1:8005"
    mcp_tools_url = f"{hub_url}/api/mcp/tools"
    discovered_tools: List[Any] = []

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{mcp_tools_url}/search", 
                json={"query": prompt, "top_k": 3, "target_category": target_category, "target_tools": target_tools, "agent_role": "cognitive_framework"}
            )
            if resp.status_code == 200:
                data = resp.json()
                selected_info_list = data.get("tools", [])

                for t_info in selected_info_list:
                    tool_name = t_info.get("name")
                    category = t_info.get("category", "")
                    tool_description = f"{t_info.get('description', '')} [Category: {category}]"
                    input_schema = t_info.get("input_schema", {})

                    tool_fn = _create_autogen_tool(tool_name, tool_description, input_schema, hub_url, task_id)
                    discovered_tools.append(tool_fn)
                    logger.info(f"AutoGen: Herramienta '{tool_name}' ({category}) vinculada dinámicamente desde metadata MCP.")
    except Exception as e:
        logger.warning(f"AutoGen: No se pudieron auto-descubrir herramientas MCP en el Hub: {e}")
        
    return discovered_tools

def _get_autogen_model_client() -> Any:
    """Instancia dinámicamente un cliente de modelo agnóstico para AutoGen (Soporta TODOS los proveedores y modelos)."""
    full_model_name = os.getenv("LLM_MODEL_FULL_NAME", "")
    provider = os.getenv("LLM_PROVIDER", "").lower()
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL") or os.getenv("NVIDIA_NIM_BASE_URL")
    api_key = (
        os.getenv("LLM_API_KEY") 
        or os.getenv("NVIDIA_NIM_API_KEY") 
        or os.getenv("GOOGLE_API_KEY") 
        or os.getenv("GEMINI_API_KEY") 
        or os.getenv("OPENAI_API_KEY") 
        or "sk-dummy"
    )

    # Resolución agnóstica de modelo
    if full_model_name:
        raw_model = full_model_name
    elif provider == "ollama":
        raw_model = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
        base_url = base_url or "http://127.0.0.1:11434/v1"
    elif provider in ("google", "gemini"):
        raw_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        base_url = base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
    else:
        raw_model = "meta/llama-3.1-8b-instruct"

    # Normalización del nombre del modelo para APIs compatibles con OpenAI
    model_name = raw_model
    if model_name.startswith("openai/"):
        model_name = model_name[len("openai/"):]
    elif model_name.startswith("openrouter/"):
        model_name = model_name[len("openrouter/"):]
        if not base_url or "nvidia" in base_url:
            base_url = "https://openrouter.ai/api/v1"
    elif model_name.startswith("gemini/") or model_name.startswith("google/"):
        if not base_url:
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # Intentar GoogleGenAIChatCompletionClient si está disponible y es nativo de Gemini sin proxy
    if ("gemini" in raw_model.lower() or provider in ("google", "gemini")) and not base_url:
        try:
            from autogen_ext.models.gemini import GoogleGenAIChatCompletionClient
            clean_gemini_model = raw_model.replace("gemini/", "").replace("google/", "")
            return GoogleGenAIChatCompletionClient(
                model=clean_gemini_model,
                api_key=api_key
            )
        except Exception:
            pass

    # Universal OpenAIChatCompletionClient (Agnóstico: OpenAI, OpenRouter, Nvidia NIM, Ollama, Groq, DeepSeek)
    client_kwargs = {
        "model": model_name,
        "api_key": api_key,
        "model_info": ModelInfo(
            vision=False,
            function_calling=True,
            json_output=False,
            family="unknown",
            structured_output=False
        )
    }
    if base_url:
        client_kwargs["base_url"] = base_url

    return OpenAIChatCompletionClient(**client_kwargs)

# --- Lógica Core AutoGen (100% Agnóstica de Dominio) ---
async def run_autogen_logic(user_prompt: str, package_id: Optional[str] = None, target_category: Optional[str] = None, target_tools: Optional[str] = None, task_id: Optional[str] = None) -> str:
    """Ejecuta razonamiento agéntico multi-agente en AutoGen de forma 100% agnóstica."""
    if not AUTOGEN_AVAILABLE:
        return "Error: AutoGen v0.10 no está disponible en este entorno."

    # Auto-descubrir herramientas MCP de dominio/memoria desde el Hub usando BM25
    autogen_tools = await _fetch_hub_mcp_tools(prompt=user_prompt, target_category=target_category, target_tools=target_tools, task_id=task_id)

    try:
        client = _get_autogen_model_client()
        logger.info(f"🚀 [SOVEREIGN AUTOGEN] Ejecutando conversación agnóstica con {client}")

        analyst = AssistantAgent(
            name="Analista_Cognitivo",
            model_client=client,
            tools=autogen_tools if autogen_tools else None,
            system_message=(
                "Eres un agente analista de RayRabbit. Analiza la consulta recibida, "
                "utiliza las herramientas MCP disponibles para consultar la memoria o los datos de dominio y resolver la tarea, "
                "y proporciona una respuesta clara y directa. "
                "Al finalizar tu respuesta escribe OBLIGATORIAMENTE la palabra TERMINATE."
            )
        )
        
        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages=4) | TimeoutTermination(timeout_seconds=75)
        agent_team = RoundRobinGroupChat([analyst], termination_condition=termination)
        
        task_text = user_prompt
        if package_id:
            task_text = f"[Contexto/ID: {package_id}] {user_prompt}"

        result = await agent_team.run(task=task_text)
        
        if result and result.messages:
            for msg in reversed(result.messages):
                if msg.content and "TERMINATE" not in str(msg.content):
                    return str(msg.content).strip()
            return str(result.messages[-1].content).replace("TERMINATE", "").strip()
            
        return "Conversación completada por AutoGen Team."
    except Exception as e:
        logger.error(f"Error Agéntico en AutoGen: {e}")
        return f"Error: {e}"

# --- Adaptador Universal de AutoGen (Generic Bridge Agnóstico) ---
class UniversalAutoGenBridge:
    def __init__(self):
        self.mcp_schemas: List[MCPTool] = [
            MCPTool(
                name="start_autogen_chat",
                description="Ejecuta conversación agéntica multi-agente en AutoGen v0.10+ de forma totalmente agnóstica.",
                category="cognitive",
                inputSchema={
                    "type": "object",
                    "category": "cognitive",
                    "properties": {
                        "user_prompt": {"type": "string", "description": "Prompt o tarea inicial para el equipo AutoGen"},
                        "package_id": {"type": "string", "description": "ID opcional del objeto o contexto sobre el que razonar"},
                        "target_category": {"type": "string", "description": "Categoría de dominio opcional o lista separada por comas"},
                        "target_tools": {"type": "string", "description": "Nombres de herramientas específicos opcionales separados por comas"}
                    },
                    "required": ["user_prompt"]
                }
            )
        ]
        logger.info("[Bridge] Herramienta AutoGen agnóstica registrada: start_autogen_chat")

    async def invoke_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if name == "start_autogen_chat":
            args_copy = dict(arguments)
            args_copy.pop("_correlation_id", None)
            user_prompt = args_copy.get("user_prompt", "")
            pkg_id = args_copy.get("package_id")
            target_cat = args_copy.get("target_category")
            target_tls = args_copy.get("target_tools")
            return await run_autogen_logic(user_prompt, package_id=pkg_id, target_category=target_cat, target_tools=target_tls)
        else:
            raise ValueError(f"Tool '{name}' no encontrada en el registro de AutoGen.")

universal_bridge = UniversalAutoGenBridge()

# --- Aplicación FastAPI ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    hub_url = os.getenv("RAYRABBIT_API_URL")
    if not hub_url:
        logger.warning("⚠️  RAYRABBIT_API_URL no definida. Usando fallback local http://127.0.0.1:8005")
        hub_url = "http://127.0.0.1:8005"

    _self_host = os.getenv("RAYRABBIT_P2P_HOST", "http://127.0.0.1:8003")
    p2p_endpoint = f"{_self_host}/a2a"
    openapi_url = f"{_self_host}/openapi.json"

    asyncio.create_task(jws_manager.identity.register_with_backoff(
        hub_url,
        p2p_endpoint=p2p_endpoint,
        openapi_url=openapi_url
    ))
    logger.info(f"🚀 AutoGen Service '{AGENT_ID}' iniciado y federado. P2P: {p2p_endpoint}")
    yield

app = FastAPI(
    title="RayRabbit External AutoGen Service",
    description="Servicio cognitivo agnóstico de AutoGen v0.10+ para conversación multi-agente.",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "AutoGen Service Agnóstico"}

@app.post("/invoke", operation_id="run_autogen_chat", response_model=InvokeResponse)
async def invoke(request: Request, payload: Dict[str, Any] = Body(...)):
    """Endpoint declarativo OpenAPI para DeclarativeBridge (Vía A)."""
    cid_from_header = await verify_signature(request, payload)
    
    correlation_id = cid_from_header or payload.get("correlation_id") or str(uuid.uuid4())
    
    actions = payload.get("actions", [])
    callback_topic = payload.get("callback_topic") or "autogen_update_listener"
    
    # Extraer package_id y prompt
    pkg_id = payload.get("package_id")
    if not pkg_id and actions and isinstance(actions, list):
        pkg_id = actions[0].get("package_id")
    
    prompt = payload.get("prompt") or payload.get("user_prompt") or f"Ejecutar acciones de campo en AutoGen para paquete {pkg_id or 'N/A'}"
    
    logger.info(f"🚀 [AUTOGEN INVOKE] Procesando chat '{prompt}' para paquete '{pkg_id}' (CID: {correlation_id})")
    
    # 1. Ejecutar conversación multi-agente
    autogen_output = await run_autogen_logic(
        user_prompt=prompt,
        package_id=pkg_id
    )
    
    # 2. Publicar evento/respuesta al MessageBus para downstream listeners (Modo Bridge)
    update_payload = {
        "sender_id": AGENT_ID,
        "sender_name": "AutoGen Service",
        "recipient_id": callback_topic,
        "message_type": "event",
        "content": {
            "status": "completed",
            "detail": {
                "final_summary": autogen_output,
                "package_id": pkg_id,
                "message": autogen_output
            }
        },
        "correlation_id": correlation_id
    }
    
    transport = HTTPClientTransport()
    await transport.start()
    try:
        headers = jws_manager.get_jws_headers(update_payload, correlation_id=correlation_id)
        success = await transport.send(Message(**update_payload), MESSAGE_BUS_ENDPOINT, headers=headers)
        if success:
            logger.info(f"✅ [{correlation_id}] Evento publicado exitosamente al Hub: {update_payload['recipient_id']}")
        else:
            logger.warning(f"⚠️ [{correlation_id}] Hub no disponible para reenvío de evento a {update_payload['recipient_id']}")
    except Exception as e:
        logger.warning(f"⚠️ [{correlation_id}] Excepción al publicar evento al MessageBus: {e}")
    finally:
        await transport.stop()
        
    return InvokeResponse(content=autogen_output, metadata={"status": "completed", "package_id": pkg_id})

@app.post("/a2a", response_model=JSONRPCResponse)
async def a2a_endpoint(http_request: Request, rpc: JSONRPCRequest) -> JSONRPCResponse:
    await verify_signature(http_request, rpc.model_dump())
    if rpc.method == "tasks/create":
        params_dict = rpc.params.get("params", {}) if isinstance(rpc.params.get("params"), dict) else {}
        prompt = (
            rpc.params.get("user_prompt") or
            rpc.params.get("prompt_or_task") or
            rpc.params.get("prompt") or
            params_dict.get("user_prompt") or
            params_dict.get("prompt_or_task") or
            params_dict.get("prompt") or
            "Procesar negociación agéntica en AutoGen"
        )
        pkg_id = rpc.params.get("package_id") or params_dict.get("package_id")
        target_cat = rpc.params.get("target_category") or params_dict.get("target_category")
        target_tls = rpc.params.get("target_tools") or params_dict.get("target_tools")
        task_id = rpc.params.get("_task_id") or params_dict.get("_task_id")
        out = await run_autogen_logic(prompt, package_id=pkg_id, target_category=target_cat, target_tools=target_tls, task_id=task_id)
        return JSONRPCResponse.success(rpc.id, {"output": out})
    return JSONRPCResponse.failure(rpc.id, -32601, "Method not found")

@app.get("/mcp/tools", response_model=MCPToolsListResponse)
async def mcp_list():
    """Descubrimiento de herramientas MCP para la UI y Hub."""
    return MCPToolsListResponse(tools=universal_bridge.mcp_schemas)

@app.post("/mcp/call")
async def mcp_call(http_request: Request, tool_call: MCPToolCallRequest):
    """Ejecución de herramientas MCP (Invocado por A2UI o Hub)."""
    await verify_signature(http_request, tool_call.model_dump())
    logger.info(f"MCP Call: {tool_call.name} with {tool_call.arguments}")
    
    try:
        res = await universal_bridge.invoke_tool(tool_call.name, tool_call.arguments)
        return MCPResponse.text(res)
    except ValueError as e:
        return MCPResponse.error(str(e))
    except Exception as e:
        logger.error(f"Error en MCP Call: {e}")
        return MCPResponse.error(f"Tool execution failed: {str(e)}")

if __name__ == "__main__":
    _host = os.getenv("SERVICE_HOST", "127.0.0.1")
    _port = int(os.getenv("SERVICE_PORT", "8003"))
    uvicorn.run(app, host=_host, port=_port)
