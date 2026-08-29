# RayRabbit Infrastructure — AGENTS.md (AI Agent DNA Guide)

> **TARGET AUDIENCE**: This document is explicitly written for AI Coding Assistants (Antigravity, Cursor, Roo Code, Copilot, Claude Code) operating on `rayrabbit-oss`. It defines the core DNA, contracts, and guidelines to evolve the RayRabbit Interoperability Infrastructure cleanly.

---

## 1. Architectural Philosophy & Vision

RayRabbit is **NOT** an agentic monolith, nor is it another cognitive framework (such as LangChain, CrewAI, AutoGen, Microsoft Agent Framework, LlamaIndex, or proprietary runtime orchestrators). It does not impose execution loops or hijack agent reasoning cycles.

Instead, RayRabbit is the **Next-Generation Interoperability Infrastructure L3 (AI TCP/IP + TLS + HTTP)** — a sovereign, protocol-driven foundation designed to interconnect heterogeneous AI frameworks, SDKs, and autonomous agents across disparate ecosystems.

* **Neutral Horizontal Mediation**: Seamlessly mediates intentions, state transitions, and tool calls between heterogeneous AI frameworks without taking over their internal reasoning loops.
* **Star Topology (Hub & Mesh Architecture)**: Central Hub Core (`api/server.py` on `:8005`), Hub MCP Server (`:8008`), A2UI Visual Portal (`:8006`), Cognitive Framework Services (`:8001-8003`), and Dynamic SDK Nodes connected via persistent WebSockets (`ws://:8005/ws`).
* **Shared-Nothing Architecture**: Eliminates single points of failure (SPOF) and global state dependencies. Each agent and service maintains 100% data sovereignty with private SQLite databases and isolated cryptographic keypairs.
* **Native Open Protocols**: Natively implements Google A2A (JSON-RPC 2.0), Anthropic MCP / MCPv2 (JSON Schema 2020-12), and A2UI v0.9.1.

---

## 2. Core Security & MAESTRO Framework

All communication across RayRabbit is Zero-Trust ("Never Trust, Always Verify"):

1. **Mutual PoP Handshake**: Every node/service must perform a Mutual Proof of Possession (PoP) cryptographic handshake over `/api/security/register` before joining the bus.
2. **JWS Per-Message Signatures**: Inter-agent payloads carry `X-RayRabbit-JWS` headers (RFC 7515 Compact Serialization with RSA-4096).
3. **Key Management**: Keys are stored at rest using `StandaloneKeyStore` with **AES-256-GCM** encryption (PBKDF2HMAC, 600,000 iterations).

---

## 3. Strict Coding & Development Rules for AI Agents

> [!WARNING]
> Any AI agent editing this codebase MUST enforce the following rules strictly:

* **Environment Agnosticism Rule in Python**:
  - **NEVER** use `os.path` or `sys.path`.
  - **ALWAYS** use `pathlib.Path` for file manipulation and `importlib.resources` for package assets.
* **No Mocking in Production Code**:
  - Code edits must be 100% functional, production-ready, without dummy fallbacks or silent exception swallowing.
* **MCP Tool Disambiguation**:
  - MCP tools registered in the Hub MUST include dynamic metadata (`category` or `namespace`).
  - Consumers MUST infer `current_use_case` dynamically from `tools/list` metadata (`tool.get("category")`). Never hardcode lists of tool names (`if name in [...]`).
* **Spec-Driven Development (SDD)**:
  - Complex architectural changes must follow the OpenSpec workflow using `/opsx:propose` and `/opsx:apply`.

---

## 4. Documentation Map (Source of Truth)

For architectural details, contracts, and guidelines, AI Coding Agents must consult:

* 📄 **[`README.md`](./README.md)**: Universal L3 architecture, star topology, endpoints, and quickstart.
* ⚙️ **[`openspec/config.yaml`](./openspec/config.yaml)**: OpenSpec SDD configuration standards and validation rules.
* 📄 **[`CODING_ASSISTANTS_INTEGRATION.md`](./CODING_ASSISTANTS_INTEGRATION.md)**: Multi-assistant coordination (Antigravity, Cursor, Claude Code, Codex).
* 📄 **[`SKILL.md`](./SKILL.md)**: Sovereign agent DNA, endpoint contracts, and Zero-Trust identity.
* 📄 **[`SECURITY_SETUP.md`](./SECURITY_SETUP.md)**: MAESTRO Zero-Trust cryptography and key storage.
* 📄 **[`NODOS.md`](./NODOS.md)**: Node catalog and dynamic port mapping.

---

## 5. Federation Integration Contracts for AI Coding Assistants

When an AI Coding Agent is instructed to generate or integrate a new agent or service into RayRabbit, it MUST select one of the **3 Sovereign Integration Paths**:

1. **Path A: Zero-Code Framework Services (`communication_mode: 'bridge'`)**:
   - Wrap cognitive frameworks (CrewAI, LangChain, AutoGen, ADK) with a FastAPI REST server exposing `openapi.json`.
   - Register in `config.yaml` under `external_services` with `mode: local` or `mode: remote`.
2. **Path B: Dynamic SDK Nodes (`ws://:8005/ws`)**:
   - Use `rayrabbit_client` (Python) or `@rayrabbit-client` (TypeScript).
   - Annotate tools with `@node.mcp_tool(category="<domain>")`. The Hub automatically spawns a `SovereignWebSocketProxy`.
3. **Path C: Native Protocol Nodes (`communication_mode: 'p2p'`)**:
   - Construct standard A2A JSON-RPC 2.0 `Message` objects.
   - Execute Mutual Proof of Possession (PoP) RSA-4096 handshake over `/api/security/register`.

