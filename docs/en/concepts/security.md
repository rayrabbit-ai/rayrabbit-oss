# MAESTRO & AIDA Security Framework (Zero-Trust)

Security in RayRabbit is not an external firewall: **it is a cryptographic property of the transport layer**. It is governed by the **MAESTRO** architecture (based on the Cloud Security Alliance - CSA Agentic AI threat model) and the **AIDA** cognitive defense engine.

---

## Verifiable Cryptographic Zero-Trust

RayRabbit operates on the premise of **Mutual Zero-Trust**: no node implicitly trusts another peer, even on `localhost` loopback connections.

### 1. Mutual Proof of Possession (Mutual PoP) Handshake
Before any agent, tool node, or framework microservice can access the MessageBus or MCP catalog, it must perform a bidirectional cryptographic handshake over `/api/security/register`:
- The connecting node presents its public PEM identity certificate and signs an asymmetric challenge nonce.
- The Hub verifies the signature against its local keystore and returns a signed confirmation payload.

### 2. Mandatory JWS Signatures on Every Message (RFC 7515 Compact)
Every payload transmitted over HTTP or WebSocket carries non-repudiation cryptographic headers:
- `X-RayRabbit-JWS`: Compact RSA-4096 signature using `RS256` / `PS256`.
- `X-RayRabbit-Agent-ID`: Sovereign agent identifier of the sender.
- `X-RayRabbit-Bridge-Public-Key-PEM`: Node or bridge public key PEM for instant out-of-band verification.

### 3. Encrypted Key Custody (`StandaloneKeyStore`)
In RayRabbit OSS, private keys are encrypted symmetrically at rest on disk:
- **Algorithm**: AES-256-GCM with authenticated data integrity.
- **Key Derivation (KDF)**: PBKDF2HMAC with SHA-256 and **600,000 iterations**.
- **Secret Management**: Configured via `RAYRABBIT_SECURITY_MASTER_SECRET` and `RAYRABBIT_SECURITY_SALT` environment variables.

### 4. Blockchain-Style Immutable Audit Trail (WORM)
The `AuditManager` writes every transaction, tool invocation, and task delegation to a private SQLite database:
- Each log entry contains a consecutive SHA-256 `previous_hash` digest.
- Any manual tampering or modification of historical records immediately invalidates the cryptographic chain.

### 5. Multi-Layer Sanitization (`DataValidator`)
Deep packet inspection across L4 and L7:
- Intercepts OS command injection, SQLi, XSS, and path traversal vectors across HTTP, WebSocket, and CLI inputs.

---

## AIDA Ouroboros & Wasm Runtimes (RayRabbit Enterprise)

For regulated corporate environments exposed to adversarial cognitive threats:

* **AIDA Ouroboros (Active Cognitive Defense)**: Secondary 2nd-level LLM evaluator that semantically inspects intermediate agent reasoning before permitting tool execution, neutralizing recursive prompt injections, privilege escalation attempts, and cognitive honeytokens.
* **WebAssembly Sandboxing (`wasmtime`)**: Hardened tool execution isolation with CPU/GPU fuel metering, 1 MB stack ceiling, and zero host network socket permissions.
* **Enterprise KMS / Cloud HSM**: Cryptographic key ring management backed by FIPS 140-2 Level 3 HSM hardware modules without storing private keys on container disk storage.
