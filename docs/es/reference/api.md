# Referencia de Endpoints del Core API (Puerto 8005)

El **Servidor API Core de RayRabbit** escucha en el Puerto **8005**. Hospeda el **MessageBus** de mensajería asíncrona, las pasarelas telemáticas A2UI y el gateway de registro del Handshake JWS bidireccional.

---

## Endpoints REST API

### 1. Estado de Salud (Health Check)
Verifica si el servidor API Core y el framework RayRabbit se encuentran completamente activos.

* **Endpoint**: `/health`
* **Método**: `GET`
* **Respuesta exitosa `200 OK`**:
```json
{
  "status": "ok",
  "infrastructure_running": true
}
```

---

### 2. Estado de Preparación de Puentes (Readiness)
Retorna un diccionario detallando si los adaptadores **conector declarativos** han cargado y validado correctamente los contratos OpenAPI de sus servicios.

* **Endpoint**: `/api/bridges/readiness`
* **Método**: `GET`
* **Respuesta exitosa `200 OK`**:
```json
{
  "crewai_service_bridge": true,
  "langchain_service_bridge": true,
  "autogen_service_bridge": true
}
```

---

### 3. Prueba Manual de conector declarativo
Envía un prompt de prueba para inicializar manualmente un flujo lógico a través del conector declarativo.

* **Endpoint**: `/api/v1/test-bridge`
* **Método**: `POST`
* **Cuerpo de la Petición**:
```json
{
  "prompt": "Escribe un breve informe logístico."
}
```
* **Respuesta exitosa `200 OK`**:
```json
{
  "status": "success",
  "message": "Mensaje de prueba enviado. Revisa los logs para ver la respuesta del servicio.",
  "message_id": "msg-8f3d-992a"
}
```

---

### 4. Publicar Mensaje (MessageBus Ingestion Gateway)
Endpoint principal para inyectar transacciones o respuestas en caliente en el MessageBus central.

* **Endpoint**: `/api/publish-message`
* **Método**: `POST`
* **Cabeceras HTTP**:
  * **Modo JWS (Preferido)**:
    * `X-RayRabbit-JWS`: `header.payload.signature` (Sobres JWS compactos estándar JWS)
    * `X-RayRabbit-Agent-ID`: `langchain_service`
    * `X-RayRabbit-Bridge-Public-Key-PEM`: `PEM_Key_String` (Clave pública para validación dinámica)
  * **Modo Legacy**:
    * `X-RayRabbit-Signature`: `Hex_Signature_String`
    * `X-RayRabbit-Agent-ID`: `langchain_service`
* **Cuerpo de la Petición**:
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
* **Respuesta exitosa `200 OK`**:
```json
{
  "status": "success",
  "message": "Mensaje publicado exitosamente.",
  "message_id": "msg-8f3d-992a",
  "correlation_id": "corr-uuid-882"
}
```

!!! enterprise "Política de Confianza Local (Local Trust Policy - LTP)"
    Para garantizar la máxima velocidad de depuración y desarrollo ágil en localhost, RayRabbit aplica la **Política de Confianza Local (LTP)**. 
    
    Las peticiones que provienen estrictamente de `127.0.0.1` o `localhost` omiten la verificación perimetral del token JWS. Sin embargo, cualquier petición de red proveniente de una IP externa se bloquea de inmediato a menos que certifique sus firmas criptográficas, blindando su clúster.

---

### 5. Forzar Persistencia de Logs de Auditoría
Fuerza al motor de auditoría a vaciar la cola de transacciones de la memoria RAM y escribirlos directamente en la base de datos inmutable SQLite local.

* **Endpoint**: `/api/flush-audit-logs`
* **Método**: `POST`
* **Respuesta exitosa `200 OK`**:
```json
{
  "status": "success",
  "message": "Logs de auditoría vaciados exitosamente."
}
```

---

### 6. Registro de Identidad Dinámico (Gateway Handshake PoP)
Endpoint donde los agentes o servicios remotos registran su clave pública al inicializarse, concretando el **Handshake Bidireccional**. El Hub verifica la autenticidad validando una firma de reto (Proof of Possession, o PoP) con sello de tiempo y le devuelve al agente la clave pública del Hub.

* **Endpoint**: `/api/security/register`
* **Método**: `POST`
* **Cuerpo de la Petición**:
```json
{
  "agent_id": "langchain_service",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkq...",
  "timestamp": "1779836260",
  "signature": "firma_base64_del_reto...",
  "p2p_endpoint": "http://127.0.0.1:8002/a2a",
  "openapi_url": "http://127.0.0.1:8002/openapi.json"
}
```
* **Respuesta exitosa `200 OK`**:
```json
{
  "status": "success",
  "message": "Identidad registrada para langchain_service",
  "hub_public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkq..."
}
```

---

### 7. Eventos SSE del Agente A2UI
Canal SSE (Server-Sent Events) utilizado por el portal web para recibir las tarjetas dinámicas y layouts declarados por un agente de UI soberano específico.

* **Endpoint**: `/api/a2ui/events/{agent_id}`
* **Método**: `GET`
* **Respuesta exitosa `200 OK`**: `text/event-stream`

---

### 8. Despachador de Acciones A2UI
Recibe clics o interacciones de los usuarios desde la interfaz del navegador y los enruta de vuelta al topic de entrada del agente correspondiente en el MessageBus.

* **Endpoint**: `/api/a2ui/action`
* **Método**: `POST`
* **Cuerpo de la Petición**:
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
* **Respuesta exitosa `200 OK`**:
```json
{
  "status": "success",
  "message_id": "msg-8f3d-992a"
}
```

---

## Canales WebSocket del Hub Central

### 1. Ingress WebSocket Soberano (`/ws`)
Canal bidireccional persistente para conectar nodos SDK (`rayrabbit_client`, `@rayrabbit-client`), scripts y asistentes de código (Claude Code, OpenHands, Antigravity) sin requerir que expongan servidores HTTP locales.

* **Dirección de red**: `ws://127.0.0.1:8005/ws`
* **Protocolo**: `WebSocket / JSON-RPC 2.0`
* **Funcionalidad**: Registra el nodo en el `SovereignWebSocketProxy`, publica herramientas dinámicas en el catálogo MCP del Hub y canaliza peticiones bidireccionales con firmas JWS.

---

### 2. Hub MCP Server WebSocket (`:8008`)
Servidor nativo Model Context Protocol para descubrimiento y ejecución de herramientas de red.

* **Dirección de red**: `ws://127.0.0.1:8008`
* **Protocolo**: `WebSocket (MCP / MCPv2)`
* **Métodos Soportados**:
  * `tools/list`: Lista el catálogo unificado de herramientas con metadato dinámico `category`.
  * `tools/call`: Ejecuta herramientas síncronas o tareas asíncronas del `TaskEngine`.

---

### 3. Canal de Telemetría A2UI (`/ws/a2ui`)

* **Dirección de red**: `ws://127.0.0.1:8005/ws/a2ui/{correlation_id}`
* **Protocolo**: `WebSocket`
* **Propósito**: Transmitir actualizaciones telemáticas bidireccionales en formato **A2UI v0.9.1** a alta velocidad para renderizar superficies reactivas (`---a2ui_JSON---`, `surfaceUpdate`, `beginRendering`).
