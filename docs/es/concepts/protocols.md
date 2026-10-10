# Suite de Protocolos: A2A, MCPv2 y A2UI

RayRabbit unifica los ecosistemas agénticos mediante tres especificaciones de protocolo abiertas y nativas que cubren transporte de mensajes, compartición de contexto/herramientas y telemetría visual reactiva.

---

## 1. Google A2A (Agent-to-Agent v1.0)

El protocolo **A2A** estandariza el intercambio de instrucciones, tareas y resultados entre nodos de IA. RayRabbit lo implementa sobre HTTP y WebSockets utilizando sobres con formato **JSON-RPC 2.0** y tarjetas de identidad criptográficas **AgentCard**.

### Ejemplo de Petición A2A
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/create",
  "params": {
    "prompt": "Optimizar envío de 50 lotes logísticos a Berlín",
    "package_id": "PKG-2026-A9",
    "priority": "high"
  },
  "id": "req-9b8c7d"
}
```

### Ejemplo de Respuesta A2A
```json
{
  "jsonrpc": "2.0",
  "result": {
    "output": "Ruta calculada con éxito: Operador DHL Express, ETA 14:00 CET.",
    "status": "completed"
  },
  "id": "req-9b8c7d"
}
```

---

## 2. Anthropic MCP / MCPv2 (Model Context Protocol)

Mientras A2A gestiona la *mensajería*, **MCP / MCPv2** estandariza las *capacidades* (herramientas dinámicas). RayRabbit opera un servidor MCP nativo sobre WebSocket en el puerto **`:8008`**, manteniendo un catálogo unificado en memoria (`tools/list`, `tools/call`).

### Desambiguación y Clasificación Dinámica (JSON Schema 2020-12)
Para permitir que cualquier LLM infiera y utilice herramientas sin acoplamiento estático, toda herramienta en RayRabbit **DEBE** incluir el metadato dinámico `category` o `namespace`:

```json
{
  "name": "get_shipment_status",
  "description": "Consulta el estado y ETA de un envío en el sistema ERP.",
  "category": "logistics",
  "inputSchema": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "Identificador único de la orden (ej. ORD-9812)"
      }
    },
    "required": ["order_id"]
  }
}
```

### Motor de Tareas Asíncronas (TaskEngine MCPv2)
Para operaciones de larga duración, RayRabbit incorpora el `TaskEngine` (`rayrabbit/core/task_engine/`):
- **Ciclo de Vida Transaccional**: Estados gestionados en SQLite (`pending` $\rightarrow$ `running` $\rightarrow$ `completed` | `failed` | `paused`).
- **Elicitación Dinámica (`elicitation/create`)**: Solicitud de confirmación humana o datos adicionales a mitad de ejecución sin bloquear el hilo del LLM.

---

## 3. Protocolo A2UI (v0.9.1) & Sovereign A2UI Agent

El protocolo **A2UI v0.9.1** es la especificación abierta para streaming de interfaces declarativas reactivas en el puerto **`:8006`**.

### Agente Soberano A2UI (`SovereignA2UIAgent`)
RayRabbit incluye un agente de telemetría visual plug-and-play adaptable a cualquier patrón cognitivo:
- **Cadenas Secuenciales (LCEL)**
- **Cuadrillas Jerárquicas (CrewAI)**
- **Aprobaciones Human-in-the-Loop (HITL)**
- **Ciclos Evaluador-Optimizador**
- **Debates y Chats Grupales (AutoGen)**

Los agentes transforman su razonamiento en bloques declarativos JSON (`---a2ui_JSON---`) que son procesados mediante primitivas de ciclo visual:
* `beginRendering`: Inicializa la superficie visual en el cliente web.
* `surfaceUpdate`: Transmite actualizaciones reactivas de componentes en tiempo real.
* `updateDataModel`: Sincroniza el estado del modelo de datos sin re-renderizar la interfaz.

---

!!! enterprise "Aceleración de Rendimiento y Runtimes Seguros"
    Para entornos de producción masiva con más de 1,000 nodos, RayRabbit Enterprise incorpora el motor **Robyn (Rust)** con latencias menores a 5 ms y ejecución de herramientas en cajas de arena aisladas **Wasmtime (WebAssembly)**.
    
    La suite **RayRabbit Enterprise ARK** lo resuelve de forma totalmente automatizada. Inyecta el ruteo de A2A, MCP, A2AUI, los filtros de seguridad MAESTRO y la rotación automática de claves criptográficas, blindando el perímetro del micro-servicio bajo un modelo Zero-Trust transparente.
