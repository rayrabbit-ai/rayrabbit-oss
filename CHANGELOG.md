# Changelog

All notable changes to **RayRabbit OSS** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-08-25 (Public Developer Preview)

### Added
- **Core Hub & Central Star Topology**:
  - FastAPI Core API Hub (`:8005`) with `/api/publish-message`, `/api/health`, and WebSocket ingress `/ws`.
  - Native Hub MCP Server (`:8008`) for unified dynamic tool catalog discovery (`tools/list`) and invocation (`tools/call`).
  - Asynchronous pub/sub `MessageBus` with synchronized `send_and_wait` and `OfflineToleranceService`.
- **Open Protocol Implementation**:
  - Google Agent-to-Agent (**A2A**) JSON-RPC 2.0 protocol implementation for direct inter-agent messaging.
  - Anthropic Model Context Protocol (**MCP / MCPv2**) with asynchronous `TaskEngine` and MRTR (Multi Round-Trip Requests) support.
  - **A2UI v0.9.1** Visual Telemetry Protocol with declarative micro-render engine on port `8006` and `SovereignA2UIAgent`.
- **MAESTRO Security Zero-Trust Layer**:
  - Mutual Proof of Possession (**Mutual PoP**) challenge handshake on `/api/security/register`.
  - Per-message **JWS RFC 7515 Compact** signatures with RSA-4096.
  - Symmetrical **AES-256-GCM** keystore encryption with PBKDF2HMAC (600,000 iterations) via `StandaloneKeyStore`.
  - Immutable append-only blockchain-style audit logging in SQLite with SHA-256 hash chaining.
  - Multi-layer `DataValidator` for SQLi, XSS, and path traversal protection.
- **Federation & Sovereign Integration**:
  - **Path A**: Zero-code DeclarativeBridges for cognitive frameworks (CrewAI `:8001`, LangChain `:8002`, AutoGen `:8003`).
  - **Path B**: Dynamic SDK sovereign nodes via WebSocket (`ws://:8005/ws`) and `@node.mcp_tool` decorator.
  - **Path C**: Native A2A/MCP protocol nodes with mutual cryptographic handshake.
- **Client SDKs**:
  - Official Python SDK (`rayrabbit_client`) under Apache-2.0.
  - Official TypeScript SDKs (`@rayrabbit/client`, `@rayrabbit/a2ui`) under Apache-2.0.
- **CLI & Developer Experience**:
  - Unified CLI `rayrabbit` with `start`, `cluster`, `chat`, `install`, and `--version` commands.
  - Zero-friction bootstrap scripts for Windows (`setup_dev.bat`), PowerShell (`setup_dev.ps1`), and Linux/macOS (`setup_dev.sh`).
