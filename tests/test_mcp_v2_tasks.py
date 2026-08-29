import asyncio
import json
import pytest
from pathlib import Path
from rayrabbit.core.message_bus import MessageBus
from rayrabbit.protocols.mcp import MCPProtocol, MCPError
from rayrabbit.communication.message import Message, MessageType
from rayrabbit.core.task_engine.store import TaskStore
from rayrabbit.core.task_engine.manager import TaskWorker, TaskManager

@pytest.mark.asyncio
async def test_mcp_v2_tasks_lifecycle():
    # Setup real components in-memory
    db_path = Path("test_tasks.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass
        
    bus = None
    worker_task = None
    try:
        # 1. Instanciar MessageBus y TaskStore reales
        bus = MessageBus()
        store = TaskStore(db_path)
        manager = TaskManager(bus, store, tenant_id="test_tenant")
        bus.task_manager = manager
        
        # 2. Iniciar el MessageBus (que arranca el protocolo MCP automáticamente)
        await bus.start()
        protocol = bus.mcp_protocol
        
        # Caso 1: Handshake de capabilities (tasks)
        init_params = {
            "protocolVersion": "2026-07-28",
            "capabilities": {
                "tasks": {}
            }
        }
        init_result = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": init_params,
            "id": 1
        })
        assert "result" in init_result
        assert "tasks" in init_result["result"]["capabilities"]
        assert protocol.client_supports_tasks is True
        
        # Registrar una herramienta de prueba en el protocolo
        test_tool_schema = {
            "type": "function",
            "description": "Calcula la suma de dos números.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"}
                },
                "required": ["a", "b"]
            }
        }
        protocol.register_tool("add_numbers", "test_agent", test_tool_schema)
        
        # Caso 2: Dynamic Routing (retornar taskHandle en vez de bloquear)
        call_params = {
            "name": "add_numbers",
            "arguments": {"a": 5, "b": 10}
        }
        call_result = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": call_params,
            "id": 2
        })
        assert "result" in call_result
        assert "taskHandle" in call_result["result"]
        task_id = call_result["result"]["taskHandle"]["task_id"]
        assert task_id is not None
        
        # Caso 3: tasks/get (recuperar estado e historial)
        get_result = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {"task_id": task_id},
            "id": 3
        })
        assert "result" in get_result
        assert get_result["result"]["task"]["task_id"] == task_id
        assert get_result["result"]["task"]["status"] == "pending"
        
        # Registrar y arrancar un TaskWorker real
        worker = TaskWorker("test_worker", bus, store, tenant_id="test_tenant")
        
        # Handler de prueba que suma a + b
        async def handle_add(payload, progress_cb, recovered_state=None):
            print("[INFO] handle_add is running! payload:", payload)
            args = payload.get("arguments", {})
            await progress_cb("processing", {"progress": 50})
            return {"sum": args["a"] + args["b"]}
            
        worker.register_handler("tool_call", handle_add)
        
        # Escuchar eventos de progreso en el bus para validar replay/routing
        progress_events = []
        # Registrar agente oyente en el bus
        class TestListenerAgent:
            def __init__(self):
                self.id = "test_progress_listener"
                self.name = "listener"
                self.capabilities = []
            async def receive_message(self, msg):
                progress_events.append(msg)
                
        listener_agent = TestListenerAgent()
        bus.agents["test_progress_listener"] = listener_agent
        
        # Suscribir al tópico de progreso
        topic_name = "rr.test_tenant.task.progress"
        bus.subscribers[topic_name].add("test_progress_listener")

        # Arrancar worker en segundo plano
        worker_task = asyncio.create_task(worker.start_listening())
        await asyncio.sleep(0.5)  # Dar tiempo al worker para iniciar
        await bus.offline_tolerance.sync_now()  # Forzar re-entrega del evento del outbox
        await asyncio.sleep(0.5)  # Dar tiempo al worker para procesar
        
        # Caso 4: tasks/list (validar que lista las tareas creadas)
        list_result = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tasks/list",
            "params": {"tenant_id": "test_tenant"},
            "id": 4
        })
        assert len(list_result["result"]) >= 1
        
        # Esperar a que el worker complete la tarea
        await asyncio.sleep(0.5)
        
        # Verificar estado final completado
        status_resp = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {"task_id": task_id},
            "id": 5
        })
        print("[INFO] status_resp result:", status_resp)
        db_state = await store.get_task_state(task_id)
        print("[INFO] store db_state:", db_state)
        assert status_resp["result"]["task"]["status"] == "completed"
        
        # Caso 5: cancel_task (probar flujo de cancelación)
        call_result2 = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": call_params,
            "id": 6
        })
        task_id2 = call_result2["result"]["taskHandle"]["task_id"]
        
        # Cancelar tarea
        cancel_result = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tasks/cancel",
            "params": {"task_id": task_id2, "actor_id": "test_actor"},
            "id": 7
        })
        assert cancel_result["result"]["status"] == "cancelled"
        
        # Caso 6: resume_task (HITL)
        async def handle_hitl(payload, progress_cb, recovered_state=None):
            current_asyncio_task = asyncio.current_task()
            task_id = None
            for tid, t_obj in worker.running_tasks.items():
                if t_obj == current_asyncio_task:
                    task_id = tid
                    break
            if not task_id:
                return {"result": "No task id found"}
                
            user_input = await worker.pause_for_approval(
                task_id=task_id,
                step="paused",
                request_payload={"message": "Requiere aprobacion"}
            )
            if user_input and user_input.get("approved"):
                return {"result": "Aprobado"}
            return {"result": "Rechazado"}
            
        worker.register_handler("tool_call", handle_hitl)
        
        call_result3 = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": call_params,
            "id": 8
        })
        task_id3 = call_result3["result"]["taskHandle"]["task_id"]
        
        await asyncio.sleep(0.5)
        
        status_resp3 = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {"task_id": task_id3},
            "id": 9
        })
        assert status_resp3["result"]["task"]["status"] == "paused"
        
        resume_result = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tasks/update",
            "params": {
                "task_id": task_id3,
                "user_input": {"approved": True},
                "actor_id": "test_actor"
            },
            "id": 10
        })
        assert resume_result["result"]["status"] == "resumed"
        
        await asyncio.sleep(0.5)
        
        status_resp3_final = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {"task_id": task_id3},
            "id": 11
        })
        assert status_resp3_final["result"]["task"]["status"] == "completed"
        
        # Caso 7: replay_history en MessageBus
        progress_events.clear()
        await bus.replay_history(topic_name, "test_progress_listener")
        assert len(progress_events) > 0
        
        # Caso 8: control de políticas por Workers Capabilities (Allowlist)
        # Cambiamos las capabilities en el policy engine del manager
        manager.policy_engine.worker_allowlist = {"test_worker": ["other_capability"]}
        result_fail = await protocol.handle_rpc_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": call_params,
            "id": 12
        })
        assert "error" in result_fail
        assert result_fail["error"]["code"] == -32003
        
    finally:
        if worker_task:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        if bus:
            try:
                await bus.stop()
            except Exception:
                pass
        if db_path.exists():
            try:
                db_path.unlink()
            except Exception:
                pass
