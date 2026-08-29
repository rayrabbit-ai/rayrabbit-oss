# Comandos de CLI y Lanzadores Soberanos

RayRabbit proporciona una interfaz de línea de comandos (CLI) unificada `rayrabbit` y scripts de inicialización automatizados para gestionar el ciclo de vida del clúster de microservicios, la seguridad criptográfica y los clientes de terminal.

---

## Referencia de Comandos CLI `rayrabbit`

| Comando | Descripción Operativa |
| :--- | :--- |
| **`rayrabbit start`** | Lanza el clúster completo en segundo plano e inicia de inmediato la sesión interactiva del chatbot en la terminal. |
| **`rayrabbit cluster`** | Inicia el ecosistema soberano completo (Hub :8005, MCP :8008, Servicios :8001–8003, Portal A2UI :8006). |
| **`rayrabbit chat`** | Abre el cliente interactivo de terminal para dialogar con los agentes federados y monitorear respuestas. |
| **`rayrabbit install`** | Aprovisiona y configura automáticamente los entornos virtuales (`venvs`) aislados de los frameworks locales. |

---

## Scripts de Bootstrap de Desarrollo (`setup_dev`)

Para inicializar el repositorio por primera vez desde el código fuente:

```bash
# En Windows:
setup_dev.bat

# En Linux / macOS:
chmod +x setup_dev.sh
./setup_dev.sh
```

El instalador detecta el runtime de Python, genera los entornos virtuales, compila las dependencias de los microservicios y enlaza los comandos de la CLI `rayrabbit`.

---

## Distribución de Puertos del Clúster Soberano

| Puerto Físico | Componente / Servicio | Protocolo / Transporte | Propósito Operativo |
| :---: | :--- | :--- | :--- |
| **`8005`** | **FastAPI Core Hub** | HTTP REST & WebSocket (`/ws`) | MessageBus asíncrono, A2ARouter, ingesta de mensajes y validación JWS. |
| **`8008`** | **Hub MCP Server** | WebSocket Nativo | Catálogo dinámico de herramientas (`tools/list`, `tools/call`) y TaskEngine MCPv2. |
| **`8006`** | **Portal Visual A2UI** | HTTP & WebSocket (`/ws/a2ui`) | Streaming reactivo telemático y dashboard de control. |
| **`8001`** | **CrewAI Sovereign Node** | DeclarativeBridge / HTTP | Gestión colaborativa de cuadrillas agénticas (`execute_crew_task`). |
| **`8002`** | **LangChain Sovereign Node** | DeclarativeBridge / HTTP | Cadenas LCEL de extracción y procesamiento de datos (`run_lcel_chain`). |
| **`8003`** | **AutoGen Sovereign Node** | DeclarativeBridge / HTTP | Conversaciones y debates multi-agente (`start_autogen_chat`). |

---

## Lanzador de Clústeres Distribuidos

Para entornos de producción y multicloud donde los microservicios están dispersos geográficamente:

```bash
python run_distributed_rayrabbit_cluster.py
```

### Capacidades del Modo Distribuido:
1. **Verificación JWS RSA-4096 Estricta**: Rechaza conexiones que carezcan de firma compacta válida en sus cabeceras.
2. **Gateway mTLS / HTTPS**: Encapsula y cifra paquetes salientes hacia la WAN pública.
3. **Tolerancia a Desconexión (OfflineToleranceService)**: Encola mensajes con reintentos exponenciales ante cortes intermitentes de red.
