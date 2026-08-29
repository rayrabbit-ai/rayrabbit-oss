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
import json
import logging
import sys
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# --- Inyección de Soberanía Local (OSS: 100% Desacoplado) ---
service_dir = Path(__file__).parent.resolve()
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Body
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64

# --- Protocolos Locales (Agnósticos) ---
from protocols import (
    JSONRPCRequest, JSONRPCResponse, MCPTool,
    MCPToolsListResponse, MCPToolCallRequest, MCPResponse
)

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
        self.client = None

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

# --- Inyección de Soberanía Local (OSS: 100% Desacoplado) ---
from sovereign import RuntimeContext, SovereignIdentity

# --- Inicialización del Servicio ---
AGENT_ID = "langchain_service"
runtime_context = RuntimeContext()

# Configuración del Logger
logger = logging.getLogger("langchain_service")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')

# Directorio de logs soberano
LOG_DIR = runtime_context.get_agent_data_path(AGENT_ID, "audit_logs")
os.makedirs(LOG_DIR, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "langchain_service_internal.log"), encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Cargar variables de entorno (Prioridad: HOME/.env o CWD/.env)
DOTENV_PATH = runtime_context.resolve_env_path(".env")
load_dotenv(DOTENV_PATH)
logger.info(f"Cargando .env desde: {DOTENV_PATH}")

# --- Dependencias de Framework (LangChain) ---
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_ollama import ChatOllama
    from langchain_core.prompts import PromptTemplate
    from langchain_core.messages import BaseMessage
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error de dependencias: {e}. Instala: pip install langchain-google-genai langchain-ollama langchain-core")
    LANGCHAIN_AVAILABLE = False

# --- Utilidades de Seguridad Integradas ---
class LocalJWSManager:
    """Gestor de JWS para el agente soberano (OSS)."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.identity = SovereignIdentity(agent_id)
        # Asegurar identidad y obtener clave privada
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

        # --- NUEVO: Patrón de Memoria L2 ---
        self.brain_dir = Path(".rayrabbit_data/brain") / self.agent_id
        self.brain_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = self.brain_dir / "service_context.json"
        self.context: Dict[str, Any] = self._load_context()

    def _load_context(self) -> Dict[str, Any]:
        if self.history_path.exists():
            try:
                return json.loads(self.history_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save_context(self):
        try:
            self.history_path.write_text(json.dumps(self.context, indent=2), encoding="utf-8")
        except Exception:
            pass
    
    def _b64url(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    def sign_message(self, message: Dict[str, Any]) -> str:
        header = {"alg": "RS256", "typ": "JWS"}
        # Usar separadores consistentes (sin espacios) para evitar desajustes JWS
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
        # Use the public key PEM loaded from SovereignIdentity
        return self.public_key_pem.replace('\n', '').replace('-----BEGIN PUBLIC KEY-----', '').replace('-----END PUBLIC KEY-----', '').strip()

    def get_jws_headers(self, message: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "X-RayRabbit-JWS": self.sign_message(message),
            "X-RayRabbit-Agent-ID": self.agent_id,
            "X-RayRabbit-Bridge-Public-Key-PEM": self.get_public_key_pem()
        }
        if correlation_id:
            headers["X-RayRabbit-Correlation-ID"] = correlation_id
        return headers

# --- Inicialización del Servicio ---
jws_manager = LocalJWSManager(AGENT_ID)

_rr_api_url = os.getenv("RAYRABBIT_API_URL")
if not _rr_api_url:
    logger.warning("⚠️  RAYRABBIT_API_URL no definida. Usando fallback local http://127.0.0.1:8005")
    _rr_api_url = "http://127.0.0.1:8005"
RAYRABBIT_API_URL = _rr_api_url
MESSAGE_BUS_ENDPOINT = f"{RAYRABBIT_API_URL}/api/publish-message"

class InvokeRequest(BaseModel):
    operation: str = "invoke_chain"
    input_variables: Dict[str, Any]
    prompt_template: str
    correlation_id: Optional[str] = None # Añadido para trazabilidad

class InvokeResponse(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

async def verify_signature(request: Request, payload_dict: Dict[str, Any]):
    sender_id = request.headers.get("X-RayRabbit-Agent-ID")
    jws_signature = request.headers.get("X-RayRabbit-JWS")
    header_pub_key_pem = request.headers.get("X-RayRabbit-Bridge-Public-Key-PEM")
    # Trazabilidad: Extraer CID de cabecera si existe
    cid = request.headers.get("X-RayRabbit-Correlation-ID")
    
    if not jws_signature or not header_pub_key_pem:
        raise HTTPException(status_code=401, detail="Se requiere JWS.")
    
    try:
        # Limpiar posibles caracteres de escape de Windows (\r) que corrompen la clave PEM
        clean_key = header_pub_key_pem.replace('\r', '').replace('\n', '')
        if "BEGIN PUBLIC KEY" not in clean_key:
            key_data = f"-----BEGIN PUBLIC KEY-----\n{clean_key}\n-----END PUBLIC KEY-----".encode('utf-8')
        else:
            key_data = clean_key.encode('utf-8')
            
        public_key = serialization.load_pem_public_key(key_data)
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
        logger.info(f"✅ JWS Verificado: {sender_id} (CID: {cid})")
    except Exception as e:
        logger.error(f"Fallo de seguridad: {e}")
        raise HTTPException(status_code=403, detail="Firma JWS inválida.")
    
    return cid # Retornamos el CID para uso opcional

# --- Persistencia Local Aislada (Shared Nothing) ---
# --- Adaptador Universal de LangChain (Generic Bridge) ---
from langchain_core.tools import BaseTool


from pydantic import BaseModel, Field, create_model

def _build_dynamic_args_schema(tool_name: str, input_schema: Dict[str, Any]) -> type[BaseModel]:
    """Construye dinámicamente el esquema de argumentos Pydantic para la herramienta MCP desde su definición JSON Schema."""
    properties = input_schema.get("properties", {}) if isinstance(input_schema, dict) else {}
    required_fields = set(input_schema.get("required", [])) if isinstance(input_schema, dict) else set()
    
    fields = {}
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": Union[dict, str, Any]
    }
    
    for prop_name, prop_info in properties.items():
        if not isinstance(prop_info, dict):
            prop_info = {}
        prop_type_str = prop_info.get("type", "string")
        py_type = type_mapping.get(prop_type_str, Any)
        has_default = "default" in prop_info
        is_required = (prop_name in required_fields) and not has_default
        
        if is_required:
            default_val = ...
        else:
            default_val = prop_info.get("default", None)
            if default_val is None:
                py_type = Union[py_type, type(None)]
                
        fields[prop_name] = (py_type, Field(default=default_val, description=prop_info.get("description", f"Parámetro {prop_name}")))
        
    clean_name = "".join([c for c in tool_name.title() if c.isalnum()]) or "Dynamic"
    return create_model(f"{clean_name}Schema", **fields)

def _create_langchain_tool(t_name: str, t_desc: str, input_schema: Dict[str, Any], hub_url: str, task_id: Optional[str] = None) -> BaseTool:
    """Fábrica dinámica segura de herramientas BaseTool de LangChain para evitar NameError en Pydantic."""
    schema_model = _build_dynamic_args_schema(t_name, input_schema)
    
    class DynamicHubTool(BaseTool):
        name: str = t_name
        description: str = t_desc
        args_schema: type[BaseModel] = schema_model
        
        def _get_payload(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
            payload = {"name": t_name, "params": kwargs, "sender_id": "langchain_service"}
            if task_id:
                payload["_task_id"] = task_id
                kwargs["_task_id"] = task_id
            return payload
        
        def _run(self, **kwargs) -> str:
            try:
                with httpx.Client(timeout=600.0) as c:
                    r = c.post(
                        f"{hub_url}/api/execute-tool",
                        json=self._get_payload(kwargs)
                    )
                    if r.status_code == 200:
                        res_data = r.json()
                        return str(res_data.get("result") or res_data)
                    return f"Error HTTP {r.status_code}: {r.text}"
            except Exception as ex:
                return f"Error ejecutando herramienta {t_name}: {ex}"

        async def _arun(self, **kwargs) -> str:
            try:
                async with httpx.AsyncClient(timeout=600.0) as c:
                    r = await c.post(
                        f"{hub_url}/api/execute-tool",
                        json=self._get_payload(kwargs)
                    )
                    if r.status_code == 200:
                        res_data = r.json()
                        return str(res_data.get("result") or res_data)
                    return f"Error HTTP {r.status_code}: {r.text}"
            except Exception as ex:
                return f"Error ejecutando herramienta {t_name}: {ex}"

    return DynamicHubTool()

async def _fetch_hub_mcp_tools(prompt: str = "", target_category: Optional[str] = None, target_tools: Optional[str] = None, task_id: Optional[str] = None) -> List[BaseTool]:
    """Descubre e inscribe dinámicamente herramientas MCP desde el Hub usando BM25."""
    hub_url = os.getenv("RAYRABBIT_API_URL", RAYRABBIT_API_URL)
    mcp_tools_url = f"{hub_url}/api/mcp/tools"
    discovered_tools: List[BaseTool] = []

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

                    tool_fn = _create_langchain_tool(tool_name, tool_description, input_schema, hub_url, task_id)
                    discovered_tools.append(tool_fn)
                    logger.info(f"LangChain: Herramienta '{tool_name}' ({category}) vinculada dinámicamente desde metadatos MCP.")
    except Exception as e:
        logger.warning(f"LangChain: No se pudieron auto-descubrir herramientas MCP: {e}")
        
    return discovered_tools

async def run_langchain_logic(
    prompt_or_task: str,
    package_id: str = "DEFAULT-TASK",
    priority: str = "medium",
    correlation_id: Optional[str] = None,
    target_category: Optional[str] = None,
    target_tools: Optional[str] = None,
    task_id: Optional[str] = None
) -> str:
    """Ejecuta razonamiento cognitivo en LangChain con herramientas MCP descubiertas dinámicamente vía BM25."""
    global llm
    if not llm:
        return "Error: LangChain LLM no inicializado en el servicio."
    
    # 1. Búsqueda Dinámica BM25 de herramientas en el Hub MCP
    tools = await _fetch_hub_mcp_tools(prompt=prompt_or_task, target_category=target_category, target_tools=target_tools, task_id=task_id)
    
    if not tools:
        res = await llm.ainvoke(prompt_or_task)
        return str(res.content) if hasattr(res, 'content') else str(res)
        
    try:
        from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
        system_prompt = (
            "Eres el Servicio Cognitivo LangChain de la infraestructura RayRabbit. "
            "Tienes a tu disposición herramientas MCP provistas dinámicamente por la infraestructura (como lectura de memoria y datos de negocio). "
            "Tu objetivo es analizar la información acumulada y generar un resumen ejecutivo o análisis conciso y claro en lenguaje natural para el usuario. "
            "No intentes editar archivos ni ejecutar operaciones de sistema a menos que la tarea lo pida explícitamente."
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt_or_task)
        ]
        
        tool_map = {t.name: t for t in tools}
        bound_llm = llm.bind_tools(tools)
        
        for step in range(5):
            ai_msg = await bound_llm.ainvoke(messages)
            messages.append(ai_msg)
            
            if not getattr(ai_msg, "tool_calls", None):
                return str(ai_msg.content)
                
            for tool_call in ai_msg.tool_calls:
                t_name = tool_call["name"]
                t_args = tool_call["args"]
                t_id = tool_call["id"]
                
                logger.info(f"LangChain: Invocando herramienta '{t_name}' ({t_args})...")
                if t_name in tool_map:
                    try:
                        tool_res = await tool_map[t_name].ainvoke(t_args)
                    except Exception as e:
                        tool_res = f"Error ejecutando {t_name}: {e}"
                else:
                    tool_res = f"Herramienta {t_name} no disponible."
                    
                messages.append(ToolMessage(content=str(tool_res), tool_call_id=t_id, name=t_name))
                
        return str(messages[-1].content)
    except Exception as e:
        logger.warning(f"LangChain fallback tras error en tool calling: {e}")
        res = await llm.ainvoke(prompt_or_task)
        return str(res.content) if hasattr(res, 'content') else str(res)

class RunLcelChainSchema(BaseModel):
    prompt_template: str = Field(..., description="Plantilla del prompt o tarea a ejecutar por LangChain")
    input_variables: Dict[str, Any] = Field(default={}, description="Diccionario opcional de variables para inyectar en la plantilla")
    target_category: Optional[str] = Field(default=None, description="Categoría de dominio opcional")
    target_tools: Optional[str] = Field(default=None, description="Nombres de herramientas específicos opcionales")

class RunLcelChainTool(BaseTool):
    name: str = "run_lcel_chain"
    description: str = "Ejecuta una cadena dinámica de LangChain (LCEL) con herramientas MCP descubiertas dinámicamente vía BM25."
    args_schema: type[BaseModel] = RunLcelChainSchema

    def _run(self, prompt_template: str, input_variables: Dict[str, Any] = {}, target_category: Optional[str] = None, target_tools: Optional[str] = None, **kwargs) -> str:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._arun(prompt_template, input_variables, target_category, target_tools, **kwargs),
                loop
            )
            return future.result()
        return asyncio.run(self._arun(prompt_template, input_variables, target_category, target_tools, **kwargs))

    async def _arun(self, prompt_template: str, input_variables: Dict[str, Any] = {}, target_category: Optional[str] = None, target_tools: Optional[str] = None, **kwargs) -> str:
        prompt_txt = prompt_template
        if input_variables:
            for k, v in input_variables.items():
                prompt_txt = prompt_txt.replace(f"{{{k}}}", str(v))
        return await run_langchain_logic(prompt_txt, target_category=target_category, target_tools=target_tools, task_id=kwargs.get("task_id"))




class UniversalLangChainBridge:
    def __init__(self):
        self.tool_registry: Dict[str, BaseTool] = {}
        self.mcp_schemas: List[MCPTool] = []
        # Exponer la herramienta genérica run_lcel_chain por defecto
        self.register_tools([RunLcelChainTool()])
        
    def register_tools(self, tools: List[BaseTool]):
        """Registra herramientas de LangChain y genera sus esquemas MCP correspondientes."""
        for tool in tools:
            self.tool_registry[tool.name] = tool
            
            # Extraer esquema de parámetros usando Pydantic
            input_schema = {"type": "object", "properties": {}, "required": []}
            if tool.args_schema:
                schema = tool.args_schema.model_json_schema() # Para Pydantic v2
                input_schema["properties"] = schema.get("properties", {})
                input_schema["required"] = schema.get("required", [])
            
            # Registrar esquema universal
            input_schema["category"] = "cognitive"
            self.mcp_schemas.append(MCPTool(
                name=tool.name,
                description=tool.description,
                category="cognitive",
                inputSchema=input_schema
            ))
            logger.info(f"[Bridge] Herramienta registrada dinámicamente: {tool.name}")

    async def invoke_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Invoca una herramienta dinámicamente por su nombre."""
        if name not in self.tool_registry:
            raise ValueError(f"Tool {name} no encontrada en el registro.")
        tool = self.tool_registry[name]
        args_copy = dict(arguments)
        args_copy.pop("_correlation_id", None)
        result = await tool.ainvoke(args_copy)
        return str(result)

# Instanciamos el bridge genérico
universal_bridge = UniversalLangChainBridge()

# --- Servicio Cognitivo Puro: Consumo Dinámico de Herramientas vía Hub MCP ---
logger.info("🚀 Servicio Cognitivo LangChain iniciado. Herramientas resueltas dinámicamente mediante Hub MCP.")

# --- Aplicación FastAPI ---
# --- Selección de Proveedor Soberano Universal (Sovereign LiteLLM Style) ---
full_model_name = os.getenv("LLM_MODEL_FULL_NAME")
base_url = os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL")
provider = os.getenv("LLM_PROVIDER", "google").lower()

if full_model_name:
    model = full_model_name
else:
    if provider == "ollama":
        model = f"ollama/{os.getenv('OLLAMA_MODEL', 'gemma4:e4b')}"
    else:
        model = f"gemini/{os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')}"

logger.info(f"🚀 [SOVEREIGN LITELLM] Inicializando LangChain con {model} (Base URL: {base_url})")

try:
    from langchain_litellm import ChatLiteLLM
    api_key = os.getenv("LLM_API_KEY")
    llm = ChatLiteLLM(
        model=model,
        api_base=base_url,
        api_key=api_key,
        timeout=600
    )
except ImportError:
    logger.error("langchain-litellm no instalado. Usando fallback nativo.")
    if "ollama" in model:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=model.split("/")[-1], base_url=base_url)
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model=model.split("/")[-1], google_api_key=api_key)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización del servicio soberano."""
    # 1. Registrar identidad en el Hub (si está disponible)
    hub_url = RAYRABBIT_API_URL  # Ya validada y logueada al inicio del módulo

    # 2. Reportar endpoints dinámicos para ruteo P2P y Bridges sin configuración previa
    _self_host = os.getenv("RAYRABBIT_P2P_HOST", "http://127.0.0.1:8002")
    p2p_endpoint = f"{_self_host}/a2a"
    openapi_url = f"{_self_host}/openapi.json"

    # Lanzar de fondo para no bloquear el inicio del servidor HTTP
    asyncio.create_task(jws_manager.identity.register_with_backoff(
        hub_url,
        p2p_endpoint=p2p_endpoint,
        openapi_url=openapi_url
    ))

    
    # Prewarm Ollama (solo si LLM_PROVIDER=ollama): carga el modelo en RAM antes de recibir peticiones
    if os.getenv("LLM_PROVIDER", "google").lower() == "ollama":
        async def _prewarm_ollama():
            import httpx
            try:
                async with httpx.AsyncClient(timeout=1200) as client:
                    await client.post(
                        f"{os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')}/api/generate",
                        json={"model": os.getenv("OLLAMA_MODEL", "gemma4:e4b"), "prompt": "ok", "stream": False}
                    )
                logger.info("✅ [PREWARM] Ollama modelo cargado en RAM.")
            except Exception as e:
                logger.warning(f"⚠️ [PREWARM] Ollama prewarm no completado: {e}")
        asyncio.create_task(_prewarm_ollama())

    logger.info(f"🚀 LangChain Service '{AGENT_ID}' iniciado y federado.")
    yield

app = FastAPI(
    title="RayRabbit External LangChain Service",
    description="Servicio que procesa el análisis inicial de órdenes (JSON) usando LangChain + Gemini.",
    version="0.1.0",
    lifespan=lifespan
)

# --- Endpoint FastAPI ---
@app.get("/health")
async def health():
    return {"status": "ok", "service": "LangChain Gemini OSS", "llm": "ready" if llm else "error"}

@app.post("/invoke", operation_id="invoke_chain", response_model=InvokeResponse)
async def invoke(request: Request, payload: Dict[str, Any] = Body(...)):
    """Endpoint principal para el DeclarativeBridge. Preservado con lógica real."""
    cid_from_header = await verify_signature(request, payload)
    req_data = InvokeRequest(**payload)
    
    # Prioridad: Header > Payload explicit > payload root
    correlation_id = cid_from_header or payload.get("correlation_id") or req_data.correlation_id or str(uuid.uuid4())

    # Assuming 'client_msg' is part of input_variables or derived from it for logging
    client_msg = req_data.input_variables.get("client_message", "No client message provided")
    logger.info(f"Procesando invocación: {client_msg}")
    
    # 1. Lógica de IA Híbrida: Extracción o Generación
    is_final_response = "Eres un agente" in req_data.prompt_template
    extracted_id = "N/A"
    sap_data = ""

    if llm:
        try:
            if is_final_response:
                # Caso A: Generación de respuesta amable al cliente
                prompt = PromptTemplate.from_template(req_data.prompt_template)
                chain = prompt | llm
                res = await chain.ainvoke(req_data.input_variables)
                sap_data = str(res.content).strip()
                extracted_id = req_data.input_variables.get("package_id", "N/A")
                logger.info(f"LangChain: Generada respuesta final para {extracted_id}")
            else:
                # Caso B: Extracción inicial de ID para el flujo
                req_msg = str(req_data.input_variables)
                tmpl = "Analiza el siguiente mensaje y extrae el ID del pedido o paquete (ej. ORD-..., PKG-..., #A...). Si existe, retornalo limpio. Si no, retorna 'N/A'. Mensaje: {msg}"
                prompt = PromptTemplate.from_template(tmpl)
                chain = prompt | llm
                extracted_id_res = await chain.ainvoke({"msg": req_msg})
                extracted_id = str(extracted_id_res.content).strip()
                
                logger.info(f"LangChain: ID Extraído -> {extracted_id}")
                
                if extracted_id != "N/A":
                    sap_data = analyze_order(extracted_id)
                    if "Order not found" in sap_data:
                         track_res = track_package(extracted_id)
                         if "not found" not in track_res:
                             sap_data = track_res
                else:
                    sap_data = "No valid ID identified."
        except Exception as e:
            logger.error(f"Error AI: {e}")
            sap_data = f"Error: {str(e)}"
    else:
        sap_data = "LLM Offline"

    # 2. Publicar respuesta y enrutar
    # correlation_id ya calculado arriba
    
    outcome_payload = {
        "sender_id": AGENT_ID,
        "sender_name": "LangChain Service",
        "recipient_id": "langchain_response_listener",
        "message_type": "response",
        "content": {
            "original_request": client_msg, 
            "sap_analysis": sap_data,
            "content": sap_data if is_final_response else "", # CAMPO CLAVE para el orquestador
            "package_id": extracted_id,
            "client_message": client_msg,
            "task": "final_response" if is_final_response else "investigate_delivery",
            "priority": "high" if "delayed" in str(sap_data) else "medium"
        },
        "correlation_id": correlation_id
    }
    
    transport = HTTPClientTransport()
    await transport.start()
    try:
        headers = jws_manager.get_jws_headers(outcome_payload, correlation_id=correlation_id)
        success = await transport.send(Message(**outcome_payload), MESSAGE_BUS_ENDPOINT, headers=headers)
        if success:
            logger.info(f"✅ [{correlation_id}] Respuesta publicada exitosamente al Hub: {outcome_payload['recipient_id']}")
        else:
            logger.error(f"❌ [{correlation_id}] Fallo al publicar respuesta al Hub: {outcome_payload['recipient_id']}")
    finally:
        await transport.stop()
        
    return InvokeResponse(content=f"Processed via SAP TM: {sap_data}")

@app.post("/a2a", response_model=JSONRPCResponse)
async def a2a_endpoint(request: Request, rpc: JSONRPCRequest):
    """Endpoint A2A Nativo."""
    await verify_signature(request, rpc.model_dump())
    
    if rpc.method == "tasks/create":
        params_dict = rpc.params.get("params", {}) if isinstance(rpc.params.get("params"), dict) else {}
        prompt_txt = (
            rpc.params.get("prompt") or
            rpc.params.get("prompt_or_task") or
            rpc.params.get("user_prompt") or
            params_dict.get("prompt") or
            params_dict.get("prompt_or_task") or
            params_dict.get("user_prompt") or
            "Procesar cadena LCEL de LangChain"
        )
        task_id = rpc.params.get("_task_id") or params_dict.get("_task_id")
        target_category = rpc.params.get("target_category") or params_dict.get("target_category")
        target_tools = rpc.params.get("target_tools") or params_dict.get("target_tools")

        output = await run_langchain_logic(
            prompt_or_task=prompt_txt,
            target_category=target_category,
            target_tools=target_tools,
            task_id=task_id
        )
        return JSONRPCResponse(id=rpc.id, result={"output": output, "status": "completed"})
        
    return JSONRPCResponse(id=rpc.id, error={"code": -32601, "message": "Method not found"})

@app.post("/mcp/call")
async def mcp_call_tool(request: Request, tool_call: MCPToolCallRequest):
    """Endpoint MCP Genérico."""
    await verify_signature(request, tool_call.model_dump())
    
    try:
        res = await universal_bridge.invoke_tool(tool_call.name, tool_call.arguments)
        return MCPResponse.text(res)
    except ValueError as e:
        return MCPResponse.error(str(e))
    except Exception as e:
        logger.error(f"Error invocando herramienta {tool_call.name}: {e}")
        return MCPResponse.error(f"Internal error: {e}")

@app.get("/mcp/tools")
async def mcp_list():
    """Retorna los esquemas MCP generados dinámicamente."""
    return MCPToolsListResponse(tools=universal_bridge.mcp_schemas)

if __name__ == "__main__":
    _host = os.getenv("SERVICE_HOST", "127.0.0.1")
    _port = int(os.getenv("SERVICE_PORT", "8002"))
    uvicorn.run(app, host=_host, port=_port)