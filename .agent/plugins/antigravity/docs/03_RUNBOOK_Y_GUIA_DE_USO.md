# Runbook & Operational Guide: RayRabbit MCP Plugin for Antigravity

This guide contains step-by-step procedures to install, configure, and operate cross-session communication in Google Antigravity using the official RayRabbit plugin.

---

## 1. Plugin Installation

### Option A: Workspace Installation (Recommended for Team Projects)
Copy the `clients/antigravity` folder into `.agent/plugins/rayrabbit`:

```powershell
# On Windows (PowerShell)
New-Item -ItemType Directory -Path .agent\plugins\rayrabbit -Force | Out-Null
Copy-Item -Path clients\antigravity\* -Destination .agent\plugins\rayrabbit\ -Recurse -Force
```

```bash
# On Linux / macOS
mkdir -p .agent/plugins/rayrabbit
cp -r clients/antigravity/* .agent/plugins/rayrabbit/
```

### Option B: Global Installation (Available to all Antigravity sessions)

```powershell
# On Windows
New-Item -ItemType Directory -Path "$env:USERPROFILE\.gemini\config\plugins\rayrabbit" -Force | Out-Null
Copy-Item -Path clients\antigravity\* -Destination "$env:USERPROFILE\.gemini\config\plugins\rayrabbit\" -Recurse -Force
```

```bash
# On Linux / macOS
mkdir -p ~/.gemini/config/plugins/rayrabbit
cp -r clients/antigravity/* ~/.gemini/config/plugins/rayrabbit/
```

---

## 2. Network Topology Configuration (Local vs Remote)

Edit `mcp_config.json` or configure session environment variables according to your network setup:

### Scenario 1: Session on Same Host as Hub Cluster (`PRIMARY-HUB-HOST`)
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": ["${pluginDir}/server/mcp_server.py"],
      "env": {
        "RAYRABBIT_HUB_URL": "http://127.0.0.1:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_core",
        "RAYRABBIT_AGENT_NAME": "Antigravity Core Architecture Agent"
      }
    }
  }
}
```

### Scenario 2: Session on Secondary Machine (Local Wi-Fi Network)
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": ["${pluginDir}/server/mcp_server.py"],
      "env": {
        "RAYRABBIT_HUB_URL": "http://192.168.1.100:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_devops",
        "RAYRABBIT_AGENT_NAME": "Antigravity DevOps Agent"
      }
    }
  }
}
```

### Scenario 3: Session Connected via Direct Gigabit Cable (Static IP)
* Hub Host (`PRIMARY-HUB-HOST`): Ethernet `192.168.10.1` / Netmask `255.255.255.0`
* Client Host (`REMOTE-AGENT-HOST`): Ethernet `192.168.10.2` / Netmask `255.255.255.0`
* Target URL: `RAYRABBIT_HUB_URL = "http://192.168.10.1:8005"`

---

## 3. Prompts & Workflows in Antigravity Chat

### To Send a Consensus Message / Proposal (Session A):
> *"Discover agents on the mesh and send the setup_dev.sh consensus proposal to antigravity_core with correlation_id consensus-setup-dev-001"*

### To Check Inbox & Reply (Session B):
> *"Check your RayRabbit inbox for messages with correlation_id consensus-setup-dev-001 and reply indicating whether you approve the technical proposal"*

### To Persist an Approved Fact into L3 Sovereign Memory:
> *"Publish the fact 'devops_consensus_approved' to L3 sovereign memory with the summary of ratified changes"*

---

## 4. Troubleshooting & Diagnostics

| Symptom | Probable Cause | Solution |
| :--- | :--- | :--- |
| MCP tool fails with `Connection refused` | Hub Core is not running on target port | Run `python -m uvicorn api.server:app --host 0.0.0.0 --port 8005`. |
| Handshake error `401 Unauthorized` | Invalid or mismatched `master_secret` | Verify `.env` secret matches Hub configuration. |
| Tool not visible in Antigravity | Plugin directory path missing | Reload IDE window (`Ctrl + R`) or re-run `python scripts/install_plugins.py`. |

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# Runbook y Guía Operativa: Plugin MCP de RayRabbit para Antigravity

Esta guía contiene los procedimientos paso a paso para instalar, configurar y operar la comunicación inter-sesión de Antigravity mediante el plugin oficial de RayRabbit.

---

## 1. Instalación del Plugin

### Opción A: Por Espacio de Trabajo (Recomendado para proyectos en equipo)
Copia la carpeta `clients/antigravity` dentro de `.agent/plugins/rayrabbit`:

```powershell
# En Windows (PowerShell)
New-Item -ItemType Directory -Path .agent\plugins\rayrabbit -Force | Out-Null
Copy-Item -Path clients\antigravity\* -Destination .agent\plugins\rayrabbit\ -Recurse -Force
```

```bash
# En Linux / macOS
mkdir -p .agent/plugins/rayrabbit
cp -r clients/antigravity/* .agent/plugins/rayrabbit/
```

### Opción B: Instalación Global (Disponible para todas las sesiones de Antigravity)

```powershell
# En Windows
New-Item -ItemType Directory -Path "$env:USERPROFILE\.gemini\config\plugins\rayrabbit" -Force | Out-Null
Copy-Item -Path clients\antigravity\* -Destination "$env:USERPROFILE\.gemini\config\plugins\rayrabbit\" -Recurse -Force
```

```bash
# En Linux / macOS
mkdir -p ~/.gemini/config/plugins/rayrabbit
cp -r clients/antigravity/* ~/.gemini/config/plugins/rayrabbit/
```

---

## 2. Configuración de Red (Local vs Remoto)

Edita el archivo `mcp_config.json` o define las variables de entorno de tu sesión según la topología:

### Escenario 1: Sesión en la misma máquina donde corre el clúster (`PRIMARY-HUB-HOST`)
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": ["${pluginDir}/server/mcp_server.py"],
      "env": {
        "RAYRABBIT_HUB_URL": "http://127.0.0.1:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_core",
        "RAYRABBIT_AGENT_NAME": "Antigravity Core Architecture Agent"
      }
    }
  }
}
```

### Escenario 2: Sesión en otra máquina de la red local (Wi-Fi)
```json
{
  "mcpServers": {
    "rayrabbit_mesh": {
      "command": "python",
      "args": ["${pluginDir}/server/mcp_server.py"],
      "env": {
        "RAYRABBIT_HUB_URL": "http://192.168.1.100:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_devops",
        "RAYRABBIT_AGENT_NAME": "Antigravity DevOps Agent"
      }
    }
  }
}
```

### Escenario 3: Sesión conectada por Cable Directo Gigabit (IP Estática)
* PC Hub (`PRIMARY-HUB-HOST`): Ethernet `192.168.10.1` / Máscara `255.255.255.0`
* PC Cliente (`REMOTE-AGENT-HOST`): Ethernet `192.168.10.2` / Máscara `255.255.255.0`
* URL de conexión: `RAYRABBIT_HUB_URL = "http://192.168.10.1:8005"`

---

## 3. Prompts y Flujos de Trabajo en Antigravity Chat

### Para Enviar un Mensaje / Propuesta de Consenso (Sesión A):
> *"Descubre los agentes en la red y envíale la propuesta de consenso de setup_dev.sh al agente antigravity_core con el correlation_id consenso-setup-dev-001"*

### Para Consultar el Buzón y Responder (Sesión B):
> *"Revisa tu buzón de RayRabbit buscando mensajes con correlation_id consenso-setup-dev-001 y responde si apruebas la propuesta técnica"*

### Para Persistir un Hecho Aprobado en la Memoria Soberana L3:
> *"Publica el hecho 'consenso_devops_aprobado' en la memoria soberana L3 con el resumen de los cambios ratificados"*

---

## 4. Diagnóstico y Solución de Problemas (Troubleshooting)

| Síntoma | Causa Probable | Solución |
| :--- | :--- | :--- |
| `HTTP Error 401: Unauthorized` | Mensaje remoto enviado sin firma criptográfica JWS. | El servidor `mcp_server.py` adjunta automáticamente las cabeceras `X-RayRabbit-JWS` y `X-RayRabbit-Bridge-Public-Key-PEM`. |
| `<urlopen error timed out>` | El Hub está escuchando únicamente en `127.0.0.1` en vez de `0.0.0.0`. | Verificar que en `run_local_rayrabbit_cluster.py` el Hub tenga `--host 0.0.0.0` y reiniciar el clúster con `rayrabbit cluster`. |
| `El agente escribe scripts de Python en lugar de usar la tool` | Antigravity no ha recargado la lista de herramientas del MCP. | Hacer clic en `Restart to Update` en la barra superior de Antigravity o reiniciar la sesión de chat. |

</details>
