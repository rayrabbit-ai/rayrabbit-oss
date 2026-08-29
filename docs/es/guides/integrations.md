# Integración Universal: Frameworks Cognitivos, SDKs Soberanos y Asistentes de Código

RayRabbit interactúa con el ecosistema global de Inteligencia Artificial agéntica sin interferir en su lógica interna ni imponer SDKs propietarios. Como estándar de **Capa L3 (AI TCP/IP + TLS + HTTP)**, proporciona un **modelo de ejecución 100% desacoplado y neutral (Shared-Nothing)**.

La red interconecta de forma horizontal:
1. **Frameworks Cognitivos Heterogéneos**: CrewAI, AutoGen, LangChain, Microsoft Agent Framework (MAF), LlamaIndex y $N$-frameworks.
2. **Nodos SDK Soberanos (Herramientas Atómicas de Dominio)**: Clientes en Python (`rayrabbit_client`) y JavaScript/TypeScript (`@rayrabbit-client`).
3. **Asistentes de Código y Agentes Autónomos**: Claude Code, OpenAI Codex CLI/SDK, Google Antigravity CLI/SDK, OpenHands, Hermes Agent, OpenClaw y $N$-Agentes.
4. **Portales Visuales Declarativos**: Interfaz telemática interactiva A2UI v0.9.1.

---

## El Modelo de Servicio Soberano Desacoplado (Modo Tri-Acceso)

Cada nodo o servicio conectado a la red RayRabbit expone **tres modos de acceso estandarizados**:

```
┌─────────────────────────────────────────────────────┐
│ Nodo Soberano / Framework / Asistente                │
├─────────────────────────────────────────────────────┤
│ Modo 1: OpenAPI (DeclarativeBridge)                │
│   GET /openapi.json                                 │
├─────────────────────────────────────────────────────┤
│ Modo 2: A2A Nativo (JSON-RPC 2.0 + Mutual PoP)      │
│   POST /a2a  --> JSON-RPC 2.0                       │
├─────────────────────────────────────────────────────┤
│ Modo 3: MCPv2 Tool Calling & TaskEngine            │
│   GET /mcp/tools  --> Discovery por categoría       │
│   POST /mcp/call  --> Task Lifecycle asíncrono      │
└─────────────────────────────────────────────────────┘
```

1. **Modo 1: OpenAPI (DeclarativeBridge Zero-Patch)**: El nodo expone `/openapi.json`. El Hub Core mapea automáticamente sus endpoints a topics asíncronos en el **MessageBus** con 0% de modificación en el código.
2. **Modo 2: A2A Nativo (Google A2A v1.0)**: Endpoint `POST /a2a` para transacciones **JSON-RPC 2.0** con firmas JWS RSA-4096 y handshake Mutual PoP.
3. **Modo 3: MCPv2 Tool Calling**: Endpoints `GET /mcp/tools` y `POST /mcp/call` con desambiguación dinámica por `category`/`namespace` (JSON Schema 2020-12) y gestión de ciclo de vida con el `TaskEngine`.

---

## Nodo LangChain Desacoplado

El microservicio de LangChain (que corre en el Puerto **8002**) envuelve flujos lógicos nativos. No importa código de `rayrabbit`. En su lugar, gestiona firmas JWS usando un gestor ligero local (como `LocalJWSManager`) que consume librerías estándar de `cryptography` de Python.

### Interfaz Core:
```python
# langchain_service.py - Estructura desacoplada de FastAPI
from fastapi import FastAPI
from protocols import JSONRPCRequest, JSONRPCResponse, MCPToolCallRequest, MCPResponse

app = FastAPI(title="Nodo Soberano LangChain")

@app.post("/invoke")
async def invoke(payload: dict):
    # Procesa a través del mapeo del DeclarativeBridge
    ...

@app.post("/a2a")
async def a2a_endpoint(rpc: JSONRPCRequest):
    # Endpoint seguro A2A JSON-RPC 2.0
    ...

@app.post("/mcp/call")
async def mcp_call_tool(tool_call: MCPToolCallRequest):
    # Ejecución de herramientas MCP
    ...
```

---

## Nodo CrewAI Desacoplado

El servicio de CrewAI (que corre en el Puerto **8001**) envuelve equipos colaborativos. Recibe entradas a través del Modo 1 (conector declarativo `/invoke`), coordina internamente sus agentes usando herramientas locales y retorna resultados vía JSON estándar, manteniendo su código totalmente libre de dependencias del framework RayRabbit.

---

## Integración de Asistentes de Código y Agentes Autónomos (Vía B)

RayRabbit permite conectar no solo microservicios de frameworks, sino también asistentes de codificación autónomos y agentes CLI como **Claude Code, OpenAI Codex, Google Antigravity, OpenHands, Hermes Agent y OpenClaw**:

### Conexión Directa por WebSocket (`ws://127.0.0.1:8005/ws`):
Los agentes se conectan al canal de ingress `/ws` del Hub. El Hub los encapsula mediante `SovereignWebSocketProxy`, permitiendo que expongan herramientas o consuman herramientas de la red sin necesidad de abrir puertos HTTP en sus entornos locales.

```python
# Integración de un Asistente o Script Autónomo con el SDK Oficial
from rayrabbit_client import RayRabbitNode

node = RayRabbitNode(agent_id="code_assistant_node", hub_url="ws://127.0.0.1:8005/ws")

@node.mcp_tool(category="code_intelligence")
def analyze_repository(repo_path: str) -> dict:
    """Inspecciona la arquitectura del repositorio y retorna el mapa de dependencias."""
    return {"status": "analyzed", "modules_count": 42, "health": "excellent"}

node.start()
```

---

!!! enterprise "Sidecar de Seguridad Enterprise Desacoplado"
    Para separar completamente la lógica de aplicación de la seguridad en la capa de transporte, RayRabbit Enterprise utiliza un patrón de despliegue Sidecar. El Sidecar maneja automáticamente el cifrado mTLS, la firma de payloads y la verificación de identidad de forma transparente, permitiendo que los servicios de agentes permanezcan completamente agnósticos de la capa criptográfica de la red.
