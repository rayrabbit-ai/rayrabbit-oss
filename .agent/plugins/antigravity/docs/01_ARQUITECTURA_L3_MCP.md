# Arquitectura L3: Plugin & Servidor MCP de RayRabbit para Google Antigravity

**Proyecto:** RayRabbit — Infraestructura de Interoperabilidad y Agnóstica de Próxima Generación de IA (AI TCP/IP + TLS + HTTP).  
**Visión:** Estándar neutral de capa L3 para conectar agentes heterogéneos, SDKs soberanos (Python/JS), portales visuales A2UI y frameworks cognitivos (CrewAI, AutoGen, LangChain) mediante mediación horizontal sin coordinadores centrales ni estado global compartido (**Shared-Nothing Architecture**).

---

## 1. Topología de Red y Mediación Horizontal

El plugin de Antigravity conecta cualquier sesión (IDE o CLI) a la red soberana de RayRabbit sin invadir la lógica interna de los agentes:

```mermaid
graph TD
    subgraph Host_A ["Host A: Estación DevOps (\\NAREDIGITAL-CRY)"]
        Session_A["Antigravity DevOps Session<br/>(RAYRABBIT_AGENT_ID=antigravity_devops)"]
        MCP_A["Servidor MCP Puente (stdio / JSON-RPC 2.0)<br/>Keypair RSA-2048 Local"]
        Session_A <-->|stdio| MCP_A
    end

    subgraph Hub_Central ["Host B: Core Hub (\\NAREDIGITAL-MAN / :8005)"]
        HubCore["RayRabbit L3 Hub Core<br/>(MessageBus + MAESTRO Zero-Trust)"]
        AuditDB[("audit.db (SQLite)<br/>Canal de Auditoría Inmutable")]
        HubCore <--> AuditDB
    end

    subgraph Host_B ["Host B: Estación Core & Arquitectura L3"]
        Session_B["Antigravity Core Session<br/>(RAYRABBIT_AGENT_ID=antigravity_core)"]
        MCP_B["Servidor MCP Puente (stdio / JSON-RPC 2.0)<br/>Keypair RSA-2048 Local"]
        Session_B <-->|stdio| MCP_B
    end

    subgraph Federated_Services ["Servicios Federados Soberanos"]
        CrewAI["CrewAI Routing (:8001)"]
        LangChain["LangChain WMS (:8002)"]
        AutoGen["AutoGen Fleet (:8003)"]
        A2UI["A2UI Telemetry (:8006)"]
    end

    MCP_A <-->|HTTP POST /api/publish-message<br/>Firma JWS RSA-2048| HubCore
    MCP_B <-->|HTTP POST /api/publish-message<br/>Firma JWS RSA-2048| HubCore
    HubCore <--> Federated_Services
```

---

## 2. Principio Zero-Patch (Inmutabilidad del Core)

* **Cero Modificaciones en el Core:** El núcleo de RayRabbit (`rayrabbit/core/`, `rayrabbit/security/`, `api/server.py`) no requiere parches ni dependencias adicionales para dar soporte a Antigravity.
* **Cliente Autónomo:** Todo el código del plugin reside exclusivamente en `clients/antigravity/`, operando como un nodo soberano más conectado a través de los protocolos abiertos de RayRabbit.

---

## 3. Seguridad MAESTRO Zero-Trust (RFC 7515 JWS)

Cada sesión de Antigravity cuenta con una identidad criptográfica asimétrica autónoma:
1. **Generación Automática de Claves:** Al arrancar el servidor MCP, se genera un par de claves RSA-2048 en `./keystore_mcp/` si no existen previamente.
2. **Firma de Mensajes:** Cada payload enviado por `rayrabbit_send_message` se firma digitalmente según el estándar JWS Compact (algoritmo `RS256` con padding `PSS` y hash `SHA-256`).
3. **Validación en el Hub:** El Hub valida la firma contra la clave pública adjunta en la cabecera `X-RayRabbit-Bridge-Public-Key-PEM` o almacenada en el KeyStore, garantizando autenticidad y no repudio.

---

## 4. Catálogo de Herramientas MCP Expuestas

| Herramienta MCP | Descripción | Parámetros Clave |
| :--- | :--- | :--- |
| `rayrabbit_send_message` | Envía un mensaje A2A firmado a otro agente o sesión. | `recipient_id`, `content`, `message_type`, `correlation_id` |
| `rayrabbit_read_inbox` | Consulta el buzón de entrada y mensajes de consenso. | `correlation_id`, `limit` |
| `rayrabbit_list_agents` | Descubre nodos y agentes federados activos en la malla. | *(Sin parámetros)* |
| `rayrabbit_call_tool` | Invoca herramientas en nodos remotos (WMS, Routing, Flota). | `tool_name`, `arguments` |
| `rayrabbit_get_telemetry` | Obtiene métricas y telemetría en vivo del Dashboard A2UI. | `stream_id` |
| `rayrabbit_publish_fact` | Persiste hechos en la Memoria Soberana L3 compartida. | `fact_key`, `fact_value` |
