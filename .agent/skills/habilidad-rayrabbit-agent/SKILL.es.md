---
name: habilidad-rayrabbit-agent
description: Habilidad experta para construir, federar e integrar Nodos Agentes autónomos en la Infraestructura de Interoperabilidad RayRabbit L3 (AI TCP/IP + TLS + HTTP).
version: 0.2.0
author: RayRabbit Labs, Inc.
---

# 🐇 SKILL: Agente Soberano y Federación de Infraestructura RayRabbit (L3)

## 1. Visión General y ADN Arquitectónico

**RayRabbit** es la **Infraestructura de Interoperabilidad de Próxima Generación L3 (AI TCP/IP + TLS + HTTP)**. **NO** es un framework orquestador (como LangChain, CrewAI o AutoGen).

RayRabbit opera como una capa neutral de mediación horizontal para interconectar:
- **Agentes Heterogéneos y SDKs Soberanos**: Herramientas atómicas de dominio (Python `rayrabbit_client`, TypeScript `@rayrabbit-client`).
- **Agentes Propietarios y Asistentes CLI**: Google Antigravity CLI/SDK, Claude Code, Codex CLI/SDK, OpenHands, Hermes Agent, OpenClaw y N-Agentes personalizados.
- **Frameworks Cognitivos**: CrewAI (:8001), LangChain (:8002), AutoGen (:8003), Microsoft Agent Framework (MAF), LlamaIndex y cualquier ADK/Framework vía Declarative Bridges (`/openapi.json`).
- **Portales Visuales A2UI**: Telemetría Server-Driven UI (SDUI) emitiendo esquemas JSON en tiempo real para interacción dinámica con el usuario (:8006).

### El Principio Shared-Nothing
RayRabbit aplica una **Arquitectura Shared-Nothing**:
- **Sin Monolito Central / Sin SPOF**: El transporte es descentralizado; el enrutamiento es dinámico P2P/Pub-Sub.
- **Soberanía de Datos**: Cada agente/servicio mantiene bases de datos SQLite privadas, estado local y pares de claves criptográficas RSA-4096 aisladas.

---

## 2. Anatomía de Directorios para Nodos Cumplientes

Al construir un nuevo servicio soberano en `examples/services/` o `rayrabbit/examples/`:

```text
mi_servicio_agente/
├── [framework]_service.py  # Punto de entrada principal FastAPI y Declarative Bridge
├── protocols.py            # Modelos Pydantic para A2A (JSON-RPC 2.0) y MCP
├── sovereign.py            # Identidad criptográfica MAESTRO, handshake Zero-Trust
├── [nodo_local].db         # Base de datos SQLite estrictamente local (NO COMPARTIR)
└── requirements.txt        # Dependencias aisladas
```

---

## 3. Protocolos y Endpoints Requeridos

Los nodos cumplientes de RayRabbit exponen los siguientes endpoints basados en estándares abiertos:

### A. Protocolo Google A2A (`POST /a2a`)
- Implementa el estándar Google Agent-to-Agent JSON-RPC 2.0.
- Acepta objetos `Message` con encabezados de verificación criptográfica.

### B. Anthropic MCP / MCPv2 (`GET /mcp/tools` y `POST /mcp/call`)
- **`GET /mcp/tools`**: Retorna el catálogo dinámico de herramientas MCP (con metadatos `category`).
- **`POST /mcp/call`**: Ejecuta acciones atómicas de dominio con parámetros estructurados.

### C. Ejecución Declarativa (`POST /invoke`)
- Recibe la carga útil, valida la firma JWS, ejecuta la lógica del framework y publica los resultados de vuelta en el `MessageBus`.

---

## 4. Criptografía Zero-Trust MAESTRO

Cada nodo que se une a la malla DEBE seguir Zero-Trust ("Nunca confíes, siempre verifica"):
1. **Par de Claves Local**: Genera y administra claves locales RSA-2048/4096 (`SovereignIdentity`).
2. **Mutual Proof of Possession (PoP)**: Ejecuta el apretón de manos de registro sobre `/api/security/register`.
3. **Firmas JWS**: Todas las cargas útiles inter-agente llevan `X-RayRabbit-JWS`, `X-RayRabbit-Agent-ID` y `X-RayRabbit-Bridge-Public-Key-PEM`.
4. **Agnosticismo de Entorno**: SIEMPRE usa `pathlib.Path`, NUNCA uses `os.path` o `sys.path`.

---

## 5. Telemetría Visual: Protocolo A2UI v0.9.1

RayRabbit desacopla la UI de la lógica de backend mediante **A2UI Server-Driven UI (SDUI)**:
- Los agentes del backend emiten componentes JSON A2UI estandarizados al `MessageBus`.
- El frontend A2UI renderiza dinámicamente tarjetas, barras de progreso, botones interactivos y widgets de telemetría en tiempo real sin tener que programar interfaces a medida para cada caso de uso.
