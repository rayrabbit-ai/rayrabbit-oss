# RayRabbit Client SDKs (Apache 2.0)

This directory contains official public client libraries and SDKs for **RayRabbit**, licensed under the **Apache License 2.0** for permissive commercial and open-source adoption without copyleft restrictions.

---

## RayRabbit Star Topology & Architecture

RayRabbit is the **Next-Generation Universal Interoperability Infrastructure L3** for AI agents (AI TCP/IP + TLS + HTTP). It is not a cognitive framework monolith, but a distributed star topology where the central infrastructure (**Hub Core**) connects three primary actor families in its reference implementation, with an agnostic architecture designed to support additional cognitive frameworks (Microsoft Agent Framework, LlamaIndex, Google ADKs), domain SDKs, and proprietary agent assistants:

```
                  ┌──────────────────────────────────────────────┐
                  │          RayRabbit CORE Hub (8005)           │
                  │  - MessageBus (Central Pub/Sub)              │
                  │  - MAESTRO Security (JWS + Zero-Trust)       │
                  │  - Hub MCP/MCPv2 Server (ws://127.0.0.1:8008)│
                  └──────────────────────┬───────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
┌───────────────────────┐    ┌───────────────────────┐    ┌───────────────────────┐
│ Sovereign Frameworks  │    │  Sovereign SDK Nodes  │    │   A2UI Visual Portal  │
│ (Ports 8001, 8002, ..)│    │ (Clients: Python/JS)  │    │      (Port 8006)      │
├───────────────────────┤    ├───────────────────────┤    ├───────────────────────┤
│ - CrewAI (8001)       │    │ - Logistics SDK Node  │    │ - Universal UI Agent  │
│ - AutoGen (8003)      │    │ - Crypto Trader Node  │    │ - A2UI Micro-Render   │
│ - LangChain (8002)    │    │ - Custom Organization │    │                       │
└───────────────────────┘    └───────────────────────┘    └───────────────────────┘
```

### 1. Framework Cognitive Services (CrewAI, AutoGen, LangChain)
Independent federated microservices running in isolated Python virtual environments (ports `8001-8003`). They run native multi-agent reasoning loops with their own LLMs and expose cognitive capabilities (`execute_crew_task`, `start_autogen_chat`, `run_lcel_chain`).

### 2. Sovereign SDK Nodes (Python & JavaScript Clients)
Lightweight domain applications built with the SDKs in this folder. They connect via **persistent WebSockets (`ws://127.0.0.1:8005/ws`)** to the Hub and dynamically register domain tools in the **MCP Registry (`ws://127.0.0.1:8008`)** without spinning up standalone HTTP servers.

### 3. A2UI Visual Portal & User Ingress
Real-time Server-Driven UI render portal (port `8006`), projecting live task events into dynamic interactive dashboards.

---

## End-to-End Interoperability Flow (E2E)

1. **A2UI Ingress:** The A2UI portal receives the user intention.
2. **A2A Dispatch:** The Hub routes the intention via A2A/JWS to the specialized cognitive service (e.g. `crewai_service`).
3. **Framework Execution:** CrewAI or AutoGen orchestrates autonomous agents with their private LLMs.
4. **MCP Discovery:** When a CrewAI agent needs an action (e.g. query SAP TM or Binance), it queries the Hub's MCP registry.
5. **SDK Node Invocations:** The Hub asynchronously routes the tool call to the connected **Sovereign SDK Node** over WebSockets.
6. **Telemetry Projection:** The SDK Node returns real data to the Hub, the Hub forwards to CrewAI/AutoGen, and visual telemetry streams to A2UI.

---

## SDK Maturity Status

| SDK / Client | Language | Maturity Status | Scope |
| :--- | :---: | :---: | :--- |
| **`python/rayrabbit_client/`** | Python 3.10+ | **Stable / Preview (v0.1.0)** | Official Python SDK for creating `RayRabbitNode` instances with `@node.tool` decorators, WebSockets `/ws`, and automated MCP proxying. |
| **`javascript/`** | TypeScript / Node | **🚧 Active Development** | Upcoming official TypeScript SDK for connecting JS agents and tools to the sovereign mesh. |
| **`antigravity/`** | Plugin / MCP | **Stable (v0.1.0)** | Official plugin and embedded MCP server for bidirectional Google Antigravity integration. |

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# RayRabbit Client SDKs (Apache 2.0)

Este directorio contiene las librerías cliente y SDKs públicos oficiales de **RayRabbit**, licenciados bajo **Apache License 2.0** para un uso comercial y de código abierto sin restricciones de copyleft.

---

## Topología en Estrella de RayRabbit

RayRabbit es la **Infraestructura de Interoperabilidad Universal L3** para agentes de IA (AI TCP/IP + TLS + HTTP). No es un framework orquestador monolítico, sino una arquitectura distribuida en estrella donde la infraestructura central (el **Hub Core**) conecta actualmente tres familias principales de actores en su implementación de referencia, con una arquitectura abierta y agnóstica diseñada para expandir su soporte en próximos releases a múltiples frameworks cognitivos adicionales (Microsoft Agent Framework, LlamaIndex, Google ADKs), SDKs de dominio y asistentes agénticos propietarios:

```
                  ┌──────────────────────────────────────────────┐
                  │          RayRabbit CORE Hub (8005)           │
                  │  - MessageBus (Pub/Sub Central)              │
                  │  - MAESTRO Security (JWS + Zero-Trust)       │
                  │  - Hub MCP/MCPv2 Server (ws://127.0.0.1:8008)│
                  └──────────────────────┬───────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
┌───────────────────────┐    ┌───────────────────────┐    ┌───────────────────────┐
│ Sovereign Frameworks  │    │  Sovereign SDK Nodes  │    │   A2UI Visual Portal  │
│ (Ports 8001, 8002, ..)│    │ (Clients: Python/JS)  │    │      (Port 8006)      │
├───────────────────────┤    ├───────────────────────┤    ├───────────────────────┤
│ - CrewAI (8001)       │    │ - Logistics SDK Node  │    │ - Universal UI Agent  │
│ - AutoGen (8003)      │    │ - Crypto Trader Node  │    │ - A2UI Micro-Render   │
│ - LangChain (8002)    │    │ - Custom Organization │    │                       │
└───────────────────────┘    └───────────────────────┘    └───────────────────────┘
```

### 1. Servicios Cognitivos Framework (CrewAI, AutoGen, LangChain)
Microservicios federados independientes que corren en sus propios entornos virtuales (puertos `8001-8003`). Ejecutan razonamiento multi-agente nativo con sus propios LLMs y exponen capacidades cognitivas (`execute_crew_task`, `start_autogen_chat`, `run_lcel_chain`).

### 2. Nodos SDK / Agentes Custom (Clientes Python & JavaScript)
Aplicaciones ligeras de negocio construidas con los SDKs de esta carpeta. Se conectan por **WebSocket (`ws://127.0.0.1:8005/ws`)** al Hub y registran dinámicamente sus herramientas en el **MCP Registry Server (`ws://127.0.0.1:8008`)** sin necesidad de levantar servidores HTTP complejos.

### 3. Portal A2UI / Pasarela de Usuario
Servicio de renderizado y comunicación con el usuario final (puerto `8006`), convirtiendo eventos de tareas en interfaces gráficas interactivas en tiempo real.

---

## Flujo de Interoperabilidad de Extremo a Extremo (E2E)

1. **Solicitud A2UI:** El portal A2UI recibe la consulta del usuario.
2. **Despacho A2A:** El Hub enruta la intención vía A2A/JWS al Servicio Cognitivo especializado (ej. `crewai_service`).
3. **Ejecución del Framework:** CrewAI o AutoGen inician su cuadrilla de agentes autónomos con su propio LLM.
4. **Consulta MCP:** Cuando un agente de CrewAI necesita ejecutar una acción de dominio (ej. consultar la BD de SAP TM o Binance), consulta el catálogo MCP del Hub.
5. **Invocación al SDK Node:** El Hub enruta asíncronamente la llamada de herramienta al **Nodo SDK Soberano** conectado por WebSocket.
6. **Respuesta Teleimétrica:** El Nodo SDK retorna los datos reales al Hub, el Hub a CrewAI/AutoGen, y la respuesta gráfica se proyecta en el portal A2UI.

---

## Estado y Madurez de los SDKs

| SDK / Cliente | Lenguaje | Estado de Madurez | Ámbito de Aplicación |
| :--- | :---: | :---: | :--- |
| **`python/rayrabbit_client/`** | Python 3.10+ | **Stable / Preview (v0.1.0)** | SDK Oficial de Python para crear `RayRabbitNode` con decoradores `@node.tool`, WebSockets `/ws`, y proxy MCP automático. |
| **`javascript/@rayrabbit-client/`** | TypeScript / Node | **Alpha (v0.1.0-alpha)** | SDK Oficial de JavaScript/Node.js para conectar agentes y herramientas JS a la red soberana por WebSocket. |
| **`javascript/@rayrabbit-a2ui/`** | React / TypeScript | **Alpha (v0.1.0-alpha)** | Librería cliente del protocolo visual A2UI v0.9.1 (SDUI) para aplicaciones Web y Dashboards. |
| **`antigravity/`** | Plugin / MCP | **Stable (v0.1.0)** | Plugin oficial y servidor MCP para integración bidireccional con Google Antigravity. |

</details>
