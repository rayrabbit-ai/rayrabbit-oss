import faulthandler
faulthandler.enable()

import os
import asyncio
from dotenv import load_dotenv
import json
import logging
import sys
os.environ.setdefault("LITELLM_LOGGING", "disabled")
import uuid

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from fastapi import FastAPI, HTTPException, Request, Body
from pydantic import BaseModel, Field
import uvicorn
import httpx
from pathlib import Path

# --- Inyección de Soberanía Local (OSS: 100% Desacoplado) ---
service_dir = Path(__file__).parent.resolve()
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from sovereign import RuntimeContext, SovereignIdentity

# --- Inicialización del Servicio ---
AGENT_ID = "crewai_service"
runtime_context = RuntimeContext()

# Configuración del Logger
logger = logging.getLogger("crewai_service")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')

LOG_DIR = runtime_context.get_agent_data_path(AGENT_ID, "audit_logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "crewai_service_internal.log")

file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Cargar variables desde .env
DOTENV_PATH = runtime_context.resolve_env_path(".env")
load_dotenv(DOTENV_PATH)
logger.info(f"Cargando .env desde: {DOTENV_PATH}")

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
_rr_api_url = os.getenv("RAYRABBIT_API_URL")
if not _rr_api_url:
    logger.warning("⚠️  RAYRABBIT_API_URL no definida. Usando fallback local http://127.0.0.1:8005")
    _rr_api_url = "http://127.0.0.1:8005"
RAYRABBIT_API_URL = _rr_api_url
MESSAGE_BUS_ENDPOINT = f"{RAYRABBIT_API_URL}/api/publish-message"

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
        logger.info(f"✅ JWS Verificado en CrewAI (CID: {cid}): {sender_id}")
        return cid
        
    except Exception as e:
        logger.error(f"❌ FALLO DE SEGURIDAD en CrewAI: {e}")
        raise HTTPException(status_code=403, detail=f"Firma JWS inválida: {str(e)}")

# --- Adaptador Universal de CrewAI (Generic Bridge Agnóstico) ---
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import BaseTool

from pydantic import BaseModel, Field, create_model

class InvokeRequest(BaseModel):
    operation: str = "run_crew"
    task: Optional[str] = None
    package_id: Optional[str] = "TASK-001"
    priority: Optional[str] = "medium"
    client_message: Optional[str] = None
    prompt: Optional[str] = None
    correlation_id: Optional[str] = None

class InvokeResponse(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

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
        # Resolver anyOf (Pydantic V2 nullable) antes de fallback ciego a "string"
        if "anyOf" in prop_info:
            prop_type_str = "string"
            for any_of_entry in prop_info["anyOf"]:
                if isinstance(any_of_entry, dict) and any_of_entry.get("type") != "null":
                    prop_type_str = any_of_entry.get("type", "string")
                    break
        else:
            prop_type_str = prop_info.get("type", "string")
        py_type = type_mapping.get(prop_type_str, Any)
        has_default = "default" in prop_info
        is_required = (prop_name in required_fields) and not has_default
        
        if is_required:
            default_val = ...
        else:
            default_val = prop_info.get("default", None)
            
            # Para Pydantic V2, si el default es None, el tipo debe permitir None explícitamente.
            # Además esto evita que campos opcionales sin default rompan la validación.
            if default_val is None:
                py_type = Union[py_type, type(None)]
                
        fields[prop_name] = (py_type, Field(default=default_val, description=prop_info.get("description", f"Parámetro {prop_name}")))
        
    clean_name = "".join([c for c in tool_name.title() if c.isalnum()]) or "Dynamic"
    return create_model(f"{clean_name}Schema", **fields)

def _create_crew_tool(t_name: str, t_desc: str, input_schema: Dict[str, Any], hub_url: str) -> BaseTool:
    """Fábrica dinámica segura de herramientas BaseTool de CrewAI con Pydantic."""
    schema_model = _build_dynamic_args_schema(t_name, input_schema)
    
    class DynamicHubTool(BaseTool):
        name: str = t_name
        description: str = t_desc
        args_schema: type[BaseModel] = schema_model
        category: str = ""
        task_id: Optional[str] = None
        def _run(self, **kwargs) -> str:
            try:
                # Pasar task_id para que el Nodo de la herramienta pueda disparar HITL si su lógica determinista lo exige
                payload = {"name": t_name, "params": kwargs, "sender_id": "crewai_service"}
                if getattr(self, "task_id", None):
                    payload["_task_id"] = self.task_id
                    kwargs["_task_id"] = self.task_id  # Inyección también en params por compatibilidad
                
                with httpx.Client(timeout=600.0) as c:
                    r = c.post(
                        f"{hub_url}/api/execute-tool",
                        json=payload
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
                        json={"name": t_name, "params": kwargs, "sender_id": "crewai_service"}
                    )
                    if r.status_code == 200:
                        res_data = r.json()
                        return str(res_data.get("result") or res_data)
                    return f"Error HTTP {r.status_code}: {r.text}"
            except Exception as ex:
                return f"Error ejecutando herramienta {t_name}: {ex}"

    return DynamicHubTool()

async def _fetch_hub_mcp_tools(prompt: str = "", target_category: Optional[str] = None, target_tools: Optional[str] = None, task_id: Optional[str] = None) -> List[BaseTool]:
    """Descubre e inscribe dinámicamente herramientas MCP usando BM25 y filtrado agnóstico."""
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
                    
                    tool_fn = _create_crew_tool(tool_name, tool_description, input_schema, hub_url)
                    tool_fn.task_id = task_id  # Inyectar para delegación de HITL
                    discovered_tools.append(tool_fn)
                    logger.info(f"CrewAI: Herramienta '{tool_name}' ({category}) vinculada dinámicamente desde metadatos MCP.")
    except Exception as e:
        logger.warning(f"CrewAI: No se pudieron auto-descubrir herramientas MCP en el Hub: {e}")
        
    return discovered_tools

async def run_crew_logic(prompt_or_task: str, package_id: str = "DEFAULT-TASK", priority: str = "medium", correlation_id: str = None, target_category: Optional[str] = None, target_tools: Optional[str] = None, task_id: Optional[str] = None) -> str:
    """Ejecuta razonamiento agéntico multi-agente CrewAI de forma 100% agnóstica de dominio."""
    full_model_name = os.getenv("LLM_MODEL_FULL_NAME")
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL")
    
    if full_model_name:
        model_name = full_model_name
    else:
        provider = os.getenv("LLM_PROVIDER", "google").lower()
        if provider == "ollama":
            model_name = f"ollama/{os.getenv('OLLAMA_MODEL', 'gemma4:e4b')}"
            base_url = base_url or "http://127.0.0.1:11434"
        else:
            model_name = f"gemini/{os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')}"
            
    logger.info(f"🚀 [SOVEREIGN CREWAI] Ejecutando cuadrilla agnóstica con {model_name}")
    
    api_key = os.getenv("LLM_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    llm_kwargs = {"model": model_name, "timeout": 1200}
    if base_url:
        llm_kwargs["base_url"] = base_url
    if api_key:
        llm_kwargs["api_key"] = api_key
    
    crew_llm = LLM(**llm_kwargs)

    # Inscribir dinámicamente herramientas desde metadatos MCP de la infraestructura (100% agnóstico via BM25)
    all_tools = await _fetch_hub_mcp_tools(prompt=prompt_or_task, target_category=target_category, target_tools=target_tools, task_id=task_id)

    # Divulgación por rol: El analista recibe todas las herramientas Top-K (dominio + memoria)
    analyst_tools = all_tools
    
    # El planificador recibe ÚNICAMENTE herramientas de memoria declarativa para prevenir el Tool Hoarding
    planner_tools = [
        t for t in all_tools 
        if getattr(t, "category", "") in ("sovereign_memory_node", "memory")
    ]

    analyst = Agent(
        role='Analista Especialista',
        goal='Analizar y procesar la tarea solicitada usando SOLO las herramientas disponibles. '
             'Cuando tengas el resultado final usa: Thought: I now know the final answer\nFinal Answer: [respuesta]',
        backstory='Experto en análisis agéntico y procesamiento estructurado de información.',
        llm=crew_llm,
        tools=analyst_tools,
        verbose=False,
        allow_delegation=False,
        max_retry_limit=3
    )
    
    planner = Agent(
        role='Planificador Estratégico',
        goal='Sintetizar los hallazgos del análisis previo y estructurar el plan de acción final. '
             'Usa SOLO las herramientas de memoria disponibles para consultar diagnósticos si los requieres. NO inventes nombres de herramientas. '
             'Cuando tengas el resultado final usa: Thought: I now know the final answer\nFinal Answer: [respuesta]',
        backstory='Estratega senior especializado en formulación de planes de ejecución.',
        llm=crew_llm,
        tools=planner_tools,
        verbose=False,
        allow_delegation=False,
        max_retry_limit=3
    )
    
    t1 = Task(
        description=f"Investigar y analizar: {prompt_or_task}. Proporcionar diagnóstico claro.",
        expected_output="Informe analítico detallado con datos reales obtenidos de las herramientas.",
        agent=analyst
    )
    
    t2 = Task(
        description=f"Basándote en el análisis previo sobre: {prompt_or_task}. "
                    "Consolida los hallazgos del análisis anterior y estructura recomendaciones o plan final. "
                    "Usa SOLO las herramientas disponibles. Si necesitas leer memoria, usa el session_id "
                    "mencionado en la tarea original.",
        expected_output="Plan o respuesta final estructurada con recomendaciones concretas.",
        agent=planner,
        context=[t1]
    )
    
    crew = Crew(
        agents=[analyst, planner], 
        tasks=[t1, t2], 
        verbose=False,
        process=Process.sequential
    )
    
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, crew.kickoff)
    final_output = str(result.raw) if hasattr(result, 'raw') else str(result)
    return final_output

class ExecuteCrewSchema(BaseModel):
    prompt_or_task: str = Field(..., description="Descripción del objetivo o tarea a ejecutar por la cuadrilla CrewAI")
    package_id: str = Field(default="DEFAULT-TASK", description="ID opcional del objeto o contexto a procesar")
    priority: str = Field(default="medium", description="Prioridad de ejecución (low, medium, high)")
    target_category: Optional[str] = Field(default=None, description="Categoría de dominio opcional o lista separada por comas (ej: 'logistics_ui_manager,system_tools_node')")
    target_tools: Optional[str] = Field(default=None, description="Nombres de herramientas específicos opcionales separados por comas (ej: 'analyze_order,save_memory_fact')")

class ExecuteCrewTool(BaseTool):
    name: str = "execute_crew_task"
    description: str = "Ejecuta orquestación cognitiva multi-agente de CrewAI instanciando cuadrillas (Crew, Agents, Tasks) de forma totalmente agnóstica."
    args_schema: type[BaseModel] = ExecuteCrewSchema

    def _run(self, prompt_or_task: str, package_id: str = "DEFAULT-TASK", priority: str = "medium", target_category: Optional[str] = None, target_tools: Optional[str] = None) -> str:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                run_crew_logic(prompt_or_task, package_id, priority, str(uuid.uuid4()), target_category, target_tools),
                loop
            )
            return future.result()
        else:
            return asyncio.run(run_crew_logic(prompt_or_task, package_id, priority, str(uuid.uuid4()), target_category, target_tools))

    async def _arun(self, prompt_or_task: str, package_id: str = "DEFAULT-TASK", priority: str = "medium", target_category: Optional[str] = None, target_tools: Optional[str] = None) -> str:
        return await run_crew_logic(prompt_or_task, package_id, priority, str(uuid.uuid4()), target_category, target_tools)

class UniversalCrewAIBridge:
    def __init__(self):
        self.tool_registry: Dict[str, BaseTool] = {}
        self.mcp_schemas: List[MCPTool] = []
        self.register_tools([ExecuteCrewTool()])
        
    def register_tools(self, tools: List[BaseTool]):
        for tool in tools:
            self.tool_registry[tool.name] = tool
            input_schema = {"type": "object", "properties": {}, "required": []}
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema.model_json_schema()
                input_schema["properties"] = schema.get("properties", {})
                input_schema["required"] = schema.get("required", [])
            
            input_schema["category"] = "cognitive"
            self.mcp_schemas.append(MCPTool(
                name=tool.name,
                description=tool.description,
                category="cognitive",
                inputSchema=input_schema
            ))
            logger.info(f"[Bridge] Herramienta CrewAI agnóstica registrada: {tool.name}")

    async def invoke_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if name not in self.tool_registry:
            raise ValueError(f"Tool '{name}' no encontrada en el registro de CrewAI.")
        tool = self.tool_registry[name]
        args_copy = dict(arguments)
        args_copy.pop("_correlation_id", None)
        try:
            result = await tool._arun(**args_copy)
        except NotImplementedError:
            result = tool._run(**args_copy)
        return str(result)

universal_bridge = UniversalCrewAIBridge()

# --- Servicio FastAPI ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    hub_url = RAYRABBIT_API_URL  # Ya validada y logueada al inicio del módulo

    _self_host = os.getenv("RAYRABBIT_P2P_HOST", "http://127.0.0.1:8001")
    p2p_endpoint = f"{_self_host}/a2a"
    openapi_url = f"{_self_host}/openapi.json"

    asyncio.create_task(jws_manager.identity.register_with_backoff(
        hub_url,
        p2p_endpoint=p2p_endpoint,
        openapi_url=openapi_url
    ))
    logger.info(f"🚀 CrewAI Service '{AGENT_ID}' iniciado y federado. P2P: {p2p_endpoint}")
    yield

app = FastAPI(
    title="RayRabbit External CrewAI Service",
    description="Servicio cognitivo agnóstico de CrewAI para orquestación multi-agente.",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "CrewAI Service Agnóstico"}

@app.post("/invoke", operation_id="run_crew", response_model=InvokeResponse)
async def invoke(request: Request, payload: Dict[str, Any] = Body(...)):
    """Endpoint declarativo OpenAPI para DeclarativeBridge (Vía A)."""
    cid_from_header = await verify_signature(request, payload)
    
    correlation_id = cid_from_header or payload.get("correlation_id") or str(uuid.uuid4())
    
    task_desc = (
        payload.get("task") or 
        payload.get("prompt") or 
        payload.get("client_message") or 
        "Procesar análisis en CrewAI"
    )
    package_id = payload.get("package_id") or "TASK-001"
    priority = payload.get("priority") or "medium"
    
    logger.info(f"🚀 [CREWAI INVOKE] Procesando tarea '{task_desc}' para paquete '{package_id}' (CID: {correlation_id})")
    
    # 1. Ejecutar razonamiento agnóstico de cuadrilla
    crew_output = await run_crew_logic(
        prompt_or_task=task_desc,
        package_id=package_id,
        priority=priority,
        correlation_id=correlation_id
    )
    
    # 2. Publicar evento/respuesta al MessageBus para downstream listeners (Modo Bridge)
    workflow_payload = {
        "sender_id": AGENT_ID,
        "sender_name": "CrewAI Service",
        "recipient_id": "crewai_workflow_listener",
        "message_type": "request",
        "content": {
            "task": task_desc,
            "package_id": package_id,
            "outcome": "crewai_plan_created",
            "details": crew_output,
            "crew_result": crew_output
        },
        "correlation_id": correlation_id
    }
    
    transport = HTTPClientTransport()
    await transport.start()
    try:
        headers = jws_manager.get_jws_headers(workflow_payload, correlation_id=correlation_id)
        success = await transport.send(Message(**workflow_payload), MESSAGE_BUS_ENDPOINT, headers=headers)
        if success:
            logger.info(f"✅ [{correlation_id}] Evento publicado exitosamente al Hub: {workflow_payload['recipient_id']}")
        else:
            logger.warning(f"⚠️ [{correlation_id}] Hub no disponible para reenvío de evento a {workflow_payload['recipient_id']}")
    except Exception as e:
        logger.warning(f"⚠️ [{correlation_id}] Excepción al publicar evento al MessageBus: {e}")
    finally:
        await transport.stop()
        
    return InvokeResponse(content=crew_output, metadata={"status": "completed", "package_id": package_id})

@app.post("/a2a", response_model=JSONRPCResponse)
async def a2a_endpoint(http_request: Request, rpc: JSONRPCRequest) -> JSONRPCResponse:
    await verify_signature(http_request, rpc.model_dump())
    if rpc.method == "tasks/create":
        params_dict = rpc.params.get("params", {}) if isinstance(rpc.params.get("params"), dict) else {}
        prompt = (
            rpc.params.get("prompt_or_task") or
            rpc.params.get("user_prompt") or
            rpc.params.get("prompt") or
            params_dict.get("prompt_or_task") or
            params_dict.get("user_prompt") or
            params_dict.get("prompt") or
            "Procesar tarea de análisis logístico en CrewAI"
        )
        pkg_id = rpc.params.get("package_id") or params_dict.get("package_id") or "TASK-001"
        target_cat = rpc.params.get("target_category") or params_dict.get("target_category")
        target_tls = rpc.params.get("target_tools") or params_dict.get("target_tools")
        task_id = rpc.params.get("_task_id") or params_dict.get("_task_id")
        res = await run_crew_logic(prompt, pkg_id, "high", str(rpc.id), target_category=target_cat, target_tools=target_tls, task_id=task_id)
        return JSONRPCResponse.success(rpc.id, {"task_id": str(rpc.id), "status": "completed", "output": res})
    return JSONRPCResponse.failure(rpc.id, -32601, f"Method not found: {rpc.method}")

@app.get("/mcp/tools", response_model=MCPToolsListResponse)
async def mcp_list_tools():
    return MCPToolsListResponse(tools=universal_bridge.mcp_schemas)

@app.post("/mcp/call")
async def mcp_call_tool(http_request: Request, tool_call: MCPToolCallRequest):
    await verify_signature(http_request, tool_call.model_dump())
    try:
        result = await universal_bridge.invoke_tool(tool_call.name, tool_call.arguments)
        return MCPResponse.text(result)
    except ValueError as e:
        return MCPResponse.error(str(e))
    except Exception as e:
        logger.exception(f"Error invocando herramienta {tool_call.name}: {e}")
        return MCPResponse.error(f"Tool execution failed: {str(e)}")

if __name__ == "__main__":
    _host = os.getenv("SERVICE_HOST", "127.0.0.1")
    _port = int(os.getenv("SERVICE_PORT", "8001"))
    uvicorn.run(app, host=_host, port=_port)
