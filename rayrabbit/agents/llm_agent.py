"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
"""
LLMAgent - Agente integrado con modelos de lenguaje
"""

import os
import re
import json
import time
import asyncio
import inspect
from typing import Dict, Optional, List, cast, Any, Union

from .simple_agent import SimpleAgent
from ..communication.message import Message, MessageType
from ..communication.payload import UniversalPayloadUnwrapper
from ..utils.exceptions import RayRabbitError
from ..utils.logger import get_logger

class LLMAgent(SimpleAgent):
    """
    Agente integrado con modelos de lenguaje, con soporte multi-proveedor vía LiteLLM.
    """
    
    def __init__(self, agent_id: str, name: str, model: str = "gpt-4o",
                 api_key: Optional[str] = None, capabilities: Optional[List[str]] = None, **kwargs: Any):
        
        description = kwargs.pop("description", "LLM Agent for advanced text processing")
        system_prompt = kwargs.pop("system_prompt", f"Eres {name}, un agente inteligente.")
        
        super().__init__(agent_id, name, description)

        # Dynamic Provider Support via env or args (Key Pooling)
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.api_keys = [self.api_key] if self.api_key else []
        
        # Collect additional keys from LLM_API_KEY_1 to LLM_API_KEY_5
        for i in range(1, 6):
            k = os.getenv(f"LLM_API_KEY_{i}")
            if k and k not in self.api_keys:
                self.api_keys.append(k)
        
        if self.api_keys:
            self.logger.info(f"Soberanía: Pool de claves LLM cargado con {len(self.api_keys)} llaves.")
        
        self.api_base = os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL")
        
        # Default model if nothing is set
        self.model = os.getenv("LLM_MODEL_FULL_NAME") or model or "gpt-4o-mini"
        
        # Override with provider-specific logic ONLY if LLM_MODEL_FULL_NAME is missing
        if not os.getenv("LLM_MODEL_FULL_NAME"):
            provider = os.getenv("LLM_PROVIDER")
            if provider == "ollama":
                self.model = f"ollama/{os.getenv('OLLAMA_MODEL', 'gemma4:e4b')}"
            elif provider == "gemini":
                self.model = f"gemini/{os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')}"

        self.system_prompt = system_prompt
        
        self.llm_config = {
            "temperature": 0.0,
            "max_tokens": 8192,
            "timeout": float(os.getenv("LLM_TIMEOUT", "60.0"))
        }
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.max_history_length = 10
        self.logger = get_logger(f"LLMAgent.{self.name}")
        self._setup_llm_commands()
        self.logger.info(f"LLM Agent inicializado con modelo universal: {self.model}")

    def _setup_llm_commands(self) -> None:
        self.add_command("procesar_texto", self._process_text_command)

    async def handle_message(self, message: Message) -> None:
        """
        Maneja un mensaje entrante, dirigiéndolo a la lógica apropiada.
        """
        if self.system_prompt and "Extrae" in self.system_prompt:
            await self._handle_extraction_task(message)
            return

        content = message.content if isinstance(message.content, dict) else {}
        command = content.get("command")

        if command and command in self.commands:
            handler = self.commands.get(command)
            if handler:
                text = content.get("text", "")
                result = await handler(text)
            else:
                result = {"error": f"Comando desconocido: {command}"}
            response_content = {"response": result, "status": "success"}
            response_type = MessageType.RESPONSE

        else:
            response_msg_obj = await self._handle_request_conversation(message)
            if response_msg_obj and self.message_bus:
                await self.message_bus.publish(response_msg_obj)
            return

        response_message = Message(
            sender_id=self.id,
            sender_name=self.name,
            recipient_id=message.sender_id,
            content=response_content,
            message_type=response_type,
            correlation_id=message.message_id
        )
        if self.message_bus:
            await self.message_bus.publish(response_message)

    async def _handle_request(self, message: Message) -> Optional[Message]:
        if self.system_prompt and "Extrae" in self.system_prompt:
            await self._handle_extraction_task(message)
            return None
        return await self._handle_request_conversation(message)

    async def _handle_extraction_task(self, message: Message) -> None:
        try:
            prompt = message.content.get("prompt") if isinstance(message.content, dict) else str(message.content)
            if not prompt:
                raise ValueError("No se recibió un prompt para la tarea de extracción.")

            llm_response = await self._generate_llm_response(prompt, "extraction_task")
            
            if llm_response:
                match = re.search(r'\b[A-Z0-9]+\b', str(llm_response))
                project_key = match.group(0) if match else str(llm_response).strip()
            else:
                project_key = ""

            if not project_key:
                raise ValueError("El LLM no pudo extraer un project_key válido.")

            if not isinstance(message.content, dict):
                raise TypeError("El contenido del mensaje para la tarea de extracción debe ser un diccionario.")
            
            next_request_content = message.content.copy()
            next_request_content.update({"project_key": project_key})

            next_request = Message(
                sender_id=self.id,
                sender_name=self.name,
                recipient_id="jira_agent",
                content=next_request_content,
                message_type=MessageType.REQUEST,
                correlation_id=message.correlation_id
            )
            
            if self.message_bus:
                await self.message_bus.publish(next_request)
                self.logger.info(f"Tarea de extracción completada. Project key '{project_key}' enviado a {next_request.recipient_id}")

        except Exception as e:
            self.logger.error(f"Error en la tarea de extracción: {e}", exc_info=True)

    async def _handle_request_conversation(self, message: Message) -> Optional[Message]:
        text = message.content.get("text", "") if isinstance(message.content, dict) else ""
        if self._should_use_llm(text):
            try:
                llm_response = await self._generate_llm_response(text, message.sender_id)
                if llm_response:
                    return Message(
                        sender_id=self.id,
                        sender_name=self.name,
                        recipient_id=message.sender_id,
                        content={"text": llm_response, "status": "success"},
                        message_type=MessageType.RESPONSE,
                        correlation_id=message.message_id
                    )
            except Exception as e:
                self.logger.error(f"Error en procesamiento LLM: {e}")
        return await super()._handle_request(message)
        
    def _should_use_llm(self, text: str) -> bool:
        return "?" in text or len(text.split()) > 15
        
    async def _generate_llm_response(self, text: str, user_id: str, tools: Optional[List[Any]] = None) -> Optional[Any]:
        messages = self._prepare_prompt(text, user_id)
        
        # Formatear herramientas si son funciones de Python
        formatted_tools = None
        tool_map = {}
        if tools:
            formatted_tools = []
            for t in tools:
                if hasattr(t, "__name__"):
                    tool_json = self._function_to_tool(t)
                    formatted_tools.append(tool_json)
                    tool_map[t.__name__] = t
                else:
                    # Ya viene formateado
                    formatted_tools.append(t)

        # Bucle de Razonamiento + Acción (Recursividad Soberana Multi-Herramienta)
        max_iterations = 6
        called_tools: set = set()
        react_retries = 0

        # Identificar herramientas cognitivas en el catálogo actual
        cognitive_tool_names = []
        if formatted_tools:
            for t in formatted_tools:
                cat = t.get("category") or t.get("function", {}).get("category", "")
                name = t.get("function", {}).get("name") or t.get("name")
                if cat in ("cognitive", "framework") and name:
                    cognitive_tool_names.append(name)

        for i in range(max_iterations):
            response = await self._call_llm_api(messages, tools=formatted_tools)
            if not response: return None
            
            message = response.choices[0].message
            
            # Convertir a dict para evitar advertencias de PydanticSerializationUnexpectedValue
            msg_dict = message.model_dump(exclude_none=True) if hasattr(message, "model_dump") else dict(message)
            messages.append(msg_dict) # Añadir respuesta del asistente (con o sin tool_calls)
            
            if not hasattr(message, "tool_calls") or not message.tool_calls:
                # No hay más herramientas que llamar: cadena completada
                content = message.content
                if content and user_id != "extraction_task":
                    self._update_conversation_history(user_id, text, content)
                return response if tools else content
            
            # Ejecutar herramientas solicitadas
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                called_tools.add(func_name)
                args_raw = tool_call.function.arguments
                func_args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                
                self.logger.info(f"[SOVEREIGN] Ejecutando herramienta local ({i+1}/{max_iterations}): {func_name}")
                
                result = "Error: Herramienta no encontrada."
                if func_name in tool_map:
                    try:
                        res = tool_map[func_name](**func_args)
                        if inspect.isawaitable(res):
                            result = await res
                        else:
                            result = res
                    except Exception as e:
                        result = f"Error ejecutando {func_name}: {e}"
                else:
                    if hasattr(self, "execute_tool"):
                        try:
                            res = self.execute_tool(func_name, func_args)
                            if inspect.isawaitable(res):
                                result = await res
                            else:
                                result = res
                        except Exception as e:
                            result = f"Error ejecutando {func_name} vía dynamic bridge: {e}"
                
                unwrapped_res = UniversalPayloadUnwrapper.extract_result(result)
                content_str = UniversalPayloadUnwrapper.extract_text(unwrapped_res)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": content_str
                })
        
        return None

    def _function_to_tool(self, func: Any) -> Dict[str, Any]:
        """Convierte una función de Python a formato de herramienta universal (LiteLLM Compatible)."""
        import inspect
        import re
        
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or f"Ejecuta la función {func.__name__}"
        
        # Sanitizar nombre (Anthropic/Gemini prohíben caracteres especiales)
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', func.__name__)
        
        properties = {}
        required = []
        
        for name, param in sig.parameters.items():
            # Descripciones descriptivas (Exigido por Anthropic)
            p_desc = f"Argumento {name} para {clean_name}"
            
            p_type = "string"
            if param.annotation == int: p_type = "integer"
            elif param.annotation == bool: p_type = "boolean"
            elif param.annotation == float: p_type = "number"
            
            properties[name] = {
                "type": p_type,
                "description": p_desc
            }
            if param.default == inspect.Parameter.empty:
                required.append(name)
        
        parameters = {
            "type": "object",
            "properties": properties,
        }
        if required:
            parameters["required"] = required
            
        return {
            "type": "function",
            "function": {
                "name": clean_name,
                "description": doc,
                "parameters": parameters
            }
        }
        
    def _prepare_prompt(self, text: str, user_id: str) -> List[Dict[str, str]]:
        system_prompt = self.system_prompt or f"Eres {self.name}, un agente inteligente."
        
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if user_id != "extraction_task" and user_id in self.conversation_history:
            messages.extend(self.conversation_history[user_id])
        messages.append({"role": "user", "content": text})
        return messages
        
    async def _call_llm_api(self, prompt: List[Dict[str, str]], tools: Optional[List[Any]] = None) -> Any:
        try:
            import litellm
            import random
            
            kwargs_base: Dict[str, Any] = {
                "model": self.model,
                "messages": prompt,
                "temperature": float(self.llm_config["temperature"]),
                "max_tokens": int(self.llm_config["max_tokens"]),
                "timeout": float(self.llm_config["timeout"])
            }
            if self.api_base:
                kwargs_base["api_base"] = self.api_base
            if tools:
                kwargs_base["tools"] = tools

            # Intentos con rotación dinámica ante Rate Limits
            max_retries = min(len(self.api_keys), 3) if self.api_keys else 1
            tried_indices = set()
            
            for attempt in range(max_retries):
                kwargs = kwargs_base.copy()
                
                # Seleccionar clave (aleatoria de las no probadas aún)
                current_api_key = self.api_key
                if self.api_keys:
                    available_indices = [i for i in range(len(self.api_keys)) if i not in tried_indices]
                    if not available_indices: break
                    
                    idx = random.choice(available_indices)
                    tried_indices.add(idx)
                    current_api_key = self.api_keys[idx]
                    self.logger.info(f"[SOVEREIGN] Intento {attempt+1}: Inferencia vía Key Index {idx}")
                
                if current_api_key:
                    kwargs["api_key"] = current_api_key
                
                if tools:
                    kwargs["tool_choice"] = "auto"

                try:
                    self.logger.debug(f"LiteLLM call to {self.model} (Attempt {attempt+1})")
                    response = await litellm.acompletion(**kwargs)
                    return response
                except Exception as e:
                    # Si es error de Rate Limit, reintentar con otra clave
                    error_str = str(e).lower()
                    if "rate_limit" in error_str or "429" in error_str:
                        self.logger.warning(f"[SOVEREIGN] Rate Limit detectado en clave {idx if self.api_keys else 'base'}. Reintentando con otra clave...")
                        continue
                    elif "tool_use_failed" in error_str:
                        self.logger.warning("[SOVEREIGN] Fallo crítico en el uso de herramientas del modelo. Reintentando sin herramientas como fallback...")
                        kwargs.pop("tools", None)
                        kwargs.pop("tool_choice", None)
                        try:
                            response = await litellm.acompletion(**kwargs)
                            return response
                        except Exception as e2:
                            self.logger.error(f"Error en fallback sin herramientas: {e2}")
                            return None
                    else:
                        # Otros errores: reportar y abortar
                        self.logger.error(f"Error en la llamada a la API (LiteLLM): {e}")
                        return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error crítico en la infraestructura de inferencia: {e}", exc_info=True)
            return None

    def _update_conversation_history(self, user_id: str, user_text: str, assistant_response: str) -> None:
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        self.conversation_history[user_id].append({"role": "user", "content": user_text})
        self.conversation_history[user_id].append({"role": "assistant", "content": assistant_response})
        if len(self.conversation_history[user_id]) > self.max_history_length * 2:
            self.conversation_history[user_id] = self.conversation_history[user_id][-(self.max_history_length*2):]
            
    async def _process_text_command(self, text: str) -> str:
        response = await self._generate_llm_response(text, "command_user")
        return str(response) if response else "No se pudo procesar el texto."