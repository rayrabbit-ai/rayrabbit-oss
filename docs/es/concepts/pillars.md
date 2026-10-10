# Los Seis Pilares Arquitectónicos de RayRabbit

La integridad de la arquitectura y la ventaja técnica de RayRabbit residen en seis pilares fundamentales:

---

## 1. Soporte Multi-Protocolo Nativo (A2A, MCPv2, A2UI)
RayRabbit implementa de forma nativa los protocolos abiertos **Google A2A** (Agent-to-Agent v1.0), **Anthropic MCP / MCPv2** (Model Context Protocol) y **A2UI v0.9.1** (Telemetría Visual Reactiva), sin añadir capas de traducción artificiales ni middleware propietario.

---

## 2. Seguridad Zero-Trust Nativa (MAESTRO & AIDA)
La seguridad está inyectada en el núcleo del MessageBus bajo la premisa de **Mutual Desconfianza**:
* Handshake bidireccional **Mutual Proof of Possession (Mutual PoP)** en `/api/security/register`.
* Firmas criptográficas compactas **JWS (RFC 7515)** con **RSA-4096** en cada mensaje.
* Custodia de claves en `StandaloneKeyStore` cifrado con **AES-256-GCM** y 600,000 iteraciones PBKDF2HMAC.
* Auditoría inmutable estilo blockchain en SQLite con encadenamiento de hashes SHA-256 (`previous_hash`).

---

## 3. Autonomía Absoluta del Framework (Zero-Patch)
RayRabbit no exige alterar sus cuadrillas de CrewAI, agentes de AutoGen o cadenas de LangChain. Permanecen 100% nativos y puros. Se ejecutan en procesos o contenedores aislados y RayRabbit interactúa con ellos a través de conectores **DeclarativeBridges** que parsean sus esquemas OpenAPI automáticamente con 0% de modificación al código fuente.

---

## 4. Arquitectura Descentralizada y Soberana (Shared-Nothing)
RayRabbit elimina los puntos únicos de fallo (SPOF) y la memoria compartida global. Cada nodo conectado es soberano, gestiona sus propias claves privadas y memoria interna, permitiendo al clúster escalar horizontalmente sin cuellos de botella de sincronización.

---

## 5. Agnosticismo de Entorno y Transporte
RayRabbit está totalmente desacoplado de la infraestructura física subyacente. Soporta canales de ingress persistentes por WebSocket (`/ws`), conexiones HTTP REST, proxies dinámicos `SovereignWebSocketProxy` y túneles WAN federados multicloud. El código utiliza rutas agnósticas con `pathlib.Path`, permitiendo migrar desde hosts locales a clústeres Kubernetes sin alteraciones.

---

## 6. Telemetría y Renderizado Declarativo (A2UI v0.9.1)
El protocolo **A2UI** y el agente **`SovereignA2UIAgent`** revolucionan la monitorización. En lugar de programar dashboards pesados ad-hoc en React, los agentes emiten bloques declarativos JSON (`---a2ui_JSON---`) que son interpretados y renderizados en caliente en el navegador mediante primitivas reactivas (`surfaceUpdate`, `beginRendering`).

---

!!! enterprise "RayRabbit Enterprise: La Ventaja del SDK Enterprise ARK"
    La versión de código abierto provee estos pilares como piezas de construcción modulares. La suite **RayRabbit ARK** (Agentic Runtime Kit) automatiza la gobernanza, inyecta sandboxing WebAssembly (`wasmtime`), activa el motor de defensa cognitiva **AIDA Ouroboros** y gestiona claves HSM corporativas en una única capa de infraestructura transparente.
