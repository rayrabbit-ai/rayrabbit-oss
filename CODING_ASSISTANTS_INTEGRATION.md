# Integration of AI Coding Assistants and Autonomous CLI Agents with RayRabbit

The current industry standard for interconnecting coding assistants and autonomous CLI agents (**Claude Code, Google Antigravity, OpenHands, Hermes Agent, OpenClaw, Codex CLI**, etc.) with an infrastructure like **RayRabbit** is based on **two bidirectional roles** and **three standardized open protocols**:

```mermaid
graph LR
    subgraph Coding_Assistants ["Coding Assistants & Monoliths"]
        CC["Claude Code (CLI)"]
        AGY["Google Antigravity"]
        OH["OpenHands (OpenDevin)"]
        HA["Hermes Agent / OpenClaw"]
        CX["Codex CLI / Custom Scripts"]
    end

    subgraph RayRabbit_L3 ["RayRabbit Hub Core (L3 Infrastructure)"]
        MCP_Srv["Hub MCP/MCPv2 Server (:8008 / stdio)"]
        WS_Proxy["Sovereign WebSocket Gateway (:8005/ws)"]
        A2A_Bus["A2A Bus & MAESTRO Security (:8005/a2a)"]
        Bridge["DeclarativeBridge (OpenAPI Engine)"]
    end

    subgraph Federated_Ecosystem ["Federated Ecosystem"]
        Crew["CrewAI Squads"]
        Lang["LangChain Chains"]
        DB["ERPs / Databases"]
        A2UI["A2UI Visual Dashboard (:8006)"]
    end

    CC -->|1. MCP Client (JSON config)| MCP_Srv
    AGY -->|1. MCP Client / SDK Hook| MCP_Srv
    OH -->|1. MCP Client or 2. REST Bridge| MCP_Srv
    HA -->|3. WebSocket SDK (@node.mcp_tool)| WS_Proxy
    CX -->|3. WebSocket SDK (@node.mcp_tool)| WS_Proxy
    OH -->|4. DeclarativeBridge| Bridge

    MCP_Srv <--> A2A_Bus
    WS_Proxy <--> A2A_Bus
    Bridge <--> A2A_Bus
    A2A_Bus <--> Federated_Ecosystem
```

---

## Role 1: Coding Assistant as Client/Consumer (MCP Standard)
In this scenario, the coding assistant (Claude Code, Antigravity, OpenHands) connects to RayRabbit to access all domain tools, enterprise APIs, ERPs, and federated agents.

### 1. Claude Code (Anthropic CLI)
Claude Code natively supports the Model Context Protocol (MCP) standard.

**CLI Configuration:**
```bash
claude mcp add rayrabbit-hub -- http://127.0.0.1:8008/mcp/v1
```

**Configuration via `~/.claude.json` or project `.claude/mcp.json`:**
```json
{
  "mcpServers": {
    "rayrabbit": {
      "url": "http://127.0.0.1:8008/mcp/v1",
      "headers": {
        "X-RayRabbit-Agent-Id": "claude_code_developer"
      }
    }
  }
}
```
> **Result**: Claude Code automatically discovers tools via `tools/list` from RayRabbit and can query databases, invoke CrewAI squads, or stream telemetry to the A2UI dashboard directly from the terminal.

---

### 2. Google Antigravity (Official Plugin & MCP Server)
RayRabbit includes an official plugin for Google Antigravity with an embedded MCP server (`stdio` and `http`) supporting **Local and Remote (Cross-Host/LAN/Cloud)** topologies.

**1. Official Plugin Installation:**
* In your project: Copy `clients/antigravity` to `.agent/plugins/rayrabbit`.
* Global (all workspaces): Copy `clients/antigravity` to `~/.gemini/config/plugins/rayrabbit`.

**2. Configuration in `mcp_config.json`:**
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": ["/path/to/rayrabbit-oss/.agent/plugins/antigravity/server/mcp_server.py"],
      "env": {
        "RAYRABBIT_HUB_URL": "http://127.0.0.1:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_devops"
      }
    }
  }
}
```

**3. MCP Tools Exposed to the Session:**
* `rayrabbit_send_message(recipient_id, content)`: Send A2A consensus messages and proposals to other agents or remote Antigravity sessions.
* `rayrabbit_list_agents()`: Discover active sovereign nodes across the mesh.
* `rayrabbit_read_inbox()`: Retrieve pending incoming inbox messages.
* `rayrabbit_call_tool(tool_name, arguments)`: Invoke distributed atomic domain tools (WMS, Routing, Logistics).
* `rayrabbit_get_telemetry()`: Fetch real-time status and metrics from the A2UI dashboard.
* `rayrabbit_publish_fact(key, value)`: Persist facts into L3 Sovereign Memory.

---

### 3. OpenHands (formerly OpenDevin)
OpenHands provides native MCP support and an isolated sandboxed execution runtime.

**Via MCP (`mcp.json` in OpenHands):**
```json
{
  "mcpServers": {
    "rayrabbit-network": {
      "command": "python",
      "args": ["-m", "rayrabbit.protocols.mcp_client", "--hub-url", "http://127.0.0.1:8008"]
    }
  }
}
```

**Or via OpenHands CLI:**
```bash
openhands mcp add rayrabbit-network --transport sse http://127.0.0.1:8008/events
```

---

## Role 2: Coding Assistant as a Sovereign Provider (WebSocket SDK Standard)
In this scenario, an autonomous agent (Hermes Agent, OpenClaw, or custom Codex scripts) exposes its specialized engineering capabilities (refactoring, unit test runners, security auditing) to the entire network.

### 4. Hermes Agent / OpenClaw / Codex CLI (Via `rayrabbit_client` in Python)
No public ports or complex HTTP servers needed; the agent connects to the Hub over secure WebSockets:

```python
from rayrabbit_client import RayRabbitNode
import subprocess

# 1. Persistent WebSocket connection to RayRabbit Hub
node = RayRabbitNode(
    agent_id="hermes_coding_agent",
    hub_url="ws://127.0.0.1:8005/ws"
)

# 2. Expose coding capabilities as MCP tools
@node.mcp_tool(category="code_execution")
def run_pytest(test_path: str) -> dict:
    """Runs the unit test suite and returns diagnostic reports."""
    result = subprocess.run(["pytest", test_path], capture_output=True, text=True)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

@node.mcp_tool(category="refactoring")
def analyze_ast(file_path: str) -> dict:
    """Analyzes code cyclomatic complexity."""
    # Hermes / AST logic
    return {"status": "SUCCESS", "complexity": "LOW", "score": 9.4}

# 3. Start node
node.start()
```

> **What RayRabbit Does Automatically:** The Hub detects the WebSocket connection, binds tools into its unified catalog via `SovereignWebSocketProxy`, and makes them instantly callable by any other agent in the mesh (including Claude Code or LangChain) with Zero-Trust cryptographic validation (JWS RSA-4096).

---

## Role 3: Monoliths with REST APIs (Via RayRabbit DeclarativeBridge)
If the assistant or framework (such as OpenHands backend or AutoGen Studio API) already exposes an HTTP server with `openapi.json`:

**1. Register in `config.yaml`:**
```yaml
external_services:
  - name: "openhands_backend"
    mode: "local"
    address: "http://127.0.0.1:3000"
    topics: ["code_generation", "terminal_execution"]
```

**2. RayRabbit DeclarativeBridge** automatically ingests the OpenAPI specification, converts REST endpoints into MCP / A2A tools, and enforces Mutual Proof of Possession (PoP) authentication with zero changes to the monolith source code (Zero-Patch).

---

## Summary of Integration Standards

| Assistant / Tool | Recommended Integration Mechanism | Underlying Standard | Setup Time |
|---|---|---|---|
| **Claude Code** | MCP Server on `:8008` (`.claude.json`) | Anthropic MCP | < 2 min |
| **Google Antigravity** | MCP Server on `:8008` / Python SDK | Anthropic MCP / A2A | < 2 min |
| **OpenHands** | MCP Config (`mcp.json`) or DeclarativeBridge REST | Anthropic MCP / OpenAPI | < 5 min |
| **Hermes Agent / OpenClaw** | Sovereign SDK (`@node.mcp_tool` on `/ws`) | WebSocket + MCP Proxy | < 5 min |
| **Codex CLI / Custom Scripts** | Sovereign SDK (`RayRabbitNode`) | WebSocket + JSON Schema | < 5 min |

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# Integración de Asistentes de Código y Agentes Autónomos CLI con RayRabbit

El estándar actual de la industria para interconectar asistentes de código y agentes autónomos CLI (**Claude Code, Google Antigravity, OpenHands, Hermes Agent, OpenClaw, Codex CLI**, etc.) con una infraestructura como **RayRabbit** se basa en **dos roles bidireccionales** y **tres protocolos abiertos estandarizados**:

```mermaid
graph LR
    subgraph Coding_Assistants ["Asistentes de Código y Monolitos"]
        CC["Claude Code (CLI)"]
        AGY["Google Antigravity"]
        OH["OpenHands (OpenDevin)"]
        HA["Hermes Agent / OpenClaw"]
        CX["Codex CLI / Custom Scripts"]
    end

    subgraph RayRabbit_L3 ["RayRabbit Hub Core (L3 Infrastructure)"]
        MCP_Srv["Hub MCP/MCPv2 Server (:8008 / stdio)"]
        WS_Proxy["Sovereign WebSocket Gateway (:8005/ws)"]
        A2A_Bus["A2A Bus & MAESTRO Security (:8005/a2a)"]
        Bridge["DeclarativeBridge (OpenAPI Engine)"]
    end

    subgraph Federated_Ecosystem ["Ecosistema Federado"]
        Crew["Cuadrillas CrewAI"]
        Lang["Cadenas LangChain"]
        DB["ERPs / Bases de Datos"]
        A2UI["Dashboard Visual A2UI (:8006)"]
    end

    CC -->|1. MCP Client (JSON config)| MCP_Srv
    AGY -->|1. MCP Client / SDK Hook| MCP_Srv
    OH -->|1. MCP Client o 2. REST Bridge| MCP_Srv
    HA -->|3. WebSocket SDK (@node.mcp_tool)| WS_Proxy
    CX -->|3. WebSocket SDK (@node.mcp_tool)| WS_Proxy
    OH -->|4. DeclarativeBridge| Bridge

    MCP_Srv <--> A2A_Bus
    WS_Proxy <--> A2A_Bus
    Bridge <--> A2A_Bus
    A2A_Bus <--> Federated_Ecosystem
```

---

## Rol 1: El Asistente de Código como Cliente/Consumidor (Estándar MCP)
En este escenario, el asistente de código (Claude Code, Antigravity, OpenHands) se conecta a RayRabbit para acceder a todas las herramientas, APIs, ERPs y agentes federados de tu empresa.

### 1. Claude Code (Anthropic CLI)
Claude Code utiliza de forma nativa el estándar Model Context Protocol (MCP).

**Configuración mediante CLI:**
```bash
claude mcp add rayrabbit-hub -- http://127.0.0.1:8008/mcp/v1
```

**Configuración en archivo `~/.claude.json` o `.claude/mcp.json` del proyecto:**
```json
{
  "mcpServers": {
    "rayrabbit": {
      "url": "http://127.0.0.1:8008/mcp/v1",
      "headers": {
        "X-RayRabbit-Agent-Id": "claude_code_developer"
      }
    }
  }
}
```
> **Resultado**: Claude Code consulta automáticamente `tools/list` a RayRabbit y puede disparar acciones sobre bases de datos, llamar a cuadrillas de CrewAI o solicitar telemetría en el dashboard A2UI directamente desde la terminal.

---

### 2. Google Antigravity (Plugin & Servidor MCP Oficial)
RayRabbit incluye un plugin oficial para Antigravity con servidor MCP integrado (`stdio` y `http`) para comunicación **Local y Remota (Cross-Host/LAN/Cloud)**.

**1. Instalación del Plugin Oficial:**
* En tu proyecto: Copia `clients/antigravity` a `.agent/plugins/rayrabbit`.
* Global (todas las sesiones): Copia `clients/antigravity` a `~/.gemini/config/plugins/rayrabbit`.

**2. Configuración en `mcp_config.json`:**
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": ["${pluginDir}/server/mcp_server.py"],
      "env": {
        "RAYRABBIT_HUB_URL": "http://127.0.0.1:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_devops"
      }
    }
  }
}
```

**3. Herramientas MCP expuestas a la sesión:**
* `rayrabbit_send_message(recipient_id, content)`: Envío de mensajes y propuestas de consenso A2A a otros agentes o sesiones de Antigravity remotas.
* `rayrabbit_list_agents()`: Descubrimiento de nodos soberanos activos en la malla.
* `rayrabbit_read_inbox()`: Lectura del buzón de mensajes entrantes.
* `rayrabbit_call_tool(tool_name, arguments)`: Ejecución de herramientas distribuidas (WMS, Routing, Flota).
* `rayrabbit_get_telemetry()`: Lectura de estado y métricas del dashboard A2UI.
* `rayrabbit_publish_fact(key, value)`: Persistencia en la Memoria Soberana L3.

---

### 3. OpenHands (antes OpenDevin)
OpenHands cuenta con soporte nativo de MCP y runtime autónomo en sandbox.

**Vía MCP (`mcp.json` de OpenHands):**
```json
{
  "mcpServers": {
    "rayrabbit-network": {
      "command": "python",
      "args": ["-m", "rayrabbit.protocols.mcp_client", "--hub-url", "http://127.0.0.1:8008"]
    }
  }
}
```

**O vía CLI de OpenHands:**
```bash
openhands mcp add rayrabbit-network --transport sse http://127.0.0.1:8008/events
```

---

## Rol 2: El Asistente de Código como Proveedor Soberano (Estándar SDK WebSocket)
En este escenario, quieres que un agente autónomo como Hermes Agent, OpenClaw o un script de Codex ofrezca sus habilidades especializadas (refactorización, ejecución de tests, análisis de seguridad) al resto de la red.

### 4. Hermes Agent / OpenClaw / Codex CLI (Vía `rayrabbit_client` en Python)
No necesitas abrir puertos públicos ni configurar servidores HTTP; el agente se conecta al Hub mediante WebSockets seguros:

```python
from rayrabbit_client import RayRabbitNode
import subprocess

# 1. Conexión WebSocket al Hub de RayRabbit
node = RayRabbitNode(
    agent_id="hermes_coding_agent",
    hub_url="ws://127.0.0.1:8005/ws"
)

# 2. Exponer capacidades de código como herramientas MCP
@node.mcp_tool(category="code_execution")
def run_pytest(test_path: str) -> dict:
    """Ejecuta la suite de pruebas unitarias y retorna el diagnóstico."""
    result = subprocess.run(["pytest", test_path], capture_output=True, text=True)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

@node.mcp_tool(category="refactoring")
def analyze_ast(file_path: str) -> dict:
    """Analiza la complejidad ciclomática del archivo."""
    # Lógica de Hermes / AST
    return {"status": "SUCCESS", "complexity": "LOW", "score": 9.4}

# 3. Arrancar el nodo
node.start()
```

> **Qué hace RayRabbit automáticamente:** El Hub detecta la conexión WebSocket, registra las herramientas en su catálogo unificado mediante `SovereignWebSocketProxy` y las vuelve invocables de inmediato para cualquier otro agente de la red (incluso para Claude Code o LangChain) con validación criptográfica Zero-Trust (JWS RSA-4096).

---

## Rol 3: Monolitos con Servidor REST (Vía DeclarativeBridge de RayRabbit)
Si el asistente o monolito (como el backend de OpenHands o una API de AutoGen Studio) ya expone un servidor HTTP con `openapi.json`:

**1. Se registra en `config.yaml` de RayRabbit:**
```yaml
external_services:
  - name: "openhands_backend"
    mode: "local"
    address: "http://127.0.0.1:3000"
    topics: ["code_generation", "terminal_execution"]
```

**2. RayRabbit DeclarativeBridge** lee la especificación OpenAPI automáticamente, convierte los endpoints en herramientas MCP / A2A y aplica autenticación mutua Proof of Possession (PoP) sin tocar ni una sola línea de código del monolito (Zero-Patch).

---

## Resumen de Estándares Actuales

| Asistente / Herramienta | Mecanismo de Integración Recomendado | Estándar Subyacente | Setup |
|---|---|---|---|
| **Claude Code** | MCP Server en `:8008` (`.claude.json`) | Anthropic MCP | < 2 min |
| **Google Antigravity** | MCP Server en `:8008` / Python SDK | Anthropic MCP / A2A | < 2 min |
| **OpenHands** | MCP Config (`mcp.json`) o DeclarativeBridge REST | Anthropic MCP / OpenAPI | < 5 min |
| **Hermes Agent / OpenClaw** | SDK Soberano (`@node.mcp_tool` en `/ws`) | WebSocket + MCP Proxy | < 5 min |
| **Codex CLI / Custom Scripts** | SDK Soberano (`RayRabbitNode`) | WebSocket + JSON Schema | < 5 min |

</details>
