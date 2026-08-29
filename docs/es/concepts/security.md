# Marco de Seguridad MAESTRO & AIDA (Zero-Trust)

La seguridad en RayRabbit es un componente central e inyectado directamente en la capa de transporte mediante el marco **MAESTRO** (basado en el modelo de amenazas para IA agéntica de la Cloud Security Alliance - CSA) y el motor cognitivo **AIDA**.

---

## Zero-Trust Criptográfico Verificable

RayRabbit parte de la premisa de **Mutual Desconfianza**: ningún nodo confía implícitamente en otro, ni siquiera en conexiones `localhost`.

### 1. Handshake Mutual Proof of Possession (Mutual PoP)
Antes de admitir a cualquier agente o microservicio en el MessageBus o en el catálogo MCP, se ejecuta un handshake criptográfico bidireccional sobre `/api/security/register`:
- El nodo entrante presenta su identidad pública PEM y firma un desafío asimétrico.
- El Hub valida la firma contra su base de confianza local y emite una confirmación firmada con su propia identidad.

### 2. Firmas JWS Obligatorias en Cada Mensaje (RFC 7515 Compact)
Todo mensaje transmitido por HTTP o WebSocket incorpora cabeceras de no-repudio criptográfico:
- `X-RayRabbit-JWS`: Firma compacta RSA-4096 con algoritmo `RS256` / `PS256`.
- `X-RayRabbit-Agent-ID`: Identificador soberano del agente emisor.
- `X-RayRabbit-Bridge-Public-Key-PEM`: Clave pública PEM del bridge o nodo para validación inmediata.

### 3. Almacenamiento Criptográfico Seguro (`StandaloneKeyStore`)
En RayRabbit OSS, las claves privadas residen cifradas simétricamente en disco:
- **Algoritmo**: AES-256-GCM con autenticación de integridad de datos.
- **Derivación de Clave (KDF)**: PBKDF2HMAC con SHA-256 y **600,000 iteraciones**.
- **Gestión de Secretos**: Variables de entorno `RAYRABBIT_SECURITY_MASTER_SECRET` y `RAYRABBIT_SECURITY_SALT`.

### 4. Auditoría Inmutable Estilo Blockchain (WORM)
El `AuditManager` persiste cada evento, llamada a herramienta y delegación en SQLite privado:
- Cada registro almacena un `previous_hash` encadenado con SHA-256.
- Cualquier manipulación o alteración externa en la base de datos invalida de inmediato la cadena criptográfica completa.

### 5. Validación y Sanitización Profunda (`DataValidator`)
Intercepción preventiva en capas L4 y L7:
- Filtra inyecciones de comandos en el sistema operativo, SQLi, XSS y path traversal en entradas HTTP, WebSocket y CLI.

---

## AIDA Ouroboros & Runtimes Wasm (RayRabbit Enterprise)

Para infraestructuras corporativas con exposición a amenazas cognitivas avanzadas:

* **AIDA Ouroboros (Defensa Cognitiva Activa)**: Motor de evaluación LLM secundario de 2do nivel que analiza semánticamente las respuestas intermedias antes de permitir la ejecución de herramientas, neutralizando *prompt injections* recursivas, escalada de privilegios y cebos cognitivos (*Honeytokens*).
* **Sandboxing WebAssembly (`wasmtime`)**: Aislamiento estricto de ejecución de herramientas de IA con límites de consumo de CPU/GPU (*fuel metering*), techo de memoria stack de 1 MB y bloqueo total de sockets de red del host.
* **Integración Cloud KMS / HSM**: Custodia de identidades corporativas en hardware HSM (FIPS 140-2 Nivel 3) sin almacenar material de claves privadas en el disco de los contenedores.
