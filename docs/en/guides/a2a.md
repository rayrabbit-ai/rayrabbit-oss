# Agent-to-Agent (A2A) Specification

The **A2A** protocol standardizes task invocation, negotiation, and payload exchange between heterogeneous agents on the RayRabbit network. It is built upon an asynchronous, cryptographically secured **JSON-RPC 2.0** structure.

---

## JSON-RPC 2.0 Structure

RayRabbit A2A packets strictly enforce the JSON-RPC 2.0 specification, wrapping payloads in standard envelopes:

### 1. Request Envelope
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/create",
  "params": {
    "prompt": "Evaluate logistics capacity for region 4",
    "priority": "high",
    "correlation_id": "corr-uuid-992a"
  },
  "id": "req-8b3c"
}
```

### 2. Success Response Envelope
```json
{
  "jsonrpc": "2.0",
  "result": {
    "output": "Fleet capacity verified. 14 vehicles active.",
    "correlation_id": "corr-uuid-992a"
  },
  "id": "req-8b3c"
}
```

### 3. Failure Response Envelope
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": "The target node does not support capability: tasks/create"
  },
  "id": "req-8b3c"
}
```

---

## Cryptographic Handshake Protocol

When nodes communicate directly via **P2P Mode** (without Core Hub mediation), they must establish trust before parsing instructions. This is managed by the **KeyExchangeAgent** and the local key store:

```
[Agent A]                                                     [Agent B]
    │                                                             │
    │ 1. Handshake Request: Hello + Agent Card A (Public Key A)   │
    ├────────────────────────────────────────────────────────────>│
    │                                                             │
    │ 2. Handshake Verification (Verifies Card A in Trust Store)  │
    │                                                             │
    │ 3. Handshake Response: Accept + Agent Card B (Public Key B) │
    │<────────────────────────────────────────────────────────────┤
    │                                                             │
    │ 4. Trust Confirmed: Both exchange JWS-signed JSON-RPC payloads.
```

---

## Agent Cards & Static Trust Store

An **Agent Card** is a signed declarative document that defines an agent's identity, public keys, and routing address.

In RayRabbit OSS, these cards are aggregated inside the static `AGENTS.md` file in the root directory. This file acts as the decentralized "Phonebook" of the network.

An agent resolves identity as follows:
1. When requesting Agent B, Agent A reads the `AGENTS.md` block corresponding to Agent B's ID.
2. It extracts the routing URL and public key.
3. It saves the public key inside the local key store directory.
4. Any future payload received from Agent B must match the signature derived from this exact public key. Payloads signed with untrusted keys are dropped instantly with a `401 Unauthorized` network error, neutralizing spoofing attacks.
