# RayRabbit Python Client SDK

The official Python client SDK for [RayRabbit](https://rayrabbit-ai.github.io), the Next-Generation Interoperability Infrastructure for AI.

## Installation

```bash
# Option A: Local editable install from source (Developer Preview)
pip install -e clients/python/rayrabbit_client

# Option B: PyPI package (Upcoming v0.1.0 release)
pip install rayrabbit-client
```

## Quickstart: Creating a Sovereign SDK Node

```python
from rayrabbit_client import RayRabbitNode

# Connect to the Hub WebSocket Ingress
node = RayRabbitNode(
    agent_id="my_logistics_node",
    hub_url="ws://127.0.0.1:8005/ws"
)

# Register an atomic domain tool with zero HTTP boilerplate
@node.mcp_tool(category="logistics")
def calculate_freight(weight_kg: float, distance_km: float) -> dict:
    cost = weight_kg * 0.45 + distance_km * 0.12
    return {"cost_usd": round(cost, 2), "currency": "USD"}

# Start node and expose tools dynamically to all federated agents
node.start()
```

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# SDK Cliente de Python de RayRabbit

SDK oficial de Python para [RayRabbit](https://rayrabbit-ai.github.io), la Infraestructura de Interoperabilidad de Próxima Generación para IA.

## Instalación

```bash
# Opción A: Instalación editable local desde el código fuente (Developer Preview)
pip install -e clients/python/rayrabbit_client

# Opción B: Paquete oficial de PyPI (Próximamente versión v0.1.0)
pip install rayrabbit-client
```

## Inicio Rápido: Creando un Nodo SDK Soberano

```python
from rayrabbit_client import RayRabbitNode

# Conectar al WebSocket Ingress del Hub
node = RayRabbitNode(
    agent_id="mi_nodo_logistico",
    hub_url="ws://127.0.0.1:8005/ws"
)

# Registrar una herramienta atómica de dominio sin servidores HTTP manuales
@node.mcp_tool(category="logistica")
def calcular_flete(peso_kg: float, distancia_km: float) -> dict:
    costo = peso_kg * 0.45 + distancia_km * 0.12
    return {"costo_usd": round(costo, 2), "moneda": "USD"}

# Arrancar nodo y exponer herramientas dinámicamente a todos los agentes federados
node.start()
```

</details>
