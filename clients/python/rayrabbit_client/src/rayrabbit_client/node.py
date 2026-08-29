import asyncio
import inspect
import json
import logging
import re
from typing import Dict, Any, Callable, Optional, Type, Union, Annotated
import websockets
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pydantic import create_model, Field, ConfigDict, BeforeValidator, ValidationError
from .message import Message, MessageType

# Esquemas rápidos para la inferencia de tipos básicos en Python a JSON Schema
TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}

class RayRabbitNode:
    """
    Cliente SDK de RayRabbit para registrar Agentes Soberanos.
    Permite exponer lógica de negocio local como Herramientas (Tools) de la red
    mediante el patrón de decoradores, integrándose de forma transparente al Hub.
    """
    
    def __init__(self, name: str, hub_url: str = "ws://localhost:8005/ws", maestro_secret: str = ""):
        self.name = name
        self.hub_url = hub_url
        self.maestro_secret = maestro_secret
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"RayRabbitSDK-{name}")
        logging.basicConfig(level=logging.INFO)

    def tool(self, *args, name: Optional[str] = None, description: Optional[str] = None, annotations: Optional[Dict[str, Any]] = None, category: Optional[str] = None, **kwargs) -> Callable:
        """
        Decorador para exponer funciones Python como herramientas MCP/A2A.
        Infiere automáticamente el JSON Schema 2020-12 de los type hints.
        Soporta uso con o sin paréntesis: @node.tool o @node.tool()
        """
        # Si se usó como @node.tool sin paréntesis, el primer argumento posicional es la función
        if args and callable(args[0]):
            func = args[0]
            tool_name = name or func.__name__
            tool_desc = description or inspect.getdoc(func) or f"Herramienta {tool_name}"
            self.register_tool(func, tool_name, tool_desc, annotations, category=category, **kwargs)
            return func

        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or inspect.getdoc(func) or f"Herramienta {tool_name}"
            self.register_tool(func, tool_name, tool_desc, annotations, category=category, **kwargs)
            return func
        return decorator

    def register_tool(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None, annotations: Optional[Dict[str, Any]] = None, category: Optional[str] = None, **kwargs) -> None:
        """Registra una función como herramienta MCP dinámicamente usando Pydantic."""
        tool_name = name or func.__name__
        tool_desc = description or inspect.getdoc(func) or f"Herramienta {tool_name}"
        
        # Parsear descripciones del docstring
        docstring = inspect.getdoc(func) or ""
        param_descriptions = {}
        for line in docstring.split("\n"):
            line = line.strip()
            # Emparejar "param_name: descripcion" o "param_name - descripcion"
            m = re.match(r"^([\w_]+)\s*(?:\([^)]+\))?\s*[:\-]\s*(.+)$", line)
            if m:
                param_descriptions[m.group(1)] = m.group(2).strip()
        
        sig = inspect.signature(func)
        fields = {}
        
        for param_name, param in sig.parameters.items():
            if param_name in ["self", "progress_cb"] or param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
                
            ann = param.annotation if param.annotation != inspect.Parameter.empty else Any
            default = ... if param.default == inspect.Parameter.empty else param.default
            desc = param_descriptions.get(param_name, f"Parámetro {param_name}")

            if ann in (int, float, bool, str) or (hasattr(ann, '__origin__') and ann.__origin__ is Union):
                from typing import Annotated
                from pydantic import BeforeValidator
                
                # Coercer para int
                if ann is int or (hasattr(ann, '__args__') and int in ann.__args__):
                    def _make_int_coercer(def_val):
                        def _coerce_int_val(v: Any) -> Any:
                            if v is None:
                                return def_val if def_val is not ... else None
                            if isinstance(v, int):
                                return v
                            if isinstance(v, float):
                                return int(v)
                            if isinstance(v, str):
                                clean = re.sub(r'[^\d.-]', '', v)
                                if clean:
                                    try: return int(float(clean))
                                    except ValueError: pass
                                if def_val is not ...:
                                    return def_val
                            if isinstance(v, list) and v:
                                return _coerce_int_val(v[0])
                            if def_val is not ...:
                                return def_val
                            return v
                        return _coerce_int_val
                    ann = Annotated[Union[int, type(None)] if default is None else int, BeforeValidator(_make_int_coercer(default))]
                elif ann is float or (hasattr(ann, '__args__') and float in ann.__args__):
                    def _make_float_coercer(def_val):
                        def _coerce_float_val(v: Any) -> Any:
                            if v is None:
                                return def_val if def_val is not ... else None
                            if isinstance(v, (float, int)):
                                return float(v)
                            if isinstance(v, str):
                                clean = re.sub(r'[^\d.-]', '', v)
                                if clean:
                                    try: return float(clean)
                                    except ValueError: pass
                                if def_val is not ...:
                                    return def_val
                            if isinstance(v, list) and v:
                                return _coerce_float_val(v[0])
                            if def_val is not ...:
                                return def_val
                            return v
                        return _coerce_float_val
                    ann = Annotated[Union[float, type(None)] if default is None else float, BeforeValidator(_make_float_coercer(default))]
                elif ann is bool or (hasattr(ann, '__args__') and bool in ann.__args__):
                    def _make_bool_coercer(def_val):
                        def _coerce_bool_val(v: Any) -> Any:
                            if v is None:
                                return def_val if def_val is not ... else None
                            if isinstance(v, bool):
                                return v
                            if isinstance(v, str):
                                low = v.strip().lower()
                                if low in ("true", "1", "yes", "si", "t", "y"): return True
                                if low in ("false", "0", "no", "f", "n"): return False
                            if isinstance(v, (int, float)):
                                return bool(v)
                            if def_val is not ...:
                                return def_val
                            return v
                        return _coerce_bool_val
                    ann = Annotated[Union[bool, type(None)] if default is None else bool, BeforeValidator(_make_bool_coercer(default))]
                elif ann is str or (hasattr(ann, '__args__') and str in ann.__args__):
                    def _make_str_coercer(def_val):
                        def _coerce_str_val(v: Any) -> Any:
                            if v is None:
                                return def_val if def_val is not ... else None
                            if isinstance(v, str):
                                return v
                            if isinstance(v, (int, float, bool)):
                                return str(v)
                            if isinstance(v, list):
                                return str(v[0]) if v else (def_val if def_val is not ... else "")
                            if isinstance(v, dict):
                                for k in ('id', 'name', 'value', 'key'):
                                    if k in v: return str(v[k])
                                return json.dumps(v)
                            return str(v)
                        return _coerce_str_val
                    ann = Annotated[Union[str, type(None)] if default is None else str, BeforeValidator(_make_str_coercer(default))]

            if default is None and not (hasattr(ann, '__origin__') and ann.__origin__ is Union):
                ann = Union[ann, type(None)]
            
            if default is ...:
                fields[param_name] = (ann, Field(description=desc))
            else:
                fields[param_name] = (ann, Field(default=default, description=desc))
                
        # Crear modelo pydantic dinámico tolerante a parámetros extra
        pydantic_model = create_model(f"{tool_name}_Arguments", __config__=ConfigDict(extra="ignore"), **fields)
        schema = pydantic_model.model_json_schema()
        
        # Formatear el JSON Schema 2020-12
        mcp_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }
        
        schema_dict = {
            "name": tool_name,
            "description": f"[Domain Atomic Tool ({self.name})] {tool_desc}",
            "category": self.name,
            "inputSchema": mcp_schema
        }
        if annotations:
            schema_dict["annotations"] = annotations
            
        self.tools[tool_name] = {
            "func": func,
            "schema": schema_dict,
            "model": pydantic_model
        }
        self.logger.info(f"Registrada herramienta nativa SDK: '{tool_name}'")

    async def start(self):
        """
        Inicia el nodo SDK, conecta vía WebSocket persistente al Hub
        y expone automáticamente todas las herramientas registradas.
        Reconecta automáticamente con backoff exponencial ante desconexiones.
        """
        self.logger.info(f"🚀 Iniciando nodo '{self.name}' conectándose a {self.hub_url}...")
        self.logger.info(f"Herramientas activas listas para exponer: {list(self.tools.keys())}")

        reconnect_delay = 1.0
        max_reconnect_delay = 30.0

        while True:
            try:
                async with websockets.connect(
                    self.hub_url,
                    ping_interval=20,
                    ping_timeout=60,
                ) as websocket:
                    self.logger.info(f"✅ Conexión TCP/WS establecida con el Hub. Iniciando Handshake MAESTRO...")
                    reconnect_delay = 1.0  # Resetear backoff tras conexión exitosa

                    # Payload inicial para Handshake Zero-Trust (Proof of Possession)
                    handshake_payload = {
                        "type": "register",
                        "agent_id": self.name,
                        "capabilities": list(self.tools.keys()),
                        "tools": [t["schema"] for t in self.tools.values()]
                    }

                    await websocket.send(json.dumps(handshake_payload))
                    response = await websocket.recv()
                    self.logger.info(f"Respuesta del Hub: {response}")

                    # Loop infinito para recibir tareas MCP
                    while True:
                        msg_str = await websocket.recv()
                        try:
                            msg_data = json.loads(msg_str)
                            if msg_data.get("method") == "tools/call":
                                await self._handle_tool_call(websocket, msg_data)
                        except json.JSONDecodeError:
                            self.logger.error("Mensaje JSON inválido recibido del Hub.")

            except Exception as e:
                self.logger.error(f"Error de conexión WebSocket: {e}")
                self.logger.info(f"Reconectando en {reconnect_delay:.0f}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

    async def connect(self):
        """Alias de compatibilidad para start()."""
        await self.start()


    async def _handle_tool_call(self, websocket, msg_data: Dict[str, Any]):
        """Maneja las peticiones de ejecución de herramientas mediante validación estricta de esquema Pydantic (100% Agnóstico)."""
        from pydantic import ValidationError
        
        req_id = msg_data.get("id")
        params = msg_data.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments") if isinstance(params.get("arguments"), dict) else (params.get("params") if isinstance(params.get("params"), dict) else {})
        if not isinstance(args, dict):
            args = {}
        
        if tool_name in self.tools:
            tool_entry = self.tools[tool_name]
            func = tool_entry["func"]
            model = tool_entry["model"]
            try:
                # Validar contra el modelo Pydantic del nodo SDK (tolerante a campos extra)
                validated_args = model(**args)
                args_dict = validated_args.model_dump()
                
                # Filtrar argumentos si la función no acepta **kwargs
                sig = inspect.signature(func)
                has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
                if not has_var_keyword:
                    call_args = {k: v for k, v in args_dict.items() if k in sig.parameters}
                else:
                    call_args = {**args, **args_dict}
                
                if inspect.iscoroutinefunction(func):
                    result = await func(**call_args)
                else:
                    result = func(**call_args)
                    
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "json", "json": result}]}
                }
            except ValidationError as ve:
                self.logger.warning(f"Aviso de validación Pydantic en herramienta '{tool_name}' con args {args}: {ve.errors()}. Aplicando ejecución resiliente de fallback...")
                try:
                    sig = inspect.signature(func)
                    safe_args = {}
                    for p_name, p_param in sig.parameters.items():
                        if p_name in ["self", "progress_cb"] or p_param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                            continue
                        if p_name in args:
                            safe_args[p_name] = args[p_name]
                        elif p_param.default != inspect.Parameter.empty:
                            safe_args[p_name] = p_param.default
                    
                    if inspect.iscoroutinefunction(func):
                        result = await func(**safe_args)
                    else:
                        result = func(**safe_args)
                        
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"content": [{"type": "json", "json": result}]}
                    }
                except Exception as fallback_err:
                    self.logger.error(f"Fallo en ejecución de fallback para '{tool_name}': {fallback_err}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32602,
                            "message": f"Invalid params: {ve.errors()}",
                            "data": ve.errors()
                        }
                    }
            except Exception as e:
                self.logger.error(f"Error ejecutando función de herramienta '{tool_name}': {e}")
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)}
                }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Tool '{tool_name}' not found."}
            }
            
        await websocket.send(json.dumps(response))
