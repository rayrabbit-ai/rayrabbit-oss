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
SovereignA2UIAgent - Clase base para agentes con capacidades de UI A2UI.
Implementa el protocolo A2UI v0.9.1 de forma nativa en RayRabbit OSS.
"""

from typing import Dict, Any, List, Optional
from ...agents.llm_agent import LLMAgent
from ...communication.message import Message, MessageType
from .generator import A2UIGenerator
from .validator import A2UIValidator
from .schema.manager import A2uiSchemaManager
import os
import re
import json
import uuid
import asyncio
from pathlib import Path

class SovereignA2UIAgent(LLMAgent):
    """
    Extensión Sovereign del Agente base para soportar A2UI con RAZONAMIENTO REAL (LLMs/Ollama).
    Gestiona el ciclo de vida de la superficie, la seguridad JWS y la generación dinámica de UI.
    Hereda de LLMAgent para soportar Inferencia Híbrida universal.
    """
    
    def __init__(self, agent_id: str, name: str, description: str = ""):
        # LLMAgent handles LLM_PROVIDER, OLLAMA_BASE_URL, LLM_API_KEY internally
        super().__init__(agent_id=agent_id, name=name, description=description)
        
        self.generator = A2UIGenerator()
        self.validator = A2UIValidator()
        self.active_surfaces: Dict[str, str] = {} # surface_id -> catalog_id
        self._ui_subscribers = set() # OSS: Para soporte SSE (stream_ui_events)
        
        self.schema_manager = A2uiSchemaManager("0.10")
        self.supported_components = ["Text", "Image", "Card", "Button", "Column", "Row", "Icon", "Divider"]
        
        # Inyectar System Prompt Dinámico (Schema) a la propiedad base del LLMAgent
        self.system_prompt = self._load_a2ui_skill()
        
        # Registrar handler para acciones de usuario de A2UI (Paso 6 del Flow E2E)
        self.register_message_handler(MessageType.REQUEST, self._handle_a2ui_request)

    def get_a2ui_tools(self, correlation_id: Optional[str] = None) -> List[Any]:
        """Retorna las herramientas nativas A2UI. Sobrescribir en subclases."""
        return []

    def _load_a2ui_skill(self) -> str:
        """Carga el manual y los ESQUEMAS NATIVOS usando el SchemaManager."""
        try:
            skill_text = ""
            skill_path = Path(__file__).parent / "a2ui_skill.md"
            if skill_path.exists():
                skill_text = skill_path.read_text(encoding="utf-8")
                # Depuración dinámica: Omitir la sección de catálogo estático para ahorrar tokens
                if "## 🏗️ Standard Catalog (v0.9.1)" in skill_text and "## 🧠 Logic & Formatting Functions" in skill_text:
                    parts = skill_text.split("## 🏗️ Standard Catalog (v0.9.1)")
                    first_part = parts[0]
                    second_part = parts[1].split("## 🧠 Logic & Formatting Functions", 1)[1]
                    skill_text = first_part + "## 🧠 Logic & Formatting Functions" + second_part
            else:
                skill_text = "Eres el RayRabbit A2UI Assistant v0.9.1. Genera siempre JSON válido."

            return self.schema_manager.generate_system_prompt(
                role_description=skill_text,
                allowed_components=self.supported_components,
                include_schema=True
            )
        except Exception as e:
            self.logger.error(f"Error cargando skill via SchemaManager: {e}")
            return "Eres el RayRabbit A2UI Assistant v0.9.1. Genera siempre JSON válido."

    async def _handle_a2ui_request(self, message: Message):
        """Maneja solicitudes que podrían ser acciones de A2UI."""
        content = message.content
        if isinstance(content, dict) and "action" in content:
            await self.handle_a2ui_action(content["action"], message)
        else:
            await self._handle_request(message)

    async def handle_a2ui_action(self, action: Any, original_message: Message):
        if isinstance(action, str):
            self.logger.info(f"Recibida acción A2UI (string): {action}")
        else:
            self.logger.info(f"Recibida acción A2UI: {action.get('name') or action.get('action') or action.get('id')}")

    async def send_a2ui_message(self, recipient_id: str, payload: Dict[str, Any], correlation_id: Optional[str] = None):
        if not self.validator.validate_message(payload):
            self.logger.error(f"A2UI: El mensaje no cumple con la especificación v0.9.1. Abortando envío.")
            return

        metadata = {}
        if self.maestro:
            try:
                jws_token = self.maestro.sign_message(payload)
                metadata["jws"] = jws_token
                self.logger.debug(f"A2UI: Mensaje firmado con JWS para {recipient_id}")
            except Exception as e:
                self.logger.error(f"A2UI: Error al firmar mensaje con JWS: {e}")

        if hasattr(self, '_ui_subscribers'):
            for q in self._ui_subscribers:
                await q.put(payload)

        msg = Message(
            sender_id=self.id,
            sender_name=self.name,
            recipient_id=recipient_id,
            message_type=MessageType.EVENT,
            content=payload,
            correlation_id=correlation_id or str(uuid.uuid4()),
            metadata=metadata
        )
        
        if self.message_bus:
            await self.publish_message(msg)
        else:
            await self._relay_to_hub(msg)
    
    async def _broadcast_working_state(self, correlation_id: Optional[str]):
        working_msg = Message(
            sender_id=self.id,
            sender_name=self.name,
            recipient_id="a2ui_client",
            message_type=MessageType.EVENT,
            correlation_id=correlation_id,
            content={
                "type": "agent_status",
                "status": "working",
                "message": "Consultando sistemas de monitoreo federados..."
            }
        )
        if self.message_bus:
            await self.publish_message(working_msg)
        else:
            await self._relay_to_hub(working_msg)

    async def _relay_to_hub(self, message: Message):
        import httpx
        hub_url = os.environ.get("RAYRABBIT_HUB_URL", "http://127.0.0.1:8005")
        relay_endpoint = f"{hub_url.rstrip('/')}/api/publish-message"
        
        payload = {
            "sender_id": message.sender_id,
            "sender_name": message.sender_name,
            "recipient_id": message.recipient_id,
            "message_type": message.message_type.value,
            "correlation_id": message.correlation_id,
            "content": message.content if isinstance(message.content, dict) else {"data": message.content}
        }
        
        headers = {}
        if self.maestro:
            try:
                headers = self.maestro.get_jws_headers(payload, correlation_id=message.correlation_id)
            except Exception as e:
                self.logger.warning(f"A2UI: No se pudo firmar relay con JWS: {e}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(relay_endpoint, json=payload, headers=headers)
                if response.status_code != 200:
                    self.logger.warning(f"A2UI: Fallo relay al Hub: {response.status_code}")
        except Exception as e:
            self.logger.error(f"A2UI: Error relay HTTP al Hub: {repr(e)}")

    async def send_begin_rendering(self, recipient_id: str, surface_id: str, root_id: str, catalog_id: str = A2UIGenerator.DEFAULT_CATALOG_ID, styles: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None):
        payload = self.generator.begin_rendering(surface_id, catalog_id)
        await self.send_a2ui_message(recipient_id, payload, correlation_id)
        self.active_surfaces[surface_id] = catalog_id

    async def send_surface_update(self, recipient_id: str, surface_id: str, components: List[Dict[str, Any]], correlation_id: Optional[str] = None):
        payload = self.generator.surface_update(surface_id, components)
        await self.send_a2ui_message(recipient_id, payload, correlation_id)

    async def send_data_update(self, recipient_id: str, surface_id: str, key: str, value: Any, path: str = "/", correlation_id: Optional[str] = None):
        full_path = f"{path.rstrip('/')}/{key}" if key else path
        payload = self.generator.update_data_model(surface_id, value, full_path)
        await self.send_a2ui_message(recipient_id, payload, correlation_id)

    async def broadcast_a2ui(self, payload: Dict[str, Any], correlation_id: Optional[str] = None):
        await self.send_a2ui_message("a2ui_client", payload, correlation_id)

    async def stream_ui_events(self):
        queue = asyncio.Queue()
        self._ui_subscribers.add(queue)
        try:
            while True:
                payload = await queue.get()
                yield f"data: {json.dumps(payload)}\n\n"
        finally:
            self._ui_subscribers.remove(queue)

    async def reason_ui_generation(self, user_query: str, context: str = "", correlation_id: Optional[str] = None, tools: Optional[List[Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Utiliza IA Híbrida de Dos Fases para generar la UI basándose en el input y contexto.

        Fase 1 (Resolución de Datos): Invoca el LLM con las herramientas disponibles para
        recuperar y condensar datos reales del sistema. Evita colisionar con el formato A2UI.

        Fase 2 (Composición Gráfica): Invoca el LLM con tools=None para que LiteLLM NO
        inyecte el prompt de function-calling, eliminando la colisión con las instrucciones
        de salida JSON del protocolo A2UI v0.9.1.
        """
        self.current_correlation_id = correlation_id
        if asyncio.iscoroutinefunction(self.get_a2ui_tools):
            native_tools = await self.get_a2ui_tools(correlation_id=correlation_id)
        else:
            native_tools = self.get_a2ui_tools(correlation_id=correlation_id)
            if asyncio.iscoroutine(native_tools):
                native_tools = await native_tools
        effective_tools = tools if tools is not None else native_tools

        # Feedback visual inicial
        await self._broadcast_working_state(correlation_id)

        resolved_context = context

        # --- FASE 1: RESOLUCIÓN DE DATOS (TOOL CALLING) ---
        if effective_tools:
            self.logger.info("[A2UI] Fase 1: Resolviendo datos del sistema (Tool Calling)...")
            tool_prompt = (
                f"Analiza la consulta del usuario y el contexto actual.\n"
                f"1. Si la consulta solicita una acción o dato de dominio (ej. consultar precio, rastrear paquete, leer archivo), DEBES invocar la herramienta de dominio MCP correspondiente.\n"
                f"2. Si la consulta involucra una etapa cognitiva o deliberativa de framework (CrewAI, AutoGen, LangChain), invoca la herramienta cognitiva asignada a la etapa activa.\n"
                f"3. Si es una consulta general o conversacional que no requiere herramientas, no invoques herramientas innecesarias.\n"
                f"Consulta del usuario: {user_query}\n"
                f"Contexto: {context or 'Sin contexto.'}"
            )
            tool_response_obj = await self._generate_llm_response(tool_prompt, "a2ui_tools_resolver", tools=effective_tools)
            if tool_response_obj:
                tool_summary = ""
                if isinstance(tool_response_obj, str):
                    tool_summary = tool_response_obj
                elif hasattr(tool_response_obj, "choices"):
                    tool_summary = tool_response_obj.choices[0].message.content or ""
                else:
                    tool_summary = str(tool_response_obj)
                if tool_summary:
                    resolved_context = f"{context}\n\n[Datos recuperados de herramientas]:\n{tool_summary}"
            self.logger.info("[A2UI] Fase 1 completada. Contexto enriquecido con datos reales.")

        # --- FASE 2: COMPOSICIÓN GRÁFICA (A2UI JSON, tools=None) ---
        self.logger.info("[A2UI] Fase 2: Generando representación gráfica A2UI (tools=None)...")
        use_case = getattr(self, "current_use_case", "default")
        prompt = f'''User Input: {user_query}

Contexto Transaccional Vivo (EVENTOS REALES DEL SISTEMA):
{resolved_context or 'Sin contexto.'}

Workspace Activo: {use_case}

INSTRUCCIONES CRÍTICAS DE UI DINÁMICA:
1. Eres el **RayRabbit A2UI Agent**. Los datos arriba son HECHOS REALES.
2. **AISLAMIENTO DE CONTEXTO**: Debes generar narrativas, layouts y comandos A2UI que pertenezcan estrictamente al Workspace Activo actual: '{use_case}'. No mezcles terminología, datos, ni componentes de otros workspaces o casos de uso.
3. **REEMPLAZO DE DASHBOARD**: Si el contexto menciona una entidad (ej. un pedido, un dato financiero) o un proceso, DEBES enviar un `surfaceUpdate` que reemplace el contenido principal.
4. **ACTUALIZA EL DASHBOARD CON CARDS**: Si la pantalla actual es un dashboard de bienvenida o inicial, cámbialo a una vista activa y detallada con componentes visuales enriquecidos (usa `Card` con `variant="glass"`, `Text`, etc.) en lugar de texto simple.
5. **ESTADO DE TAREAS Y BOTONES DE ACCIÓN**: Genera componentes de estado claros e interactivos según el contexto. Si el flujo requiere interacción o confirmación paso a paso (ej. etapas posteriores pendientes), DEBES generar e incluir OBLIGATORIAMENTE el botón interactivo de acción (`Button` con `variant="primary"`, `action={{"name": "userAction", "id": "step_action"}}`, `label={{"path": "/buttons/step_action/label"}}` y `disabled={{"path": "/buttons/step_action/disabled"}}`). Si la operación ya concluyó todas sus etapas finales, presenta el estado consolidado de cierre sin botones redundantes.
6. **SEPARACIÓN DE RESPONSABILIDADES Y TASKENGINE**: Mantén siempre una clara separación visual entre el bloque de **Orquestación de Pipeline Agéntico** (visión global de negocio) y el bloque de **TaskEngine — Gestor de ciclo de vida de tareas asíncronas** (telemetría de pasos técnicos con ProgressBar y badges).
7. **NARRATIVA EN LENGUAJE NATURAL OBLIGATORIA**: En el campo 'narrative', debes redactar SIEMPRE una respuesta fluida, elegante y ejecutiva en lenguaje natural en Markdown dirigida al usuario, explicando de forma concisa qué operaciones se realizaron y el estado actual. PROHIBIDO TERMINANTEMENTE incluir estructuras JSON crudas, fragmentos de código JSON, dumps técnicos de diccionarios o repetir el texto del prompt del usuario.
8. Responde OBLIGATORIAMENTE como un OBJETO JSON con la siguiente estructura exacta:
```json
{{
  "narrative": "Tu explicación conversacional y ejecutiva en lenguaje natural aquí...",
  "a2ui": [ ...comandos v0.9.1 beginRendering, surfaceUpdate, updateDataModel... ]
}}
```'''

        # Fase 2: tools=None explícito — LiteLLM no inyectará prompt de function-calling
        response_obj = await self._generate_llm_response(prompt, "a2ui_reasoning", tools=None)

        text = ""
        if isinstance(response_obj, str):
            text = response_obj
        elif hasattr(response_obj, "choices"):
            text = response_obj.choices[0].message.content or ""
        else:
            text = str(response_obj)

        if not text:
            return None

        # Guardar únicamente la narrativa en el historial L2 (Memoria conversacional limpia)
        narrative_to_save = text
        try:
            narrative_match = re.search(r'"narrative":\s*"(.*?)"', str(text), re.DOTALL)
            if narrative_match:
                narrative_to_save = narrative_match.group(1).replace("\\n", "\n")
        except: pass

        self._update_conversation_history("a2ui_reasoning", user_query, narrative_to_save)

        # Structural Agnostic Parser (Agnosticismo Total)
        data = self._extract_json_structurally(text)
        
        if not data:
            self.logger.warning(f"A2UI: No se pudo extraer estructura JSON válida del modelo {self.model}")
            return None

        try:
            
            narrative = ""
            raw_commands = []
            
            if isinstance(data, dict):
                # Mayor resiliencia en la detección de claves de narrativa
                for k in ["narrative", "text", "response", "message", "content", "summary"]:
                    if k in data and isinstance(data[k], str) and data[k].strip():
                        narrative = data[k]
                        break
                raw_commands = data.get("a2ui", [])
                if not raw_commands and any(k in data for k in ["beginRendering", "updateDataModel", "surfaceUpdate"]):
                    raw_commands = [data]
            elif isinstance(data, list):
                raw_commands = data

            # Fallback de rendimiento: si la narrativa está vacía, extraemos texto fuera del bloque JSON
            if not narrative and text:
                clean_text = text
                json_start = text.find('{')
                json_end = text.rfind('}')
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    clean_text = text[:json_start] + text[json_end+1:]
                
                # Remover marcas de markdown
                clean_text = re.sub(r'```(?:json)?\s*```', '', clean_text, flags=re.DOTALL)
                clean_text = re.sub(r'```', '', clean_text)
                clean_text = clean_text.strip()
                if clean_text:
                    narrative = clean_text

            if not narrative or narrative.strip() == "Aquí tienes la información solicitada:":
                narrative = "He procesado la fase actual de la solicitud. Las tareas están siendo coordinadas a través del TaskEngine y la memoria L3. Puedes revisar los detalles en el panel interactivo e interactuar con el botón de acción para continuar."

            final_commands = []
            standard_surface = getattr(self, "surface_id", None) or "universal_dashboard"

            has_narrative_cmd = any(
                cmd.get("updateDataModel", {}).get("path") == "/narrative" 
                for cmd in raw_commands if isinstance(cmd, dict)
            )

            if narrative and not has_narrative_cmd:
                final_commands.append({
                    "version": "v0.9.1",
                    "updateDataModel": {
                        "surfaceId": standard_surface,
                        "path": "/narrative",
                        "value": narrative
                    }
                })

            for cmd in raw_commands:
                if not isinstance(cmd, dict): continue
                if "version" not in cmd: cmd["version"] = "v0.9.1"
                
                for key in ["beginRendering", "surfaceUpdate", "updateDataModel"]:
                    if key in cmd and isinstance(cmd[key], dict):
                        if "surfaceId" not in cmd[key] or cmd[key]["surfaceId"] != standard_surface:
                            cmd[key]["surfaceId"] = standard_surface

                if "beginSurface" in cmd: cmd["beginRendering"] = cmd.pop("beginSurface")
                if "renderSurface" in cmd: cmd["beginRendering"] = cmd.pop("renderSurface")
                if "dataModelUpdate" in cmd: cmd["updateDataModel"] = cmd.pop("dataModelUpdate")
                final_commands.append(cmd)

            surface_cmds = [c for c in final_commands if "surfaceUpdate" in c]
            data_cmds = [c for c in final_commands if "updateDataModel" in c]
            render_cmds = [c for c in final_commands if "beginRendering" in c]
            other_cmds = [c for c in final_commands if not any(k in c for k in ["surfaceUpdate", "updateDataModel", "beginRendering"])]

            # Inyectar / Preservar Scaffold Estructural A2UI (TaskEngine + Action Button)
            for cmd in surface_cmds:
                update_obj = cmd.get("surfaceUpdate", {})
                components = update_obj.get("components", [])
                if isinstance(components, list):
                    comp_map = {c.get("id"): c for c in components if isinstance(c, dict) and "id" in c}

                    # 1. Identificar si el LLM ya incluye un botón interactivo y mapear todas las dependencias
                    referenced_children = set()
                    has_user_button = False

                    for c in components:
                        if not isinstance(c, dict):
                            continue
                        comp_body = c.get("component", {})
                        if isinstance(comp_body, dict):
                            for ctype, props in comp_body.items():
                                if ctype == "Button":
                                    has_user_button = True
                                    if isinstance(props, dict):
                                        if not props.get("disabled"):
                                            props["disabled"] = {"path": "/buttons/step_action/disabled"}
                                        if not props.get("label"):
                                            props["label"] = {"path": "/buttons/step_action/label"}
                                        if not props.get("action"):
                                            props["action"] = {"name": "userAction", "id": "step_action"}
                                if isinstance(props, dict):
                                    child = props.get("child")
                                    if isinstance(child, str):
                                        referenced_children.add(child)
                                    children = props.get("children")
                                    if isinstance(children, list):
                                        for ch_id in children:
                                            if isinstance(ch_id, str):
                                                referenced_children.add(ch_id)

                    # 2. Definiciones de componentes del Scaffold del Sistema
                    scaffold_defs = [
                        {
                            "id": "task-engine-card",
                            "component": {
                                "Card": {
                                    "variant": "flat",
                                    "children": ["task-engine-header-row", "task-progress-bar", "pipeline-status"]
                                }
                            }
                        },
                        {
                            "id": "task-engine-header-row",
                            "component": {
                                "Row": {
                                    "align": "center",
                                    "justify": "spaceBetween",
                                    "children": ["task-engine-title", "task-engine-badge"]
                                }
                            }
                        },
                        {
                            "id": "task-engine-title",
                            "component": {
                                "Text": {
                                    "text": {"literalString": "⚙️ TaskEngine — Gestor de ciclo de vida de tareas asíncronas"},
                                    "variant": "caption"
                                }
                            }
                        },
                        {
                            "id": "task-engine-badge",
                            "component": {
                                "Text": {
                                    "text": {"path": "/task_status"},
                                    "variant": "badge badge-running"
                                }
                            }
                        },
                        {
                            "id": "task-progress-bar",
                            "component": {
                                "ProgressBar": {
                                    "progress": {"path": "/task_progress"}
                                }
                            }
                        },
                        {
                            "id": "pipeline-status",
                            "component": {
                                "Text": {
                                    "text": {"path": "/task_status"},
                                    "variant": "body"
                                }
                            }
                        }
                    ]

                    # Determinar si el flujo completó al 100% para no inyectar botón huérfano
                    is_flow_completed = False
                    for d_cmd in data_cmds:
                        if isinstance(d_cmd, dict) and "updateDataModel" in d_cmd:
                            udm = d_cmd["updateDataModel"]
                            if udm.get("path") == "/task_progress" and udm.get("value") == 100:
                                is_flow_completed = True

                    should_render_button = (not has_user_button) and (not is_flow_completed)

                    # Solo inyectar action-zone-card si el LLM no generó ningún botón y el flujo sigue activo
                    if should_render_button:
                        scaffold_defs.extend([
                            {
                                "id": "action-zone-card",
                                "component": {
                                    "Card": {
                                        "variant": "glass",
                                        "children": ["action-btn-row"]
                                    }
                                }
                            },
                            {
                                "id": "action-btn-row",
                                "component": {
                                    "Row": {
                                        "align": "center",
                                        "justify": "center",
                                        "children": ["step-action-btn"]
                                    }
                                }
                            },
                            {
                                "id": "step-action-btn",
                                "component": {
                                    "Button": {
                                        "variant": "primary",
                                        "action": {
                                            "name": "userAction",
                                            "id": "step_action"
                                        },
                                        "disabled": {"path": "/buttons/step_action/disabled"},
                                        "label": {"path": "/buttons/step_action/label"}
                                    }
                                }
                            }
                        ])
                        data_cmds.append({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": standard_surface,
                                "path": "/buttons/step_action/disabled",
                                "value": False
                            }
                        })
                        data_cmds.append({
                            "version": "v0.9.1",
                            "updateDataModel": {
                                "surfaceId": standard_surface,
                                "path": "/buttons/step_action/label",
                                "value": "► Continuar a la Siguiente Fase"
                            }
                        })

                    for s_comp in scaffold_defs:
                        cid = s_comp["id"]
                        if cid not in comp_map:
                            components.append(s_comp)
                            comp_map[cid] = s_comp

                    # 3. Calcular los nodos raíz reales (aquellos que no son hijos de nadie)
                    scaffold_internal_ids = {
                        "task-engine-header-row", "task-engine-title", "task-engine-badge",
                        "task-progress-bar", "pipeline-status", "action-btn-row", "step-action-btn",
                        "task-engine-card", "action-zone-card", "root"
                    }

                    true_roots = [
                        c["id"] for c in components
                        if isinstance(c, dict) and "id" in c
                        and c["id"] not in referenced_children
                        and c["id"] not in scaffold_internal_ids
                    ]

                    root_comp = comp_map.get("root")
                    if root_comp and isinstance(root_comp.get("component"), dict):
                        root_inner = root_comp["component"]
                        for container_type in ["Column", "Row", "Box", "Container"]:
                            if container_type in root_inner and isinstance(root_inner[container_type], dict):
                                ch = root_inner[container_type].get("children", [])
                                if isinstance(ch, list):
                                    # Limpiar para evitar duplicados
                                    ch = [cid for cid in ch if cid not in ("task-engine-card", "action-zone-card")]
                                    if ch:
                                        new_ch = [ch[0], "task-engine-card"] + ch[1:]
                                    else:
                                        new_ch = ["task-engine-card"]
                                    if should_render_button:
                                        new_ch.append("action-zone-card")
                                    root_inner[container_type]["children"] = new_ch
                    else:
                        if true_roots:
                            root_children = [true_roots[0], "task-engine-card"] + true_roots[1:]
                        else:
                            root_children = ["task-engine-card"]
                        if should_render_button and "action-zone-card" not in root_children:
                            root_children.append("action-zone-card")
                        root_comp = {
                            "id": "root",
                            "component": {
                                "Column": {
                                    "children": root_children
                                }
                            }
                        }
                        comp_map["root"] = root_comp
                        components.append(root_comp)

                    # 4. Reordenar para que 'root' esté siempre en el índice 0 para el renderer
                    ordered_components = [comp_map["root"]] + [c for c in components if c.get("id") != "root"]
                    update_obj["components"] = ordered_components

            if (surface_cmds or data_cmds) and not render_cmds:
                render_cmds.append({
                    "version": "v0.9.1",
                    "beginRendering": {
                        "surfaceId": standard_surface,
                        "catalogId": "standard"
                    }
                })

            for cmd in surface_cmds + data_cmds + other_cmds:
                await self.broadcast_a2ui(cmd, correlation_id=correlation_id)
            
            for cmd in render_cmds:
                await self.broadcast_a2ui(cmd, correlation_id=correlation_id)
            
            return final_commands

        except Exception as e:
            self.logger.error(f"Error procesando JSON (LLM): {e}")
            return None

    def _extract_json_structurally(self, text: str) -> Optional[Any]:
        """
        Structural Agnostic Parser: Extrae el bloque JSON balanceado más externo y válido.
        Prioriza la estructura que contiene el mayor número de caracteres válidos.
        """
        if not text: return None
        
        # 1. Limpiar marcas de markdown
        text = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL).strip()
        
        candidates = []
        
        # 2. Búsqueda de balance estructural (Outer-to-Inner)
        for start_char in ['{', '[']:
            start_idx = text.find(start_char)
            while start_idx != -1:
                end_char = '}' if start_char == '{' else ']'
                end_idx = text.rfind(end_char)
                while end_idx > start_idx:
                    candidate = text[start_idx:end_idx+1]
                    try:
                        # Dirty JSON Repair (Eliminar comas finales)
                        candidate_repaired = re.sub(r',\s*([\]}])', r'\1', candidate)
                        # Comentarios de línea
                        candidate_repaired = re.sub(r'//.*', '', candidate_repaired)
                        
                        obj = json.loads(candidate_repaired)
                        candidates.append((len(candidate), obj))
                        break # Encontró el más grande para este start_idx
                    except:
                        end_idx = text.rfind(end_char, start_idx, end_idx)
                start_idx = text.find(start_char, start_idx + 1)
        
        if not candidates:
            return None
            
        # Retornar el objeto que abarque la mayor cantidad de texto (el más externo)
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
