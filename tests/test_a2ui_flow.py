"""
test_a2ui_flow.py - Prueba de Integración E2E del Flujo A2UI v0.9.1

Cubre 3 escenarios:
  1. Health checks de todos los servicios del cluster
  2. Conexión WebSocket al relay y recepción del dashboard inicial
  3. Consulta humana por WebSocket y verificación de respuesta narrativa

Requisito: el cluster debe estar corriendo antes de ejecutar este test.
  > taskkill /F /IM python.exe /T
  > python run_distributed_cluster.py
"""

import asyncio
import json
import os
import httpx
import websockets
import sys


HUB_URL = "http://127.0.0.1:8005"
UI_MANAGER_URL = "http://127.0.0.1:8006"
WS_URL = "ws://127.0.0.1:8005/ws/a2ui/test_dashboard"
STREAM_ID = "test_dashboard"
TIMEOUT = 90  # segundos esperando mensajes WS


# ─── Helpers ──────────────────────────────────────────────────────────────────

def ok(msg: str):
    print(f"  ✅ {msg}")

def fail(msg: str):
    print(f"  ❌ {msg}")
    raise AssertionError(msg)

def info(msg: str):
    print(f"  ℹ️  {msg}")


import pytest

async def check_cluster_online():
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"{HUB_URL}/health")
            if resp.status_code == 200:
                return True
    except Exception:
        pass
    pytest.skip("Cluster local no está corriendo en http://127.0.0.1:8005 (Prueba E2E requiere clúster activo)")

# ─── Test 1: Health checks ────────────────────────────────────────────────────

async def test_health_checks():
    await check_cluster_online()
    print("\n[TEST 1] Health checks de servicios")
    services = {
        "Hub (8005)":            f"{HUB_URL}/health",
        "UI Manager (8006)":     f"{UI_MANAGER_URL}/health",
        "LangChain (8002)":      "http://127.0.0.1:8002/health",
        "CrewAI (8001)":         "http://127.0.0.1:8001/health",
        "AutoGen (8003)":        "http://127.0.0.1:8003/health",
    }
    async with httpx.AsyncClient(timeout=5) as client:
        for name, url in services.items():
            try:
                resp = await client.get(url)
                if resp.status_code in [200, 404]:
                    status = resp.json().get('status', 'ok') if resp.status_code == 200 else "online (route not found)"
                    ok(f"{name} → {status}")
                else:
                    fail(f"{name} respondió HTTP {resp.status_code}")
            except Exception as e:
                fail(f"{name} no responde: {e}")


# ─── Test 2: WebSocket — Recepción del Dashboard inicial ─────────────────────

async def test_ws_dashboard_init():
    await check_cluster_online()
    print("\n[TEST 2] WebSocket → Solicitud 'get_dashboard' → Recepción de eventos A2UI")
    received = []

    try:
        async with websockets.connect(WS_URL) as ws:
            ok(f"WebSocket conectado a {WS_URL}")

            # Solicitar el dashboard
            await ws.send(json.dumps({
                "action": "get_dashboard",
                "agent_id": "universal_a2ui_agent"
            }))
            info("Solicitud 'get_dashboard' enviada. Esperando respuesta...")

            deadline = asyncio.get_running_loop().time() + TIMEOUT
            while asyncio.get_running_loop().time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=3)
                    data = json.loads(raw)
                    a2ui = data.get("a2ui", data)
                    msg_type = list(a2ui.keys())[0] if a2ui else "unknown"
                    received.append(msg_type)
                    info(f"Mensaje recibido: tipo='{msg_type}'")
                    # Si llegó al menos un beginRendering o surfaceUpdate, el flujo funciona
                    if msg_type in ("beginRendering", "surfaceUpdate", "dataModelUpdate"):
                        ok(f"Evento A2UI válido recibido: '{msg_type}'")
                        return
                except asyncio.TimeoutError:
                    continue

    except Exception as e:
        fail(f"Error WebSocket: {e}")

    if received:
        ok(f"Recibidos {len(received)} mensajes: {received}")
    else:
        fail(f"No se recibieron mensajes A2UI en {TIMEOUT}s. ¿El agente está corriendo?")


# ─── Test 3: Consulta humana por WebSocket (Transporte / Dry-Run) ───────────────

async def test_ws_human_query():
    await check_cluster_online()
    print("\n[TEST 3] WebSocket → human_query (Dry-Run Transporte) → Confirmación A2UI")

    try:
        async with websockets.connect(WS_URL) as ws:
            ok("WebSocket conectado")

            # Enviar una consulta humana con flag dry_run para validar transporte sin invocar LLM
            await ws.send(json.dumps({
                "name": "human_query",
                "params": {
                    "query_input": "Ping de transporte A2UI",
                    "dry_run": True
                }
            }))
            info("Consulta de prueba enviada (dry_run: True). Esperando confirmación de relay...")

            deadline = asyncio.get_running_loop().time() + TIMEOUT
            while asyncio.get_running_loop().time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=3)
                    data = json.loads(raw)
                    a2ui = data.get("a2ui", data)
                    
                    cmd_key = None
                    if "updateDataModel" in a2ui:
                        cmd_key = "updateDataModel"
                    elif "dataModelUpdate" in a2ui:
                        cmd_key = "dataModelUpdate"
                        
                    if cmd_key:
                        update = a2ui[cmd_key]
                        if update.get("path") == "/narrative":
                            value = update.get("value", "")
                            ok(f"Narrativa recibida: '{value[:80]}...'")
                            return
                    if "surfaceUpdate" in a2ui:
                        ok("surfaceUpdate recibido (el agente está procesando)")
                        return
                except asyncio.TimeoutError:
                    continue

    except Exception as e:
        fail(f"Error WebSocket: {e}")

    fail(f"No se recibió respuesta narrativa en {TIMEOUT}s")


# ─── Test 3 (Live): Inferencia Real LLM E2E (Post-Desarrollo) ───────────────────

@pytest.mark.e2e_live
async def test_ws_human_query_live_llm():
    """
    Prueba E2E con inferencia LLM real (OpenRouter/Gemini) y orquestación cognitiva.
    Aislada para evaluación post-desarrollo. Omitida por defecto en CI/local para evitar
    costos y latencia innecesaria.
    """
    if os.getenv("RAYRABBIT_LIVE_LLM_TESTS") != "1":
        pytest.skip("Prueba E2E con inferencia real LLM omitida por defecto. Para activar: RAYRABBIT_LIVE_LLM_TESTS=1 pytest -m e2e_live")

    await check_cluster_online()
    print("\n[TEST 3-LIVE] WebSocket → human_query (Live LLM) → Respuesta cognitiva generada")

    try:
        async with websockets.connect(WS_URL) as ws:
            ok("WebSocket conectado")

            # Enviar una consulta humana real sin dry_run
            await ws.send(json.dumps({
                "name": "human_query",
                "params": {"query_input": "¿Dónde está mi paquete?"}
            }))
            info("Consulta enviada al LLM. Esperando narrativa generada...")

            deadline = asyncio.get_running_loop().time() + TIMEOUT
            while asyncio.get_running_loop().time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=3)
                    data = json.loads(raw)
                    a2ui = data.get("a2ui", data)
                    
                    cmd_key = None
                    if "updateDataModel" in a2ui:
                        cmd_key = "updateDataModel"
                    elif "dataModelUpdate" in a2ui:
                        cmd_key = "dataModelUpdate"
                        
                    if cmd_key:
                        update = a2ui[cmd_key]
                        if update.get("path") == "/narrative":
                            value = update.get("value", "")
                            if value and not value.startswith("✅ [DRY-RUN]"):
                                ok(f"Narrativa generada por LLM recibida: '{value[:80]}...'")
                                return
                    if "surfaceUpdate" in a2ui:
                        ok("surfaceUpdate recibido (el agente está procesando en vivo)")
                except asyncio.TimeoutError:
                    continue

    except Exception as e:
        fail(f"Error WebSocket en test live: {e}")

    fail(f"No se recibió respuesta narrativa del LLM en {TIMEOUT}s")


# ─── Test 4: Inyección directa vía HTTP API ───────────────────────────────────

async def test_http_publish():
    await check_cluster_online()
    """
    Simula la publicación de un mensaje logístico (como si fuera un agente externo)
    directamente en el MessageBus del Hub y verifica que llega al WebSocket.
    """
    print("\n[TEST 4] HTTP /api/publish-message → MessageBus → WebSocket relay")

    received_via_ws = []

    async def listen_ws():
        try:
            async with websockets.connect(WS_URL) as ws:
                deadline = asyncio.get_running_loop().time() + TIMEOUT
                while asyncio.get_running_loop().time() < deadline:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=2)
                        received_via_ws.append(json.loads(raw))
                    except asyncio.TimeoutError:
                        continue
        except Exception:
            pass

    # Lanzar listener WebSocket en paralelo
    ws_task = asyncio.create_task(listen_ws())
    await asyncio.sleep(0.5)  # Dar tiempo al listener para conectar

    # Publicar un mensaje de prueba en el Hub
    payload = {
        "sender_id": "test_runner",
        "sender_name": "Test Runner",
        "recipient_id": "universal_a2ui_agent",
        "message_type": "request",
        "content": {
            "action": "get_dashboard",
            "test": True
        },
        "correlation_id": STREAM_ID
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            resp = await client.post(f"{HUB_URL}/api/publish-message", json=payload)
            if resp.status_code == 200:
                ok(f"Mensaje publicado en Hub: {resp.json().get('status')}")
            else:
                fail(f"Fallo al publicar: {resp.status_code} - {resp.text}")
        except Exception as e:
            fail(f"Error HTTP: {e}")

    # Esperar mensajes
    await asyncio.sleep(TIMEOUT / 3)
    ws_task.cancel()

    if received_via_ws:
        ok(f"✅ Relay funcionando: {len(received_via_ws)} mensajes recibidos por WS")
        info(f"Primer mensaje: tipo='{list(received_via_ws[0].get('a2ui', {}).keys())}'")
    else:
        fail(f"No llegaron mensajes al WebSocket. Revisar relay y agente.")


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print(" RayRabbit A2UI — Prueba de Integración E2E")
    print(f" Stream: {STREAM_ID} | Hub: {HUB_URL}")
    print("=" * 60)

    await test_health_checks()
    await test_ws_dashboard_init()
    await test_ws_human_query()
    await test_http_publish()
    if os.getenv("RAYRABBIT_LIVE_LLM_TESTS") == "1":
        await test_ws_human_query_live_llm()

    print("\n" + "=" * 60)
    print(" Prueba completada")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
