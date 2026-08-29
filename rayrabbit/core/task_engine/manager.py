"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.
SPDX-License-Identifier: AGPL-3.0-only
"""
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Awaitable
from .store import TaskStore
from ...communication.message import Message, MessageType
from ...utils.logger import get_logger
from ...core.agent import Agent, AgentStatus

class TaskPolicyEngine:
    """
    Motor de políticas de MAESTRO para validar identidades, scopes, tenant isolation
    y autorizar transiciones de tareas.
    """
    def __init__(self, security_module: Any = None):
        self.security = security_module
        # Allowlist de workers: key = worker_id, value = list of capabilities/task_types
        self.worker_allowlist: Dict[str, List[str]] = {
            "default_worker": ["default", "tool_call", "a2ui", "task_execution", "*"],
            "universal_a2ui_agent": ["default", "tool_call", "a2ui", "task_execution", "*"]
        }

    def register_worker(self, worker_id: str, capabilities: List[str]):
        """Registra un worker en la lista blanca con sus capacidades."""
        self.worker_allowlist[worker_id] = capabilities

    def authorize_action(self, action: str, actor_id: str, task_state: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        """
        Valida si el actor_id tiene autorización para realizar la acción sobre la tarea.
        Acciones: "create", "accept", "update", "cancel", "get", "list", "watch"
        """
        task = task_state.get("task", {})
        task_tenant = task.get("tenant_id")
        
        # 1. Tenant Isolation y validación proactiva de Capabilities en la Creación
        if action == "create":
            task_type = payload.get("type", "default")
            has_worker = False
            for w_id, caps in self.worker_allowlist.items():
                if "*" in caps or task_type in caps:
                    has_worker = True
                    break
            if not has_worker:
                return False

        # El Hub o TaskManager central siempre están autorizados a enrutar una vez validado
        if actor_id in ("task_manager", "hub_mcp", "web_ui_bridge"):
            return True

        # 2. Allowlist de Workers por Capability
        if action == "accept":
            allowed_caps = self.worker_allowlist.get(actor_id, [])
            task_payload = payload.get("payload", {}) if "payload" in payload else payload
            task_type = task_payload.get("type", "default")
            if "*" not in allowed_caps and task_type not in allowed_caps:
                return False

        # 3. Bloqueo de Cancelaciones o Actualizaciones no autorizadas
        if action in ("cancel", "update"):
            # Solo el creador original o un agente del mismo tenant puede alterar la tarea
            if task_tenant and hasattr(payload, "get") and payload.get("tenant_id") and payload.get("tenant_id") != task_tenant:
                return False

        return True


class TaskManager:
    """
    Gestiona la creación de tareas, el enrutamiento inicial y las consultas de estado.
    """
    def __init__(self, message_bus: Any, store: TaskStore, tenant_id: str = "default"):
        self.bus = message_bus
        self.store = store
        self.tenant_id = tenant_id
        self.logger = get_logger("TaskManager")
        self.policy_engine = TaskPolicyEngine(getattr(message_bus, "security_module", None))
        self.approval_events: Dict[str, asyncio.Event] = {}
        self.approval_inputs: Dict[str, Any] = {}

    async def create_task(self, payload: Dict[str, Any], parent_task_id: Optional[str] = None, correlation_id: Optional[str] = None) -> str:
        """Crea una nueva tarea, la persiste y emite el evento task.created."""
        task_id = str(uuid.uuid4())
        corr_id = correlation_id or str(uuid.uuid4())
        
        # Validar la creación con el policy engine
        if not self.policy_engine.authorize_action("create", "task_manager", {}, payload):
            raise PermissionError("Acción 'create' denegada por políticas MAESTRO.")

        # Generar firma si el módulo de seguridad está disponible
        signature = ""
        nonce = str(uuid.uuid4())
        security_module = getattr(self.bus, "security_module", None)
        if security_module:
            sign_data = {
                "task_id": task_id,
                "event_type": "task.created",
                "step": "init",
                "payload": payload,
                "nonce": nonce
            }
            try:
                signature = security_module.sign_message(sign_data)
            except Exception as e:
                self.logger.error(f"Error firmando task.created: {e}")

        # Guardar estado inicial en SQLite (WAL)
        await self.store.save_task_event(
            task_id=task_id,
            tenant_id=self.tenant_id,
            correlation_id=corr_id,
            parent_task_id=parent_task_id,
            status="pending",
            event_type="task.created",
            step="init",
            payload=payload,
            signature=signature,
            nonce=nonce,
            policy_decision="ALLOW",
            hash_chain="", # Calculado automáticamente en save_task_event
            checkpoint_ref=None
        )
        
        # Publicar evento en el bus
        topic = f"rr.{self.tenant_id}.task.created"
        msg = Message(
            sender_id="task_manager",
            sender_name="Task Manager",
            recipient_id=topic,
            message_type=MessageType.EVENT,
            content={
                "task_id": task_id,
                "event_type": "task.created",
                "payload": payload,
                "correlation_id": corr_id,
                "tenant_id": self.tenant_id
            },
            correlation_id=corr_id
        )
        await self.bus.publish(msg)
        self.logger.info(f"Tarea {task_id} creada y publicada en {topic}")
        return task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Recupera el estado de una tarea desde el TaskStore."""
        return await self.store.get_task_state(task_id)

    async def pause_for_approval(self, task_id: str, step: str, request_payload: Dict[str, Any], correlation_id: str = "") -> Any:
        """Pausa la ejecución de una tarea en caliente esperando aprobación humana HITL."""
        event = asyncio.Event()
        self.approval_events[task_id] = event

        await self.store.save_task_event(
            task_id=task_id,
            tenant_id=self.tenant_id,
            correlation_id=correlation_id,
            parent_task_id=None,
            status="paused",
            event_type="task.paused",
            step=step,
            payload={"status": "paused", "hitl_request": request_payload},
            signature="",
            nonce=str(uuid.uuid4()),
            policy_decision="ALLOW",
            hash_chain="",
            checkpoint_ref=None
        )

        topic = f"rr.{self.tenant_id}.task.paused"
        await self.bus.publish(Message(
            sender_id="task_manager",
            sender_name="TaskManager",
            recipient_id=topic,
            message_type=MessageType.EVENT,
            content={
                "task_id": task_id,
                "event_type": "task.paused",
                "step": step,
                "payload": {"status": "paused", "hitl_request": request_payload},
                "correlation_id": correlation_id
            },
            correlation_id=correlation_id
        ))

        self.logger.info(f"TaskManager: Tarea {task_id} pausada esperando decisión HITL ({step}).")
        await event.wait()
        self.approval_events.pop(task_id, None)
        return self.approval_inputs.pop(task_id, None)

    async def resume_task(self, task_id: str, user_input: Any, actor_id: str = "task_manager") -> bool:
        """Reanuda una tarea pausada publicando una actualización de progreso."""
        state = await self.store.get_task_state(task_id)
        if not state:
            return False

        if not self.policy_engine.authorize_action("update", actor_id, state, {"tenant_id": self.tenant_id}):
            raise PermissionError(f"Acción 'resume' denegada para actor {actor_id} por políticas MAESTRO.")

        # Desbloquear evento en memoria si estaba esperando decisión HITL
        if task_id in self.approval_events:
            self.approval_inputs[task_id] = user_input
            self.approval_events[task_id].set()

        # Emitir la actualización del progreso para reanudar el bucle del worker
        topic = f"rr.{self.tenant_id}.task.progress"
        msg = Message(
            sender_id=actor_id,
            sender_name="Task API",
            recipient_id=topic,
            message_type=MessageType.EVENT,
            content={
                "task_id": task_id,
                "event_type": "task.progress",
                "step": "resume",
                "payload": {"status": "running", "user_input": user_input},
                "correlation_id": state["task"].get("correlation_id", "")
            },
            correlation_id=state["task"].get("correlation_id", "")
        )
        await self.bus.publish(msg)
        return True

    async def cancel_task(self, task_id: str, actor_id: str = "task_manager") -> bool:
        """Cancela una tarea activa publicando la solicitud de cancelación."""
        state = await self.store.get_task_state(task_id)
        if not state:
            return False

        if not self.policy_engine.authorize_action("cancel", actor_id, state, {"tenant_id": self.tenant_id}):
            raise PermissionError(f"Acción 'cancel' denegada para actor {actor_id} por políticas MAESTRO.")

        await self.store.save_task_event(
            task_id=task_id,
            tenant_id=self.tenant_id,
            correlation_id=state["task"].get("correlation_id", ""),
            parent_task_id=state["task"].get("parent_task_id"),
            status="cancelled",
            event_type="task.cancelled",
            step="cancel",
            payload={"reason": "Cancelado por usuario/API"},
            signature="",
            nonce=str(uuid.uuid4()),
            policy_decision="ALLOW",
            hash_chain="",
            checkpoint_ref=None
        )

        topic = f"rr.{self.tenant_id}.task.cancelled"
        msg = Message(
            sender_id=actor_id,
            sender_name="Task API",
            recipient_id=topic,
            message_type=MessageType.EVENT,
            content={
                "task_id": task_id,
                "event_type": "task.cancelled",
                "step": "cancel",
                "payload": {"status": "cancelled", "reason": "Cancelado por usuario/API"},
                "correlation_id": state["task"].get("correlation_id", "")
            },
            correlation_id=state["task"].get("correlation_id", "")
        )
        await self.bus.publish(msg)
        return True


class TaskWorker(Agent):
    """
    Worker que consume y ejecuta tareas sobre el MessageBus, heredando de Agent.
    """
    def __init__(self, worker_id: str, message_bus: Any, store: TaskStore, tenant_id: str = "default"):
        super().__init__(worker_id, f"TaskWorker-{worker_id}", "Worker para procesar tareas asíncronas de MCP v2")
        self.worker_id = worker_id
        self.bus = message_bus
        self.message_bus = message_bus
        self.store = store
        self.tenant_id = tenant_id
        self.logger = get_logger(f"TaskWorker-{worker_id}")
        self._handlers: Dict[str, Callable] = {}
        
        # Tracking de ejecución y HITL
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.approval_events: Dict[str, asyncio.Event] = {}
        self.approval_inputs: Dict[str, Any] = {}
        
        # Inyectar MAESTRO Security si está disponible
        self.maestro = getattr(message_bus, "security_module", None)
        self.policy_engine = TaskPolicyEngine(self.maestro)

    def register_handler(self, task_type: str, handler: Callable):
        """Registra un procesador para un tipo de tarea específico."""
        self._handlers[task_type] = handler
        self.policy_engine.register_worker(self.worker_id, list(self._handlers.keys()))

    async def start_listening(self):
        """Se registra en el bus, se suscribe a los tópicos e inicia el agente."""
        # 1. Registrarse formalmente como agente
        await self.bus.register_agent(self)
        
        # 2. Suscribirse a los tópicos canónicos
        self.bus.subscribe(f"rr.{self.tenant_id}.task.created", self.id)
        self.bus.subscribe(f"rr.{self.tenant_id}.task.progress", self.id)
        self.bus.subscribe(f"rr.{self.tenant_id}.task.cancelled", self.id)
        
        # 3. Iniciar el ciclo de ejecución de la clase base Agent
        await self.start()
        
        # 4. Recuperación automática (Cold Resume) al arrancar
        await self.recover_active_tasks()
        self.logger.info(f"Worker {self.worker_id} escuchando tópicos de tarea de tenant '{self.tenant_id}'.")

    async def recover_active_tasks(self):
        """Escanea la base de datos de tareas y reanuda tareas interrumpidas."""
        try:
            tasks = await self.store.list_tasks(self.tenant_id)
            for t in tasks:
                if t["status"] in ("running", "paused"):
                    task_id = t["task_id"]
                    self.logger.info(f"Detectada tarea huérfana {task_id} en estado '{t['status']}'. Iniciando Cold Resume...")
                    asyncio.create_task(self._recover_and_resume_task(task_id))
        except Exception as e:
            self.logger.error(f"Error durante Cold Resume: {e}")

    async def _recover_and_resume_task(self, task_id: str):
        state = await self.store.get_task_state(task_id)
        if not state:
            return
            
        task = state["task"]
        events = state["events"]
        
        # Buscar el último checkpoint
        last_checkpoint = None
        for ev in reversed(events):
            if ev["event_type"] == "task.checkpoint":
                last_checkpoint = ev
                break
                
        payload = last_checkpoint["payload"] if last_checkpoint else task
        task_payload = payload.get("payload", {}) if "payload" in payload else payload
        task_type = task_payload.get("type", "default")
        
        handler = self._handlers.get(task_type)
        if not handler:
            self.logger.warning(f"No hay handler registrado para recuperar tarea tipo '{task_type}'")
            return
            
        corr_id = task.get("correlation_id", "")
        task_obj = asyncio.create_task(
            self._execute_task(task_id, handler, task_payload, corr_id, recovered=True, last_checkpoint=last_checkpoint)
        )
        self.running_tasks[task_id] = task_obj

    async def _process_message(self, message: Message) -> None:
        """Sobrescribe el procesamiento de mensajes para el enrutamiento de eventos."""
        # Validar firma JWS si MAESTRO está inyectado
        if self.maestro and message.signature:
            # Validar firma usando la clave del emisor
            verified = self.maestro.verify_message(message.signature, message.sender_id)
            if not verified:
                self.logger.error(f"Firma JWS inválida del remitente {message.sender_id}. Mensaje descartado.")
                return

        if not isinstance(message.content, dict):
            return
            
        event_type = message.content.get("event_type")
        task_id = message.content.get("task_id")
        payload = message.content.get("payload", {})
        corr_id = message.correlation_id or message.content.get("correlation_id", "")

        if event_type == "task.created":
            await self._on_task_created(task_id, payload, corr_id)
        elif event_type == "task.progress":
            await self._on_task_progress(task_id, payload)
        elif event_type == "task.cancelled":
            await self._on_task_cancelled(task_id)

    async def _on_task_created(self, task_id: str, payload: Dict[str, Any], correlation_id: str):
        """Maneja el evento task.created."""
        task_type = payload.get("type", "default")
        handler = self._handlers.get(task_type)
        if not handler:
            self.logger.warning(f"No handler for task type: {task_type}")
            return
            
        # Autorizar transición "accept" vía MAESTRO Policy Engine
        if not self.policy_engine.authorize_action("accept", self.worker_id, {}, payload):
            self.logger.warning(f"Worker {self.worker_id} rechazó tarea {task_id} por restricción de capacidades.")
            return

        # Emitir task.accepted
        await self._emit_event(task_id, "task.accepted", "started", {}, correlation_id)
        
        # Ejecutar asíncronamente
        task_obj = asyncio.create_task(self._execute_task(task_id, handler, payload, correlation_id))
        self.running_tasks[task_id] = task_obj
        
        # Limpieza al terminar
        task_obj.add_done_callback(lambda t: self.running_tasks.pop(task_id, None))

    async def _on_task_progress(self, task_id: str, payload: Dict[str, Any]):
        """Maneja notificaciones del bus en rr.*.task.progress (ej: resume humano)."""
        # Si la tarea está esperando aprobación humana y recibe una actualización de reanudación
        if payload.get("status") == "running" and task_id in self.approval_events:
            user_input = payload.get("user_input")
            self.approval_inputs[task_id] = user_input
            self.approval_events[task_id].set()

    async def _on_task_cancelled(self, task_id: str):
        """Cancela físicamente la ejecución de la tarea."""
        if task_id in self.running_tasks:
            task_obj = self.running_tasks[task_id]
            task_obj.cancel()
            self.logger.info(f"Tarea {task_id} cancelada físicamente mediante asyncio.Task.cancel()")

    async def pause_for_approval(self, task_id: str, step: str, request_payload: Dict[str, Any], correlation_id: str = "") -> Any:
        """Pausa la ejecución de la tarea en caliente usando asyncio.Event esperando respuesta humana."""
        event = asyncio.Event()
        self.approval_events[task_id] = event
        
        # Emitir evento de pausa
        await self._emit_event(
            task_id=task_id,
            event_type="task.progress",
            step=step,
            payload={"status": "paused", "hitl_request": request_payload},
            correlation_id=correlation_id
        )
        
        # Esperar bloqueo asíncrono
        await event.wait()
        
        # Limpiar referencias
        self.approval_events.pop(task_id, None)
        user_input = self.approval_inputs.pop(task_id, None)
        return user_input

    async def save_checkpoint(self, task_id: str, step: str, payload: Dict[str, Any], correlation_id: str = ""):
        """Guarda un checkpoint intermedio recuperable de la tarea."""
        await self._emit_event(
            task_id=task_id,
            event_type="task.checkpoint",
            step=step,
            payload=payload,
            correlation_id=correlation_id
        )

    async def _execute_task(self, task_id: str, handler: Callable, payload: Dict[str, Any], correlation_id: str, recovered: bool = False, last_checkpoint: Optional[Dict[str, Any]] = None):
        try:
            # Definir callback de progreso dinámico
            async def progress_cb(step_name: str, progress_data: Dict[str, Any]):
                await self._emit_event(task_id, "task.progress", step_name, progress_data, correlation_id)
                
            # Llamar al handler del worker pasándole el checkpoint de recuperación si aplica
            if recovered and last_checkpoint:
                result = await handler(payload, progress_cb, recovered_state=last_checkpoint.get("payload"))
            else:
                result = await handler(payload, progress_cb)
                
            # Emitir result final
            await self._emit_event(task_id, "task.result", "completed", result or {}, correlation_id)
            
        except asyncio.CancelledError:
            self.logger.info(f"Ejecución de tarea {task_id} interrumpida por cancelación.")
            await self._emit_event(task_id, "task.cancelled", "cancelled", {"status": "cancelled"}, correlation_id)
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea {task_id}: {e}", exc_info=True)
            await self._emit_event(task_id, "task.failed", "error", {"error": str(e)}, correlation_id)

    async def _emit_event(self, task_id: str, event_type: str, step: str, payload: Dict[str, Any], correlation_id: str = ""):
        """Persiste el evento y lo propaga a través del MessageBus."""
        status_map = {
            "task.accepted": "running",
            "task.progress": "running",
            "task.checkpoint": "running",
            "task.result": "completed",
            "task.failed": "failed",
            "task.cancelled": "cancelled"
        }
        status = status_map.get(event_type, "running")
        if isinstance(payload, dict) and payload.get("status") == "paused":
            status = "paused"
            
        # Generar firma si el módulo de seguridad está disponible
        signature = ""
        nonce = str(uuid.uuid4())
        policy_decision = "ALLOW"
        
        if self.maestro:
            sign_data = {
                "task_id": task_id,
                "event_type": event_type,
                "step": step,
                "payload": payload,
                "nonce": nonce
            }
            try:
                signature = self.maestro.sign_message(sign_data)
            except Exception as e:
                self.logger.error(f"Error firmando evento {event_type} con MAESTRO: {e}")

        # Guardar en SQLite y calcular hash encadenado
        checkpoint_ref = payload.get("checkpoint_ref") if isinstance(payload, dict) else None
        
        hash_chain = await self.store.save_task_event(
            task_id=task_id,
            tenant_id=self.tenant_id,
            correlation_id=correlation_id or "worker-correlation",
            parent_task_id=None,
            status=status,
            event_type=event_type,
            step=step,
            payload=payload,
            signature=signature,
            nonce=nonce,
            policy_decision=policy_decision,
            checkpoint_ref=checkpoint_ref
        )
        
        # Publicar en el bus
        topic = f"rr.{self.tenant_id}.{event_type}"
        msg = Message(
            sender_id=self.worker_id,
            sender_name="Task Worker",
            recipient_id=topic,
            message_type=MessageType.EVENT,
            content={
                "task_id": task_id,
                "event_type": event_type,
                "step": step,
                "payload": payload,
                "correlation_id": correlation_id,
                "signature": signature,
                "nonce": nonce,
                "policy_decision": policy_decision,
                "hash_chain": hash_chain
            },
            correlation_id=correlation_id
        )
        await self.bus.publish(msg)
