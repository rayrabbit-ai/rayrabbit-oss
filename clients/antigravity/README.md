# RayRabbit Plugin & MCP Server for Google Antigravity

The official **RayRabbit** plugin connects Google Antigravity (IDE & CLI) sessions to the **RayRabbit Universal Interoperability Infrastructure L3 (AI TCP/IP + TLS + HTTP)**, unlocking bidirectional inter-agent messaging, distributed tool execution, sovereign memory persistence, and **MAESTRO Zero-Trust** cryptographic security (JWS RSA-2048/4096 signatures).

---

## ⚡ Quickstart Installation (Single Command)

From the repository root, execute the official installer script:

```bash
python scripts/install_plugins.py --plugin antigravity
```

The script automatically configures:
1. The plugin in `.agent/plugins/antigravity/`.
2. Global registry in `~/.gemini/config/mcp_config.json`.
3. Cached schemas in `~/.gemini/antigravity/mcp/rayrabbit_mesh/`.

---

## Network Configuration: Local vs Remote

Antigravity registers MCP servers from **`mcp_config.json`** in two locations:
* **Global (Recommended):** `~/.gemini/config/mcp_config.json` (applies to all workspaces).
* **Per Project:** `.agent/plugins/antigravity/mcp_config.json` (applies to current project).

### 1. Scenario A: Local Node (Same Host as RayRabbit Hub)
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": [
        "/path/to/rayrabbit-oss/.agent/plugins/antigravity/server/mcp_server.py"
      ],
      "env": {
        "RAYRABBIT_HUB_URL": "http://127.0.0.1:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_core",
        "RAYRABBIT_AGENT_NAME": "Antigravity Core Agent",
        "RAYRABBIT_TIMEOUT": "10.0"
      }
    }
  }
}
```

### 2. Scenario B: Remote Node (Secondary Host / LAN / Cloud)
If Antigravity runs on a secondary machine (e.g. `192.168.1.X`), point `RAYRABBIT_HUB_URL` to the Hub's network IP:
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": [
        "/path/to/rayrabbit-oss/.agent/plugins/antigravity/server/mcp_server.py"
      ],
      "env": {
        "RAYRABBIT_HUB_URL": "http://192.168.1.100:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_devops",
        "RAYRABBIT_AGENT_NAME": "Antigravity DevOps Agent",
        "RAYRABBIT_TIMEOUT": "10.0"
      }
    },
    "rayrabbit_hub_sse": {
      "serverUrl": "http://192.168.1.100:8005/api/mcp/sse"
    }
  }
}
```

---

## Available MCP Tools

Once the plugin is loaded, the coding assistant has instant access to 6 sovereign mesh tools:

| Tool Name | Description |
| :--- | :--- |
| **`rayrabbit_send_message`** | Sends real-time A2A messages with MAESTRO JWS cryptographic signatures to other agents or remote Antigravity sessions. |
| **`rayrabbit_read_inbox`** | Inspects private inbox for incoming task assignments, replies, and telemetry events. |
| **`rayrabbit_list_agents`** | Discovers active sovereign nodes and federated agents across the mesh (local & remote). |
| **`rayrabbit_call_tool`** | Invokes atomic domain tools on federated nodes (`crewai_service`, `autogen_service`, `langchain_service`, SAP TM, Crypto). |
| **`rayrabbit_publish_fact`** | Immutably persists facts into shared L3 Sovereign Memory. |
| **`rayrabbit_get_telemetry`** | Queries cluster health, latency metrics, and A2UI visual telemetry. |

---

## Verification in Antigravity IDE

1. Open Antigravity and navigate to:
   **Settings $
ightarrow$ Customizations $
ightarrow$ Projects $
ightarrow$ `your-project`**.
2. Look for the yellow category **Mcp Tools (48 tokens)** with the **`rayrabbit_mesh`** server and its 6 registered tools.
3. If not visible immediately:
   * Press `Ctrl + R` to reload the IDE window.
   * Verify that `~/.gemini/config/mcp_config.json` points to the correct `python` path and `server/mcp_server.py`.

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# RayRabbit Plugin & MCP Server para Google Antigravity

El plugin oficial de **RayRabbit** conecta sesiones de Google Antigravity (IDE y CLI) a la **Infraestructura de Interoperabilidad L3 (AI TCP/IP + TLS + HTTP)**, habilitando comunicación inter-agente bidireccional, ejecución de herramientas distribuidas, persistencia en memoria soberana y seguridad criptográfica **MAESTRO Zero-Trust** (firmas JWS RSA-2048).

---

## Instalación Rápida (1 Solo Comando)

En la raíz del repositorio, ejecuta el script instalador oficial:

```bash
python scripts/install_plugins.py --plugin antigravity
```

El script configurará automáticamente:
1. El plugin en `.agent/plugins/antigravity/`.
2. El registro global en `~/.gemini/config/mcp_config.json`.
3. El caché de esquemas en `~/.gemini/antigravity/mcp/rayrabbit_mesh/`.

---

## Configuración de Red: Local vs Remota

Antigravity registra los servidores MCP leyendo el archivo **`mcp_config.json`** en dos ubicaciones posibles:
* **Global (Recomendado):** `~/.gemini/config/mcp_config.json` (aplica a todos los proyectos).
* **Por Proyecto:** `.agent/plugins/antigravity/mcp_config.json` (aplica al workspace abierto).

### 1. Escenario A: Nodo Local (Misma Máquina donde corre el Hub)
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": [
        "/path/to/rayrabbit-oss/.agent/plugins/antigravity/server/mcp_server.py"
      ],
      "env": {
        "RAYRABBIT_HUB_URL": "http://127.0.0.1:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_core",
        "RAYRABBIT_AGENT_NAME": "Antigravity Core Agent",
        "RAYRABBIT_TIMEOUT": "10.0"
      }
    }
  }
}
```

### 2. Escenario B: Nodo Remoto (Segunda PC en Red Local o VPN)
Si Antigravity corre en una máquina secundaria (ej. `REMOTE-AGENT-HOST` o `192.168.1.X`), `RAYRABBIT_HUB_URL` debe apuntar a la IP de la máquina principal:
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": [
        "/path/to/rayrabbit-oss/.agent/plugins/antigravity/server/mcp_server.py"
      ],
      "env": {
        "RAYRABBIT_HUB_URL": "http://192.168.1.100:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_devops",
        "RAYRABBIT_AGENT_NAME": "Antigravity DevOps Agent",
        "RAYRABBIT_TIMEOUT": "10.0"
      }
    },
    "rayrabbit_hub_sse": {
      "serverUrl": "http://192.168.1.100:8005/api/mcp/sse"
    }
  }
}
```

---

## Herramientas MCP Disponibles

Una vez cargado el plugin, el asistente dispondrá automáticamente de las 6 herramientas nativas de la malla:

| Herramienta | Descripción |
| :--- | :--- |
| **`rayrabbit_send_message`** | Envía mensajes A2A en tiempo real con firma criptográfica MAESTRO JWS a otros agentes o sesiones de Antigravity. |
| **`rayrabbit_read_inbox`** | Consulta la bandeja de entrada privada para verificar respuestas, tareas o eventos recibidos. |
| **`rayrabbit_list_agents`** | Descubre nodos y agentes activos en la malla (locales y remotos). |
| **`rayrabbit_call_tool`** | Invoca herramientas de dominio en nodos federados (`crewai_service`, `autogen_service`, `langchain_service`, SAP TM, Crypto). |
| **`rayrabbit_publish_fact`** | Publica hechos de forma inmutable en la Memoria Soberana L3 compartida. |
| **`rayrabbit_get_telemetry`** | Consulta la salud del clúster, latencia y telemetría visual de A2UI. |

---

## Verificación en la Interfaz de Antigravity

1. Abre Antigravity y dirígete a:
   **Settings $\rightarrow$ Customizations $\rightarrow$ Projects $\rightarrow$ `tu-proyecto`**.
2. Deberás ver la categoría amarilla **Mcp Tools (48 tokens)** con el servidor **`rayrabbit_mesh`** y sus 6 herramientas listadas.
3. Si no aparece de inmediato:
   * Presiona `Ctrl + R` para recargar la ventana.
   * Verifica que `~/.gemini/config/mcp_config.json` tenga la ruta correcta a `python` y `server/mcp_server.py`.

---

## Estructura Interna del Plugin

```
.agent/plugins/antigravity/
├── plugin.json               # Manifiesto oficial del plugin
├── mcp_config.json           # Configuración del servidor MCP
├── rules/
│   └── AGENTS.md             # Directivas de comportamiento para el LLM
├── skills/
│   └── rayrabbit-grid/       # Runbooks operacionales inter-sesión
├── server/
│   └── mcp_server.py         # Sidecar criptográfico MAESTRO Zero-Trust
└── docs/                     # Guías de arquitectura y consensos
```

</details>
