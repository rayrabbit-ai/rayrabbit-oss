import asyncio
import json
import websockets

async def run_demo():
    print("🎯 Iniciando Demo de Cliente MCP v2 Tasks...")
    hub_mcp_url = "ws://127.0.0.1:8008" # Puerto del MCP Server del Hub
    
    try:
        async with websockets.connect(hub_mcp_url) as ws:
            print("🔗 Conectado al Servidor MCP del Hub en el puerto 8008.")
            
            # 1. Solicitar la ejecución de una herramienta (tools/call)
            # Esto iniciará una tarea asíncrona en el motor
            call_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "optimize_route",
                    "arguments": {
                        "origin": "MADRID",
                        "destination": "BARCELONA",
                        "priority": "high"
                    }
                },
                "id": 1
            }
            
            print(f"\n📤 Enviando tools/call para 'optimize_route'...")
            await ws.send(json.dumps(call_request))
            
            raw_response = await ws.recv()
            response = json.loads(raw_response)
            
            result = response.get("result", {})
            if "taskHandle" not in result:
                print(f"❌ Error: El Hub no retornó un taskHandle. Respuesta: {response}")
                return
                
            task_handle = result["taskHandle"]
            task_id = task_handle["task_id"]
            print(f"✅ Tarea asíncrona iniciada con ID: {task_id}")
            print(f"   Estado inicial: {task_handle.get('status')}")
            
            # 2. Suscribirse para ver el progreso real de la tarea (tasks/watch)
            watch_request = {
                "jsonrpc": "2.0",
                "method": "tasks/watch",
                "params": {
                    "task_id": task_id
                },
                "id": 2
            }
            print(f"\n📤 Enviando tasks/watch para seguir el progreso en vivo...")
            await ws.send(json.dumps(watch_request))
            
            # 3. Escuchar notificaciones y eventos de progreso
            print("⏳ Escuchando eventos del motor de tareas...")
            for _ in range(10):
                try:
                    raw_event = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    event_data = json.loads(raw_event)
                    print(f"📥 Notificación recibida:\n{json.dumps(event_data, indent=2)}")
                    
                    # Validar si el estado indica finalización
                    params = event_data.get("params", {})
                    task_data = params.get("task", {}) or event_data.get("result", {}).get("task", {})
                    task_status = task_data.get("status") if isinstance(task_data, dict) else None
                    if not task_status:
                        task_status = params.get("status")
                        
                    if task_status in ["completed", "failed", "cancelled"]:
                        print(f"\n🏁 Tarea terminada con estado: {task_status}")
                        break
                except asyncio.TimeoutError:
                    # Polling alternativo si la notificación tarda en propagarse
                    get_request = {
                        "jsonrpc": "2.0",
                        "method": "tasks/get",
                        "params": {
                            "task_id": task_id
                        },
                        "id": 3
                    }
                    print("\n📤 Enviando tasks/get (Polling)...")
                    await ws.send(json.dumps(get_request))
                    
    except Exception as e:
        print(f"❌ Error de conexión/comunicación: {e}")
        print("Asegúrate de que la infraestructura local esté corriendo (python run_local_rayrabbit_cluster.py)")

if __name__ == "__main__":
    asyncio.run(run_demo())
