# Logistics Use Case — RayRabbit (Dual-Mode: Sovereign A2A/MCP & OpenAPI Declarative Bridge)

## Purpose and Vision

This enterprise reference use case demonstrates **real, decentralized, and framework-agnostic interoperability** with RayRabbit mediating between heterogeneous cognitive agents (**LangChain**, **CrewAI**, **AutoGen**).

The infrastructure natively and interchangeably supports **two operation modes**:

1. **Sovereign Native Mode (`communication_mode: 'p2p'`)**: Based purely on open standards (**Google A2A JSON-RPC 2.0**, **Anthropic MCP v2**), cryptographic perimeter security (**MAESTRO Framework with Mutual PoP RSA-4096**), and reactive UI streaming (**A2UI Standard v0.9.1**).
2. **Declarative Bridge Mode (`communication_mode: 'bridge'`)**: Based on Zero-Code OpenAPI contracts (`/openapi.json` and `/invoke`) and a dynamic listener network over the MessageBus.

---

## 1. Native P2P Interoperability Architecture (A2A + MCP)

In this mode, each microservice operates as a sovereign node (*Shared Nothing*), dynamically resolving tools via MCP and orchestrating tasks via JSON-RPC 2.0:

```mermaid
sequenceDiagram
    autonumber
    participant Browser as Web Browser (WebSocket)
    participant Hub as RayRabbit Hub (8005)
    participant UIM as logistics_ui_manager (8006)
    participant LC as LangChain Service (8002)
    participant CR as CrewAI Service (8001)
    participant AG as AutoGen Service (8003)

    Note over Browser,AG: 1. Infrastructure Startup & Connection
    Browser->>Hub: WebSocket Connection (/ws/a2ui/logistics_dashboard)
    activate Hub
    Hub-->>Browser: [HANDSHAKE OK] Telemetry channel connected
    deactivate Hub

    UIM->>Hub: Dynamic Handshake (Sovereign P2P JWS Identity)
    activate Hub
    Hub->>Hub: Verifies RSA Signature and registers dynamic endpoint in A2ARouter
    Hub-->>UIM: [SUCCESS] Identity bound to Business Bus
    deactivate Hub

    Note over Browser,AG: 2. Request & Multi-Agent Orchestration (A2A / MCP)
    Browser->>Hub: Send User Action ("Track order ORD-2025-001")
    activate Hub
    Hub->>UIM: Direct A2A routing via HTTP POST (/a2ui)
    deactivate Hub
    activate UIM
    
    Note over UIM: AI Inference (z-ai/glm-4.5-air)<br/>Determines MCP tools to execute in parallel
    
    par [MCP Tool Call] -> Get structured tracking
        UIM->>LC: POST /mcp/call (tool: get_order_tracking) [Signed JWS]
        activate LC
        LC->>LC: Queries Local SAP TM DB (SQLite)
        LC-->>UIM: Returns standard JSON-RPC
        deactivate LC
    and [MCP Tool Call] -> Get optimal routing plan
        UIM->>CR: POST /mcp/call (tool: get_routing_plan) [Signed JWS]
        activate CR
        CR->>CR: Runs CrewAI squad (route optimization)
        CR-->>UIM: Returns standard JSON-RPC
        deactivate CR
    end

    UIM->>UIM: Synthesizes logistics report & generates A2UI declarative surface
    UIM->>Hub: Emits A2UI event (surfaceUpdate + components)
    activate Hub
    Hub->>Browser: Streams visual widgets live via WebSocket
    deactivate Hub
    deactivate UIM
```

---

## 2. Quick Execution Guide

### Prerequisites
* 4 open terminal windows (or run `python run_local_rayrabbit_cluster.py` to launch all automatically).
* Hub running on Port 8005.

### Step 1: Start Hub Core
```bash
python -m uvicorn api.server:app --host 127.0.0.1 --port 8005
```

### Step 2: Start Cognitive Framework Services
```bash
# Terminal 2: CrewAI Service (Port 8001)
python -m examples.services.crewai.crewai_service

# Terminal 3: LangChain Service (Port 8002)
python -m examples.services.langchain.langchain_service

# Terminal 4: AutoGen Service (Port 8003)
python -m examples.services.autogen.autogen_service
```

### Step 3: Start Sovereign A2UI Portal (Port 8006)
```bash
python rayrabbit/examples/logistics_use_case/run_logistics_agent.py
```

Open `http://localhost:8005/dashboard` in your web browser to observe real-time inter-agent communication, telemetry, and live interactive UI surfaces!

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# Caso de Uso de Logística — RayRabbit (Dual-Mode: A2A/MCP Soberano & OpenAPI Declarative Bridge)

## Propósito y Visión

Este caso de uso demuestra la **interoperabilidad real**, agnóstica y descentralizada de RayRabbit mediando entre agentes y servicios de frameworks cognitivos heterogéneos (**LangChain**, **CrewAI**, **AutoGen**). 

La infraestructura soporta de forma nativa e intercambiable **los dos modos de operación**:

1. **Modo Soberano Nativo (`communication_mode: 'p2p'`)**: Basado exclusivamente en estándares abiertos (**Google A2A JSON-RPC 2.0**, **Anthropic MCP v2**), seguridad perimetral de firmas (**Marco MAESTRO con Mutual PoP RSA-4096**) y visualización reactiva (**Estándar A2UI v0.9.1**).
2. **Modo Declarativo Bridge (`communication_mode: 'bridge'`)**: Basado en integración Zero-Code mediante contratos **OpenAPI 3.0/3.1** (`/openapi.json` e `/invoke`) y un sistema nervioso de agentes listeners sobre el MessageBus.

---

## 1. Arquitectura de Interoperabilidad Nativa P2P (A2A + MCP)

En este modo, cada microservicio opera como un nodo soberano (*Shared Nothing*), resolviendo herramientas dinámicamente vía MCP y orquestando tareas mediante JSON-RPC 2.0:

```mermaid
sequenceDiagram
    autonumber
    participant Browser as Navegador (WebSocket)
    participant Hub as Hub RayRabbit (8005)
    participant UIM as logistics_ui_manager (8006)
    participant LC as LangChain Service (8002)
    participant CR as CrewAI Service (8001)
    participant AG as AutoGen Service (8003)

    Note over Browser,AG: 1. Arranque de Infraestructura y Conexión
    Browser->>Hub: Conexión WebSocket (/ws/a2ui/logistics_dashboard)
    activate Hub
    Hub-->>Browser: [HANDSHAKE OK] Canal de visualización conectado
    deactivate Hub

    UIM->>Hub: Handshake dinámico (Identidad Soberana P2P JWS)
    activate Hub
    Hub->>Hub: Verifica Firma RSA y añade endpoint dynamic a A2ARouter
    Hub-->>UIM: [SUCCESS] Identidad vinculada en el Business Bus
    deactivate Hub

    Note over Browser,AG: 2. Petición y Orquestación Inteligente (A2A / MCP)
    Browser->>Hub: Enviar Acción ("Rastrear pedido ORD-2025-001")
    activate Hub
    Hub->>UIM: Ruteo A2A directo vía HTTP POST (/a2ui)
    deactivate Hub
    activate UIM
    
    Note over UIM: Inferencia de IA (z-ai/glm-4.5-air)<br/>Determina ejecutar herramientas MCP en paralelo
    
    par [MCP Tool Call] -> Obtener tracking estructurado
        UIM->>LC: POST /mcp/call (tool: get_order_tracking) [Firmado JWS]
        activate LC
        LC->>LC: Busca en SAP TM Local DB (SQLite)
        LC-->>UIM: Retorna JSON-RPC estándar
        deactivate LC
    and [MCP Tool Call] -> Obtener plan de ruteo
        UIM->>CR: POST /mcp/call (tool: get_routing_plan) [Firmado JWS]
        activate CR
        CR->>CR: Ejecuta Crew (Planificación de rutas)
        CR-->>UIM: Retorna JSON-RPC estándar
        deactivate CR
    and [MCP Tool Call] -> Obtener asignación de flota
        UIM->>AG: POST /mcp/call (tool: get_fleet_assignments) [Firmado JWS]
        activate AG
        AG->>AG: Ejecuta Multi-Agent Chat en AutoGen
        AG-->>UIM: Retorna JSON-RPC estándar
        deactivate AG
    end

    Note over UIM: Consolidación de datos de los 3 nodos<br/>Construcción del modelo A2UI v0.9.1
    
    UIM->>Hub: Publicar Actualización (MessageType.EVENT / A2UI v0.9.1)
    activate Hub
    Hub->>Hub: Aplica Política de Confianza Local (LTP)
    Hub->>Browser: Transmite JSON A2UI a través del canal de visualización
    deactivate Hub

    Note over Browser: Renderizado dinámico interactivo en la pantalla
    deactivate UIM
```

---

## 2. Arquitectura Declarativa Bridge (OpenAPI + Listeners)

En este modo (`communication_mode: 'bridge'`), el Hub auto-descubre los contratos OpenAPI (`/openapi.json`) de los servicios externos y los expone al MessageBus mediante `DeclarativeBridge`. Los agentes listeners coordinan la cascada reactiva:

```mermaid
graph TD
    subgraph NervousSystem ["Sistema Nervioso (listener_agents.py)"]
        LCR["LangChainResponseListener"]
        CWF["CrewAIWorkflowListener"]
        AGU["AutoGenUpdateListener"]
        CFD["CrewAIFinalDecisionListener"]
        FCR["FinalCustomerResponseListener"]
    end

    subgraph Bridges ["Declarative Bridges"]
        LCB["langchain_service_bridge"]
        CRB["crewai_service_bridge"]
        AGB["autogen_service_bridge"]
    end

    subgraph Endpoints ["OpenAPI REST Endpoints"]
        LCE["POST /invoke (invoke_chain) :8002"]
        CRE["POST /invoke (run_crew) :8001"]
        AGE["POST /invoke (run_autogen_chat) :8003"]
    end

    LCB -->|HTTP JWS| LCE
    CRB -->|HTTP JWS| CRE
    AGB -->|HTTP JWS| AGE

    LCE -->|Publish Event| LCR
    LCR -->|Message| CRB
    CRE -->|Publish Event| CWF
    CWF -->|Message| AGB
    AGE -->|Publish Event| AGU
    AGU -->|Message| CFD
    CFD -->|Message| LCB
    LCE -->|Final Event| FCR
```

---

## Guía de Lanzamiento y Ejecución

La suite logística soberana se administra y ejecuta de forma unificada utilizando el lanzador dinámico y cross-platform del clúster.

### Modo 1: Ejecución en Clúster Unificado P2P (Recomendado)

#### Paso 1: Iniciar el Clúster Soberano (1 sola ventana)
Abre tu consola en la raíz del repositorio y ejecuta:
```bash
python run_local_rayrabbit_cluster.py
```
*Este comando se encarga de forma automática de:*
1. Limpiar sockets y puertos huérfanos del clúster anterior (evitando errores `10048` de bindeo).
2. Levantar secuencialmente el Hub Core en el puerto `8005`.
3. Detectar dinámicamente y arrancar los servicios soberanos externos (`crewai_service` en `8001`, `langchain_service` en `8002`, `autogen_service` en `8003`) en sus respectivos entornos virtuales (`venv`).
4. Levantar la capa de visualización e interacción: `A2UI` (puerto `8006`), nodos de dominio y consola limpia.

#### Paso 2: Abrir el Dashboard de Visualización
Navega en tu navegador a la URL nativa servida por el Hub:
```
http://127.0.0.1:8005/dashboard/index.html
```

#### Paso 3: Validación E2E Automatizada (AAIF)
Para ejecutar la suite completa de pruebas de interoperabilidad de extremo a extremo en modo P2P:
```bash
python rayrabbit/examples/logistics_use_case/run_logistics_aaif.py "Rastrear pedido ORD-2025-001"
```

---

### Modo 2: Ejecución en Modo Declarativo Bridge (OpenAPI)

Para operar en la Vía A (Zero-Code OpenAPI):
1. Configura en `config.yaml`:
   ```yaml
   custom:
     discovery:
       communication_mode: 'bridge'
   ```
2. Inicia los listeners del sistema nervioso:
   ```bash
   python rayrabbit/examples/logistics_use_case/run_listeners.py
   ```
3. Ejecuta el proyecto logístico clásico:
   ```bash
   python -c "import asyncio; from rayrabbit.examples.logistics_use_case.project import LogisticsClassicProject; asyncio.run(LogisticsClassicProject('logistics').execute({'order_info': 'Mi paquete #A123 no llegó'}))"
   ```

---

## Auditoría Criptográfica y Trazabilidad perimetral

RayRabbit implementa el marco **MAESTRO** perimetral para asegurar cada interacción en el bus:
- Cada mensaje que viaja entre los agentes soberanos requiere autenticación criptográfica robusta vía **JWS (JSON Web Signature)** compacta (RFC 7515).
- Las claves públicas se intercambian dinámicamente en el arranque mediante el handshake de firma RSA en el endpoint `/api/security/register`.
- Cada llamada es inmutablemente registrada en la base de datos cifrada SQLite correspondiente (`audit_logs/agent_{agent_id}_audit.db`).

Para consultar el estado de auditoría del clúster y el contenido de transacciones perimetrales, ejecuta:
```bash
python query_audit.py --limit 20
```

---

## Principios Arquitectónicos Demostrados

1. **Desacoplamiento Absoluto (Shared-Nothing)**: El core de RayRabbit no importa librerías nativas de terceros. Los agentes externos mantienen 100% de soberanía sobre su pila tecnológica y almacenamiento SQLite local.
2. **Paridad Dual Transparente**: Soporte simétrico para servicios OpenAPI REST (Vía A) y Nodos Nativos A2A/MCP (Vía C) sin fricción de código.
3. **Resiliencia con Offline Tolerance**: Si un servicio de red está temporalmente ocupado o reiniciándose, el Hub retiene las transacciones en la outbox de SQLite de forma segura, previniendo pérdidas de paquetes.

</details>
