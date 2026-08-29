# The Protocol Suite: A2A, MCPv2, and A2UI

RayRabbit unifies heterogeneous AI agent ecosystems through three native, open protocol specifications governing transport messaging, context/tool sharing, and reactive visual telemetry.

---

## 1. Google A2A (Agent-to-Agent v1.0)

The **A2A** protocol standardizes task delegation, messaging, and results exchange. RayRabbit implements this over HTTP and WebSockets using **JSON-RPC 2.0** envelopes and cryptographic **AgentCard** identities.

### A2A Request Example
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/create",
  "params": {
    "prompt": "Optimize dispatch for 50 logistics bundles to Munich",
    "package_id": "PKG-2026-A9",
    "priority": "high"
  },
  "id": "req-9b8c7d"
}
```

### A2A Response Example
```json
{
  "jsonrpc": "2.0",
  "result": {
    "output": "Route optimized successfully: Carrier DHL Express, ETA 14:00 CET.",
    "status": "completed"
  },
  "id": "req-9b8c7d"
}
```

---

## 2. Anthropic MCP / MCPv2 (Model Context Protocol)

While A2A manages *messaging*, **MCP / MCPv2** standardizes *capabilities* (dynamic tools). RayRabbit operates a native MCP server over WebSocket on port **`:8008`**, maintaining an in-memory unified catalog (`tools/list`, `tools/call`).

### Dynamic Tool Classification (JSON Schema 2020-12)
To allow any LLM to discover and use domain tools without static hardcoding, all tools in RayRabbit **MUST** declare a dynamic `category` or `namespace` metadata attribute:

```json
{
  "name": "get_shipment_status",
  "description": "Queries real-time order status and ETA from the corporate ERP.",
  "category": "logistics",
  "inputSchema": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "Unique order identifier (e.g. ORD-9812)"
      }
    },
    "required": ["order_id"]
  }
}
```

### Asynchronous TaskEngine (MCPv2)
For long-running background operations, RayRabbit provides the `TaskEngine` (`rayrabbit/core/task_engine/`):
- **Transactional State Persistence**: SQLite-backed lifecycle tracking (`pending` $\rightarrow$ `running` $\rightarrow$ `completed` | `failed` | `paused`).
- **Dynamic Elicitation (`elicitation/create`)**: Request user feedback, confirmations, or additional input mid-flight without blocking LLM reasoning loops.

---

## 3. A2UI Protocol (v0.9.1) & Sovereign A2UI Agent

The **A2UI v0.9.1** protocol is the open specification for declarative reactive visual streaming over port **`:8006`**.

### Sovereign A2UI Agent (`SovereignA2UIAgent`)
RayRabbit includes a plug-and-play visual telemetry agent adaptable to any cognitive architecture:
- **Sequential LCEL Chains**
- **Hierarchical CrewAI Squads**
- **Human-in-the-Loop (HITL) Approvals**
- **Evaluator-Optimizer Loops**
- **AutoGen Multi-Agent Group Chats**

Agents translate internal reasoning into declarative JSON blocks (`---a2ui_JSON---`) rendered instantly in React/Web clients using visual lifecycle primitives:
* `beginRendering`: Initializes the visual surface in web clients.
* `surfaceUpdate`: Streams live reactive component updates.
* `updateDataModel`: Synchronizes data model state without redrawing the entire DOM.

---

!!! enterprise "Enterprise Performance & Sandboxed Runtimes"
    For high-throughput deployments exceeding 1,000 nodes, RayRabbit Enterprise introduces the **Robyn (Rust)** routing engine with sub-5ms latency and **Wasmtime (WebAssembly)** runtime sandboxing for secure tool execution perimeters.
    
    The **RayRabbit ARK** (Agentic Runtime Kit) automates A2A, MCP, and A2AUI routing, MAESTRO security filters, and enterprise KMS keys natively in a single operation. This ensures that all incoming and outgoing protocol packages are automatically audited, validated, and sandboxed at the kernel level, preserving framework autonomy.
