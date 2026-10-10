# Nodos SDK, Herramientas Atómicas de Dominio y Asistentes CLI

RayRabbit permite conectar aplicaciones agénticas personalizadas, herramientas atómicas de negocio y asistentes de codificación (Claude Code, OpenAI Codex, Google Antigravity, OpenHands, Hermes, OpenClaw, $N$-Agentes) a la red soberana mediante los **RayRabbit Client SDKs** (Python y JavaScript/TypeScript en `clients/`).

---

## Malla Soberana: ¿Cómo interactúan los Nodos SDK y los Servicios Framework?

En la arquitectura L3 de RayRabbit, existe una mediación horizontal con separación limpia de roles:

* **Servicios Cognitivos Framework (CrewAI, AutoGen, LangChain, MAF, LlamaIndex):** Ejecutan razonamiento complejo, orquestación de cuadrillas multi-agente y debates de consenso utilizando sus propios motores y LLMs.
* **Nodos SDK y Herramientas Atómicas de Dominio (Clientes `rayrabbit_client`):** Exponen herramientas de datos de negocio (SAP TM, Binance, APIs REST locales, conectores ERP) conectándose por **WebSocket persistente (`ws://127.0.0.1:8005/ws`)** directamente a la Pasarela Core L3.
* **Asistentes de Código y Agentes Autónomos:** Se conectan a la Pasarela Core vía WebSocket para consumir y ejecutar herramientas disponibles en la malla de forma descentralizada.

```
                               ┌──────────────────────────────────┐
                               │   Portal A2UI (Puerto 8006)      │
                               └────────────────┬─────────────────┘
                                                │ 1. Solicita tarea (A2A)
                                                ▼
┌───────────────────────────┐  2. Invocación A2A ┌──────────────────────────────────┐
│ Sovereign Framework Nodes │ ─────────────────► │ RayRabbit Core Gateway(Pto 8005) │
│ - CrewAI (8001)           │ ◄───────────────── │    MessageBus + MAESTRO + MCP    │
│ - AutoGen (8003)          │ 3. Consulta Tools  └────────────────┬─────────────────┘
│ - LangChain (8002)        │    vía Mesh MCP                     │ 4. Ruteo asíncrono
│ - MAF / LlamaIndex        │                                     │    vía WebSocket /ws
└───────────────────────────┘                                     ▼
                                                 ┌──────────────────────────────────┐
                                                 │ Sovereign SDK Nodes & CLI Agents │
                                                 │ - logistics_ui_manager (Python)  │
                                                 │ - crypto_trader_agent (Node.js)  │
                                                 │ - Claude Code / Antigravity CLI  │
                                                 └──────────────────────────────────┘
```

---

## Uso del SDK de Python (`rayrabbit_client`)

El SDK de Python permite convertir cualquier script, base de datos o función en un **Nodo Soberano RayRabbit** usando el decorador `@node.mcp_tool`:

```python
import asyncio
from rayrabbit_client import RayRabbitNode

# Inicializar el nodo soberano
node = RayRabbitNode(
    agent_id="my_business_agent",
    hub_url="ws://127.0.0.1:8005/ws"
)

@node.mcp_tool(category="inventory")
def check_inventory(product_id: str) -> dict:
    """Consulta el inventario en tiempo real del sistema ERP."""
    return {"product_id": product_id, "stock": 42, "status": "available"}

if __name__ == "__main__":
    node.start()
```

---

## Flujo de Seguridad y Registro MAESTRO

Al iniciar un `RayRabbitNode`:

1. **Conexión WebSocket:** Se conecta al endpoint `/ws` de la Pasarela Core.
2. **Generación de Identidad:** Crea un par de llaves RSA-2048/4096 soberanas.
3. **Handshake PoP (Proof of Possession):** Firma el desafío de registro con JWS (RFC 7515).
4. **Proxy Soberano (`SovereignWebSocketProxy`):** La Pasarela Core crea un proxy dinámico en memoria y registra las herramientas expuestas en el catálogo global de la **Pasarela MCP Mesh (`ws://127.0.0.1:8008`)**.

Cualquier servicio federado (CrewAI, AutoGen o LangChain) puede ahora descubrir y consumir tus herramientas de negocio a través de la infraestructura soberana de RayRabbit.
