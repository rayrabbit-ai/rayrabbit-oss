# Infraestructura RayRabbit — AGENTS.md (Guía de ADN para Agentes de IA)

> **AUDIENCIA OBJETIVO**: Este documento está escrito explícitamente para Asistentes de Código IA (Antigravity, Cursor, Roo Code, Copilot, Claude Code) que operan sobre `rayrabbit-oss`. Define el ADN central, contratos y lineamientos para evolucionar limpiamente la Infraestructura de Interoperabilidad RayRabbit.

---

## 1. Filosofía y Visión Arquitectónica

RayRabbit **NO** es un monolito agéntico, ni es otro framework cognitivo (como LangChain, CrewAI, AutoGen, Microsoft Agent Framework, LlamaIndex o ejecutores agénticos propietarios). No impone bucles de ejecución ni secuestra los ciclos de razonamiento de los agentes.

En su lugar, RayRabbit es la **Infraestructura de Interoperabilidad de Próxima Generación L3 (AI TCP/IP + TLS + HTTP)**: una base soberana orientada a protocolos diseñada para interconectar frameworks de IA heterogéneos, SDKs y agentes autónomos a través de ecosistemas dispares.

* **Mediación Horizontal Neutral**: Media de forma fluida intenciones, transiciones de estado y llamadas a herramientas entre frameworks de IA heterogéneos sin apoderarse de sus bucles internos de razonamiento.
* **Topología en Estrella (Arquitectura Hub & Mesh)**: Núcleo Central Hub (`api/server.py` en `:8005`), Servidor MCP del Hub (`:8008`), Portal Visual A2UI (`:8006`), Servicios de Frameworks Cognitivos (`:8001-8003`) y Nodos SDK Dinámicos conectados mediante WebSockets persistentes (`ws://:8005/ws`).
* **Arquitectura Shared-Nothing**: Elimina puntos únicos de falla (SPOF) y dependencias de estado global. Cada agente y servicio mantiene 100% de soberanía de datos con bases de datos SQLite privadas y pares de claves criptográficas aisladas.
* **Protocolos Abiertos Nativos**: Implementa de forma nativa Google A2A (JSON-RPC 2.0), Anthropic MCP / MCPv2 (JSON Schema 2020-12) y A2UI v0.9.1.

---

## 2. Seguridad Central y Framework MAESTRO

Toda la comunicación en RayRabbit es Zero-Trust ("Nunca confíes, siempre verifica"):

1. **Handshake Mutual PoP**: Cada nodo/servicio debe realizar un apretón de manos criptográfico de Prueba de Posesión (PoP) sobre `/api/security/register` antes de unirse al bus.
2. **Firmas JWS por Mensaje**: Las cargas útiles inter-agente llevan encabezados `X-RayRabbit-JWS` (Serialización Compacta RFC 7515 con RSA-4096).
3. **Gestión de Claves**: Las claves se almacenan en reposo usando `StandaloneKeyStore` con cifrado **AES-256-GCM** (PBKDF2HMAC, 600,000 iteraciones).

---

## 3. Reglas Estrictas de Código y Desarrollo para Agentes IA

> [!WARNING]
> Cualquier agente de IA que edite este código DEBE aplicar estrictamente las siguientes reglas:

* **Regla de Agnosticismo de Entorno en Python**:
  - **JAMÁS** uses `os.path` o `sys.path`.
  - **SIEMPRE** usa `pathlib.Path` para manipulación de archivos e `importlib.resources` para activos de paquetes.
* **Sin Mocks en Código de Producción**:
  - Las ediciones de código deben ser 100% funcionales, listas para producción, sin fallbacks ficticios ni captura silenciosa de excepciones.
* **Desambiguación de Herramientas MCP**:
  - Las herramientas MCP registradas en el Hub DEBEN incluir metadatos dinámicos (`category` o `namespace`).
  - Los consumidores DEBEN inferir el caso de uso dinámicamente de los metadatos de `tools/list` (`tool.get("category")`). Nunca hardcodees listas de nombres de herramientas (`if name in [...]`).
* **Desarrollo Guiado por Especificaciones (Spec-Driven Development / SDD)**:
  - Cambios arquitectónicos complejos deben seguir el flujo de OpenSpec usando `/opsx:propose` y `/opsx:apply`.

---

## 4. Mapa de Documentación (Fuente de Verdad)

Para detalles arquitectónicos, contratos y lineamientos, los Agentes de Código IA deben consultar:

* 📄 **[`README.md`](./README.md)**: Arquitectura universal L3, topología en estrella, endpoints y quickstart.
* ⚙️ **[`openspec/config.yaml`](./openspec/config.yaml)**: Estándares de configuración y reglas de validación OpenSpec SDD.
* 📄 **[`CODING_ASSISTANTS_INTEGRATION.md`](./CODING_ASSISTANTS_INTEGRATION.md)**: Coordinación multi-asistente (Antigravity, Cursor, Claude Code, Codex).
* 📄 **[`SKILL.md`](./SKILL.md)**: ADN de agente soberano, contratos de endpoints e identidad Zero-Trust.
* 📄 **[`SECURITY_SETUP.md`](./SECURITY_SETUP.md)**: Criptografía Zero-Trust MAESTRO y almacenamiento de claves.
* 📄 **[`NODOS.md`](./NODOS.md)**: Catálogo de nodos y mapeo dinámico de puertos.

---

## 5. Contratos de Integración y Federación para Asistentes de Código IA

Cuando se le instruye a un Agente de Código IA generar o integrar un nuevo agente o servicio en RayRabbit, DEBE seleccionar una de las **3 Vías de Integración Soberana**:

1. **Vía A: Servicios de Framework Zero-Code (`communication_mode: 'bridge'`)**:
   - Envuelve frameworks cognitivos (CrewAI, LangChain, AutoGen, ADK) con un servidor REST FastAPI que exponga `openapi.json`.
   - Regístralo en `config.yaml` bajo `external_services` con `mode: local` o `mode: remote`.
2. **Vía B: Nodos SDK Dinámicos (`ws://:8005/ws`)**:
   - Usa `rayrabbit_client` (Python) o `@rayrabbit-client` (TypeScript).
   - Anota las herramientas con `@node.mcp_tool(category="<dominio>")`. El Hub genera automáticamente un `SovereignWebSocketProxy`.
3. **Vía C: Nodos de Protocolo Nativo (`communication_mode: 'p2p'`)**:
   - Construye objetos `Message` estándar de A2A JSON-RPC 2.0.
   - Ejecuta el apretón de manos Proof of Possession (PoP) RSA-4096 sobre `/api/security/register`.
