# Universal Integrations: Cognitive Frameworks, Sovereign SDKs & Coding Assistants

RayRabbit connects the global agentic AI ecosystem without altering internal logic or imposing vendor SDKs. Operating as the **Layer 3 (AI TCP/IP + TLS + HTTP)** industry standard, it provides a **100% decoupled, neutral execution model under Shared-Nothing Architecture**.

The network horizontally interconnects:
1. **Heterogeneous Cognitive Frameworks**: CrewAI, AutoGen, LangChain, Microsoft Agent Framework (MAF), LlamaIndex, and arbitrary $N$-frameworks.
2. **Sovereign SDK Nodes (Domain Atomic Tools)**: Python (`rayrabbit_client`) and JavaScript/TypeScript (`@rayrabbit-client`) clients.
3. **Coding Assistants & Autonomous CLI Agents**: Claude Code, OpenAI Codex CLI/SDK, Google Antigravity CLI/SDK, OpenHands, Hermes Agent, OpenClaw, and arbitrary $N$-Agents.
4. **Declarative Visual Portals**: Interactive telemetry interfaces powered by A2UI v0.9.1.

---

## The Sovereign Decoupled Service Model (Tri-Access Mode)

Every node or service connected to the RayRabbit network exposes **three standardized access modes**:

```
┌─────────────────────────────────────────────────────┐
│ Sovereign Node / Framework / Assistant             │
├─────────────────────────────────────────────────────┤
│ Mode 1: OpenAPI (DeclarativeBridge)                │
│   GET /openapi.json                                 │
├─────────────────────────────────────────────────────┤
│ Mode 2: Native A2A (JSON-RPC 2.0 + Mutual PoP)     │
│   POST /a2a  --> JSON-RPC 2.0                       │
├─────────────────────────────────────────────────────┤
│ Mode 3: MCPv2 Tool Calling & TaskEngine            │
│   GET /mcp/tools  --> Discovery by category         │
│   POST /mcp/call  --> Async Task Lifecycle          │
└─────────────────────────────────────────────────────┘
```

1. **Mode 1: OpenAPI (DeclarativeBridge Zero-Patch)**: The node exposes `/openapi.json`. The Core Hub automatically maps its endpoints to asynchronous topics on the **MessageBus** with 0% code modifications.
2. **Mode 2: Native A2A (Google A2A v1.0)**: Endpoint `POST /a2a` for **JSON-RPC 2.0** transactions with RSA-4096 JWS signatures and Mutual PoP handshake.
3. **Mode 3: MCPv2 Tool Calling**: Endpoints `GET /mcp/tools` and `POST /mcp/call` with dynamic `category`/`namespace` disambiguation (JSON Schema 2020-12) and `TaskEngine` async lifecycle management.

---

## Decoupled LangChain Node

The LangChain microservice (running on Port **8002**) wraps chain workflows natively. It does not import any `rayrabbit` code. Instead, it implements JWS signing using a lightweight standalone manager class (e.g. `LocalJWSManager`) which relies on standard `cryptography` libraries.

### Core Interface:
```python
# langchain_service.py typical decoupled FastAPI layout
from fastapi import FastAPI
from protocols import JSONRPCRequest, JSONRPCResponse, MCPToolCallRequest, MCPResponse

app = FastAPI(title="Sovereign LangChain Node")

@app.post("/invoke")
async def invoke(payload: dict):
    # Processed via DeclarativeBridge mapping
    ...

@app.post("/a2a")
async def a2a_endpoint(rpc: JSONRPCRequest):
    # Secure JSON-RPC 2.0 endpoint
    ...

@app.post("/mcp/call")
async def mcp_call_tool(tool_call: MCPToolCallRequest):
    # MCP tool calling execution
    ...
```

---

## Decoupled CrewAI Node

The CrewAI service (running on Port **8001**) wraps collaborating agent teams. It accepts raw inputs via Mode 1 (declarative connector `/invoke`), processes tasks internally using native tools (such as checking database states or shipping metrics), and returns output results via standard JSON responses, keeping its code 100% independent.

---

## Integrating Coding Assistants & Autonomous Agents (Path B)

RayRabbit seamlessly federates not only framework microservices, but also autonomous coding assistants and CLI agents such as **Claude Code, OpenAI Codex, Google Antigravity, OpenHands, Hermes Agent, and OpenClaw**:

### Direct Ingress via Persistent WebSocket (`ws://127.0.0.1:8005/ws`):
Agents connect to the Hub's `/ws` ingress channel. The Hub encapsulates them via `SovereignWebSocketProxy`, allowing them to expose or execute network tools without having to bind local HTTP listening ports.

```python
# Connecting an Autonomous Script or Assistant using the Official SDK
from rayrabbit_client import RayRabbitNode

node = RayRabbitNode(agent_id="code_assistant_node", hub_url="ws://127.0.0.1:8005/ws")

@node.mcp_tool(category="code_intelligence")
def analyze_repository(repo_path: str) -> dict:
    """Inspects codebase topology and extracts dependency relationships."""
    return {"status": "analyzed", "modules_count": 42, "health": "excellent"}

node.start()
```

---

!!! enterprise "Decoupled Enterprise Security Sidecar"
    To fully separate application logic from transport-layer security, RayRabbit Enterprise utilizes a Sidecar deployment pattern. The Sidecar automatically handles mTLS encryption, payload signing, and identity verification transparently, allowing agent services to remain completely agnostic of the cryptographic network layer.
