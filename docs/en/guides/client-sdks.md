# SDK Nodes, Domain Atomic Tools & CLI Assistants

RayRabbit enables developers to connect custom agentic applications, domain business tools, and autonomous coding assistants (Claude Code, OpenAI Codex, Google Antigravity, OpenHands, Hermes, OpenClaw, $N$-Agents) to the sovereign network using the official **RayRabbit Client SDKs** (available for Python and JavaScript/TypeScript under `clients/`).

---

## Sovereign Mesh: How SDK Nodes & Framework Services Interact

In RayRabbit's Layer 3 architecture, there is a clear separation of concerns with horizontal mediation:

* **Cognitive Framework Services (CrewAI, AutoGen, LangChain, MAF, LlamaIndex):** Execute complex reasoning, multi-agent squad orchestration, and consensus debates using their own LLM engines.
* **SDK Nodes & Domain Atomic Tools (`rayrabbit_client` Clients):** Expose domain business tools (SAP TM, ERP systems, Binance, local REST APIs) by connecting via **persistent WebSocket (`ws://127.0.0.1:8005/ws`)** directly to the Core Gateway.
* **Coding Assistants & Autonomous Agents:** Connect via persistent WebSockets to invoke or expose tools across the decentralized mesh.

```
                               ┌──────────────────────────────────┐
                               │   A2UI Visual Portal (Port 8006) │
                               └────────────────┬─────────────────┘
                                                │ 1. Request Task (A2A)
                                                ▼
┌───────────────────────────┐  2. A2A Invocation┌──────────────────────────────────┐
│ Sovereign Framework Nodes │ ─────────────────►│ RayRabbit Core Gateway(Port 8005)│
│ - CrewAI (8001)           │ ◄─────────────────│    MessageBus + MAESTRO + MCP    │
│ - AutoGen (8003)          │ 3. Query Tools    └────────────────┬─────────────────┘
│ - LangChain (8002)        │    via Mesh MCP                    │ 4. Async Routing
│ - MAF / LlamaIndex        │                                    │    via WebSocket /ws
└───────────────────────────┘                                    ▼
                                                ┌──────────────────────────────────┐
                                                │ Sovereign SDK Nodes & CLI Agents │
                                                │ - logistics_ui_manager (Python)  │
                                                │ - crypto_trader_agent (Node.js)  │
                                                │ - Claude Code / Antigravity CLI  │
                                                └──────────────────────────────────┘
```

---

## Using the Python SDK (`rayrabbit_client`)

The Python SDK turns any Python function, database connector, or script into a **Sovereign RayRabbit Node** using the `@node.mcp_tool` decorator:

```python
import asyncio
from rayrabbit_client import RayRabbitNode

# Initialize the sovereign node
node = RayRabbitNode(
    agent_id="my_business_agent",
    hub_url="ws://127.0.0.1:8005/ws"
)

@node.mcp_tool(category="inventory")
def check_inventory(product_id: str) -> dict:
    """Queries real-time stock levels in the ERP database."""
    return {"product_id": product_id, "stock": 42, "status": "available"}

if __name__ == "__main__":
    node.start()
```

---

## MAESTRO Security & Registration Flow

When starting a `RayRabbitNode`:

1. **WebSocket Connection:** Establishes a persistent bidirectional connection to `/ws` on the Core Gateway.
2. **Identity Generation:** Generates sovereign RSA-4096 asymmetric keypairs locally.
3. **Mutual PoP Handshake:** Signs the registration challenge with compact JWS (RFC 7515).
4. **Sovereign Proxy (`SovereignWebSocketProxy`):** The Core Gateway instantiates an in-memory proxy and exposes the tools in the global **MCP Mesh Gateway (`ws://127.0.0.1:8008`)** catalog.

Any federated service (CrewAI, AutoGen, LangChain, MAF, LlamaIndex, Claude Code, or Antigravity) can now discover and invoke your domain business tools across the RayRabbit sovereign mesh.
