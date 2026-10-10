# AGENTS.md Contract Catalog

RayRabbit relies on a static manifest file called **`AGENTS.md`** located in your project's root folder to resolve micro-service locations and cryptographic identities. This document acts as the decentralized "Phonebook" of your agentic network.

---

## Structure of AGENTS.md

The Core Hub reads `AGENTS.md` at boot, parsing each agentic block to initialize gateways. The file must follow this exact markdown format:

```markdown
## 1. Logistics Orchestrator (LangChain Agent)
- **ID**: `logistics_manager`
- **Name**: Global Logistics Manager
- **Protocols**: `["a2a", "mcp", "http"]`
- **Capabilities**: `["order_analysis", "inventory_dispatch", "conflict_resolution", "analyze_order", "track_package"]`
- **a2a**: `http://127.0.0.1:8002/a2a`
- **mcp**: `http://127.0.0.1:8002/mcp`
- **mcp_tools**: `http://127.0.0.1:8002/mcp/tools`
- **mcp_call**: `http://127.0.0.1:8002/mcp/call`
- **Description**: Analyzes customer requests and coordinates tools to fulfill orders.
```

---

## Parameter Reference

* **ID**: The unique identifier of the agent. Used to route messages inside the MessageBus and check signature matches inside the local keystore.
* **Protocols**: List of protocols supported by the node's adapters.
* **Capabilities**: List of logical methods or MCP tools exposed by this service.
* **a2a / mcp endpoints**: The network URLs pointing to the node's listening port. Used by DeclarativeBridges to forward payload traffic.

---

!!! enterprise "Dynamic Cryptographic Directory Service"
    For large-scale dynamic environments containing numerous transient agent instances, RayRabbit Enterprise provides a dynamic, cryptographically signed directory service. It automates agent registration, handles live routing resolution, and manages secure key rotation without manual configuration file updates.
