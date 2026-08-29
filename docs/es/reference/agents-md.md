# Catálogo de Contratos AGENTS.md

RayRabbit se rige por un catálogo estático estructurado en el archivo **`AGENTS.md`** situado en la carpeta raíz del proyecto para realizar el descubrimiento estático de agentes e identidades criptográficas. Actúa como la libreta de direcciones del clúster agéntico descentralizado.

---

## Esquema Estructurado de AGENTS.md

El Servidor API Core interpreta `AGENTS.md` al inicializarse y expone sus rutas. Cada bloque debe seguir este formato exacto de markdown:

```markdown
## 1. Logistics Orchestrator (LangChain Agent)
- **ID**: `logistics_manager`
- **Name**: Global Logistics Manager
- **Protocols**: `["a2a", "mcp", "http"]`
- **Capabilities**: `["order_analysis", "inventory_dispatch", "conflict_resolution", "analyze_order", "track_package"]`
- **a2a**: `http://127.0.0.1:8002/a2a`
- **mcp**: `http://127.0.0.1:8002/mcp`
- **mcp_tools**: `http://127.0.0.1:8002/mcp/tools`
- **mcp_call**: `http://127.0.0.1:8002/mcp/call`
- **Description**: Analiza las peticiones de los clientes y coordina las herramientas para procesar órdenes.
```

---

## Referencia de Parámetros

* **ID**: El identificador único del agente en el sistema. Se asocia a las colas de ruteo del MessageBus y se emplea para verificar firmas criptográficas en el almacén de claves público.
* **Protocols**: Listado de protocolos de comunicación soportados por el adaptador del agente.
* **Capabilities**: Listado de métodos lógicos y herramientas MCP expuestas por el micro-servicio.
* **a2a / mcp endpoints**: Direcciones físicas locales de red que apuntan al puerto de escucha del agente.

---

!!! enterprise "Servicio de Directorio Criptográfico Dinámico"
    Para entornos dinámicos a gran escala con múltiples instancias de agentes efímeros, RayRabbit Enterprise proporciona un servicio de directorio dinámico firmado criptográficamente. Automatiza el registro de agentes, gestiona la resolución de rutas en caliente y administra la rotación segura de claves sin necesidad de actualizar archivos de configuración manuales.
