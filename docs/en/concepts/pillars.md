# The Six Architectural Pillars of RayRabbit

The architectural integrity and competitive advantage of RayRabbit rests upon six foundational technical pillars:

---

## 1. Native Multi-Protocol Support (A2A, MCPv2, A2UI)
RayRabbit implements open standards natively—Google's **A2A** (Agent-to-Agent v1.0), Anthropic's **MCP / MCPv2** (Model Context Protocol), and **A2UI v0.9.1** (Declarative Visual Telemetry)—without synthetic translation middleware or runtime lock-in.

---

## 2. Verifiable Zero-Trust Security (MAESTRO & AIDA)
Security is a cryptographic property of the transport layer under the **Mutual Zero-Trust** model:
* Bidirectional **Mutual Proof of Possession (Mutual PoP)** handshake on `/api/security/register`.
* Compact **JWS (RFC 7515)** signatures with **RSA-4096** on every single packet.
* Private key custody via `StandaloneKeyStore` with **AES-256-GCM** and 600,000 PBKDF2HMAC iterations.
* Immutable blockchain-style audit database in SQLite with SHA-256 hash chaining (`previous_hash`).

---

## 3. Absolute Framework Autonomy (Zero-Patch)
No vendor lock-in. Your LangChain chains, AutoGen chats, or CrewAI swarms remain 100% standard and pure. They execute inside isolated environments or containers. RayRabbit interfaces with them through sidecar **DeclarativeBridges** that consume OpenAPI schemas automatically with 0% code modifications required.

---

## 4. Decentralized & Shared-Nothing Architecture
There are no master coordinators, global singletons, or centralized shared state in RayRabbit. Every node is sovereign and manages its own private keys and internal memory, eliminating single points of failure (SPOF) and scaling horizontally.

---

## 5. Environment & Transport Agnosticism
RayRabbit is fully decoupled from physical infrastructure. Its message handlers support persistent WebSocket ingress (`/ws`), HTTP REST endpoints, dynamic `SovereignWebSocketProxy` tunnels, and multi-cloud WAN relays. The codebase uses agnostic `pathlib.Path` standards, enabling seamless portability between local workstations and enterprise Kubernetes clusters.

---

## 6. Declarative Visual Telemetry (A2UI v0.9.1)
The **A2UI** protocol and the **`SovereignA2UIAgent`** eliminate heavy frontend rebuilds. Agents emit declarative JSON blocks (`---a2ui_JSON---`) rendered on-the-fly in browser clients via reactive primitives (`surfaceUpdate`, `beginRendering`).

---

!!! enterprise "RayRabbit Enterprise: The ARK SDK Advantage"
    The open-source edition provides these pillars as modular building blocks. The **RayRabbit ARK** (Agentic Runtime Kit) automates enterprise governance, injects **Wasmtime (WebAssembly)** sandboxing, activates the **AIDA Ouroboros** cognitive defense engine, and manages corporate Cloud KMS/HSM keys across distributed clusters transparently.
