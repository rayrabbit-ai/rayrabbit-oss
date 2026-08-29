# Core API Server Endpoints (Port 8005)

The **RayRabbit Core API Server** runs on Port **8005**. It orchestrates the centralized **MessageBus**, the dynamic A2UI visual telemetry streams, and the P2P JWS Handshake registration gateway.

---

## REST API Endpoints

### 1. Health Status
Check if the API server and the underlying RayRabbit Framework are fully operational.

* **Endpoint**: `/health`
* **Method**: `GET`
* **Response `200 OK`**:
```json
{
  "status": "ok",
  "infrastructure_running": true
}
```

---

### 2. Bridges Readiness Status
Queries the status of active **declarative connectors** connected to external microservices.

* **Endpoint**: `/api/bridges/readiness`
* **Method**: `GET`
* **Response `200 OK`**:
```json
{
  "crewai_service_bridge": true,
  "langchain_service_bridge": true,
  "autogen_service_bridge": true
}
```

---

### 3. Declarative Connector Manual Test
Manually post a prompt to trigger a declarative connector workflow for testing.

* **Endpoint**: `/api/v1/test-bridge`
* **Method**: `POST`
* **Payload**:
```json
{
  "prompt": "Write a short logistics insight."
}
```
* **Response `200 OK`**:
```json
{
  "status": "success",
  "message": "Mensaje de prueba enviado. Revisa los logs para ver la respuesta del servicio.",
  "message_id": "msg-8f3d-992a"
}
```

---

### 4. Publish Message (MessageBus Ingestion Gateway)
Submit a signed message payload to be enqueued on the central MessageBus.

* **Endpoint**: `/api/publish-message`
* **Method**: `POST`
* **Headers**:
  * **JWS Mode (Preferred)**:
    * `X-RayRabbit-JWS`: `header.payload.signature` (JWS standard Compact format)
    * `X-RayRabbit-Agent-ID`: `langchain_service`
    * `X-RayRabbit-Bridge-Public-Key-PEM`: `PEM_Key_String` (Dynamic public identity key)
  * **Legacy Mode**:
    * `X-RayRabbit-Signature`: `Hex_Signature_String`
    * `X-RayRabbit-Agent-ID`: `langchain_service`
* **Payload**:
```json
{
  "sender_id": "langchain_service",
  "sender_name": "LangChain Service",
  "recipient_id": "langchain_response_listener",
  "message_type": "response",
  "correlation_id": "corr-uuid-882",
  "content": {
    "package_id": "PKG-2026",
    "sap_analysis": "On track"
  }
}
```
* **Response `200 OK`**:
```json
{
  "status": "success",
  "message": "Mensaje publicado exitosamente.",
  "message_id": "msg-8f3d-992a",
  "correlation_id": "corr-uuid-882"
}
```

!!! enterprise "Zero-Trust Edge Case: Local Trust Policy (LTP)"
    To enable seamless local loopback development and debugging, RayRabbit applies a **Local Trust Policy (LTP)**. 
    
    Requests originating from `127.0.0.1` or `localhost` bypass mandatory JWS signature validation at the Hub gatekeeper. However, requests originating from any remote IP address are strictly blocked unless verified cryptographically, protecting your production perimeter.

---

### 5. Flush Audit Logs
Forces the audit engine to immediately flush memory-queued transactions to the persistent structured local audit database.

* **Endpoint**: `/api/flush-audit-logs`
* **Method**: `POST`
* **Response `200 OK`**:
```json
{
  "status": "success",
  "message": "Logs de auditoría vaciados exitosamente."
}
```

---

### 6. Dynamic Identity Registration (Handshake PoP Gateway)
Allows external microservices to dynamically register their public keys, establishing a **Bidirectional Handshake**. The Hub validates identity by verifying a signature challenge (Proof of Possession, or PoP) containing a timestamp.

* **Endpoint**: `/api/security/register`
* **Method**: `POST`
* **Payload**:
```json
{
  "agent_id": "langchain_service",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkq...",
  "timestamp": "1779836260",
  "signature": "base64_signature_of_challenge...",
  "p2p_endpoint": "http://127.0.0.1:8002/a2a",
  "openapi_url": "http://127.0.0.1:8002/openapi.json"
}
```
* **Response `200 OK`**:
```json
{
  "status": "success",
  "message": "Identidad registrada para langchain_service",
  "hub_public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkq..."
}
```

---

### 7. A2UI SSE Events Stream
Server-Sent Events (SSE) channel used by the portal to monitor UI events emitted by a specific sovereign agent.

* **Endpoint**: `/api/a2ui/events/{agent_id}`
* **Method**: `GET`
* **Response `200 OK`**: `text/event-stream`

---

### 8. A2UI UI Action Dispatcher
Posts browser user actions or button clicks from the A2UI portal back to the target agent on the MessageBus.

* **Endpoint**: `/api/a2ui/action`
* **Method**: `POST`
* **Payload**:
```json
{
  "agent_id": "logistics_ui_manager",
  "surface_id": "logistics_dashboard",
  "action": {
    "name": "dispatch_truck",
    "params": {"carrier": "DHL", "driver_id": "DRV-01"}
  }
}
```
* **Response `200 OK`**:
```json
{
  "status": "success",
  "message_id": "msg-8f3d-992a"
}
```

---

## Central Hub WebSocket Channels

### 1. Sovereign WebSocket Ingress (`/ws`)
Persistent bidirectional channel to connect SDK nodes (`rayrabbit_client`, `@rayrabbit-client`), custom scripts, and autonomous coding assistants (Claude Code, OpenHands, Antigravity) without requiring them to host local HTTP servers.

* **Network Address**: `ws://127.0.0.1:8005/ws`
* **Protocol**: `WebSocket / JSON-RPC 2.0`
* **Functionality**: Registers the client node in `SovereignWebSocketProxy`, publishes dynamic tools to the Hub's MCP catalog, and routes bidirectional requests with JWS signatures.

---

### 2. Hub MCP Server WebSocket (`:8008`)
Native Model Context Protocol server for network capability discovery and execution.

* **Network Address**: `ws://127.0.0.1:8008`
* **Protocol**: `WebSocket (MCP / MCPv2)`
* **Supported Methods**:
  * `tools/list`: Lists the unified tool catalog with dynamic `category` metadata.
  * `tools/call`: Executes synchronous tools or dispatches asynchronous `TaskEngine` tasks.

---

### 3. A2UI Telemetry Channel (`/ws/a2ui`)

* **Network Address**: `ws://127.0.0.1:8005/ws/a2ui/{correlation_id}`
* **Protocol**: `WebSocket`
* **Purpose**: High-speed bidirectional streaming of **A2UI v0.9.1** declarative JSON updates (`---a2ui_JSON---`, `surfaceUpdate`, `beginRendering`).
