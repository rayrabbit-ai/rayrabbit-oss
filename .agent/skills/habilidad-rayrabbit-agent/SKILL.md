---
name: habilidad-rayrabbit-agent
description: Expert skill for building, federating, and integrating autonomous Agent Nodes into the RayRabbit L3 Interoperability Infrastructure (AI TCP/IP + TLS + HTTP).
version: 0.2.0
author: RayRabbit Labs, Inc.
---

# SKILL: RayRabbit Sovereign Agent & Infrastructure Federation (L3)

## 1. Overview & Architectural DNA

**RayRabbit** is the **Next-Generation Interoperability Infrastructure L3 (AI TCP/IP + TLS + HTTP)**. It is **NOT** an orchestrator framework (like LangChain, CrewAI, or AutoGen).

RayRabbit operates as a neutral horizontal mediation layer to connect:
- **Heterogeneous Agents & Sovereign SDKs**: Atomic domain tools (Python `rayrabbit_client`, TypeScript `@rayrabbit-client`).
- **Proprietary Agents & CLI Assistants**: Google Antigravity CLI/SDK, Claude Code, Codex CLI/SDK, OpenHands, Hermes Agent, OpenClaw, and custom N-Agents.
- **Cognitive Frameworks**: CrewAI (:8001), LangChain (:8002), AutoGen (:8003), Microsoft Agent Framework (MAF), LlamaIndex, and any ADK/Framework via Declarative Bridges (`/openapi.json`).
- **A2UI Visual Portals**: Server-Driven UI (SDUI) telemetry emitting real-time JSON schemas for dynamic user interaction (:8006).

### The Shared-Nothing Principle
RayRabbit enforces a **Shared-Nothing Architecture**:
- **No Central Monolith / No SPOF**: Transport is decentralized; routing is dynamic P2P/Pub-Sub.
- **Data Sovereignty**: Each agent/service maintains private SQLite databases, local state, and isolated RSA-4096 cryptographic keypairs.

---

## 2. Directory Anatomy for Compliant Nodes

When constructing a new sovereign service in `examples/services/` or `rayrabbit/examples/`:

```text
my_agent_service/
├── [framework]_service.py  # Main FastAPI entrypoint and Declarative Bridge
├── protocols.py            # Pydantic models for A2A (JSON-RPC 2.0) and MCP
├── sovereign.py            # MAESTRO cryptographic identity, zero-trust handshake
├── [node_local].db         # Strictly local SQLite database (DO NOT SHARE)
└── requirements.txt        # Isolated dependencies
```

---

## 3. Required Protocols & Endpoints

Compliant RayRabbit nodes expose the following open standard endpoints:

### A. Google A2A Protocol (`POST /a2a`)
- Implements Google Agent-to-Agent JSON-RPC 2.0 standard.
- Accepts `Message` objects with cryptographic verification headers.

### B. Anthropic MCP / MCPv2 (`GET /mcp/tools` & `POST /mcp/call`)
- **`GET /mcp/tools`**: Returns dynamic MCP tool catalog (with `category` metadata).
- **`POST /mcp/call`**: Executes atomic domain actions with structured parameters.

### C. Declarative Execution (`POST /invoke`)
- Receives payload, validates JWS signature, executes framework logic, and publishes results back to the `MessageBus`.

---

## 4. MAESTRO Zero-Trust Cryptography

Every node joining the grid MUST follow Zero-Trust ("Never Trust, Always Verify"):
1. **Local Keypair**: Generates and manages local RSA-2048/4096 keys (`SovereignIdentity`).
2. **Mutual Proof of Possession (PoP)**: Executes registration handshake over `/api/security/register`.
3. **JWS Signatures**: All inter-agent payloads carry `X-RayRabbit-JWS`, `X-RayRabbit-Agent-ID`, and `X-RayRabbit-Bridge-Public-Key-PEM`.
4. **Environment Agnosticism**: ALWAYS use `pathlib.Path`, NEVER use `os.path` or `sys.path`.

---

## 5. Visual Telemetry: A2UI Protocol v0.9.1

RayRabbit decouples UI from backend logic through **A2UI Server-Driven UI (SDUI)**:
- Backend agents emit standardized A2UI JSON components to the `MessageBus`.
- The A2UI frontend dynamically renders cards, progress bars, interactive buttons, and telemetry widgets in real time without writing bespoke frontend code for each use case.