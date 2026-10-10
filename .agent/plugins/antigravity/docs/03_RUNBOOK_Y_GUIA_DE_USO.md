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

### Escenario 1: Sesión en la misma máquina donde corre el clúster (`NAREDIGITAL-MAN`)
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
        "RAYRABBIT_HUB_URL": "http://192.168.0.44:8005",
        "RAYRABBIT_AGENT_ID": "antigravity_devops",
        "RAYRABBIT_AGENT_NAME": "Antigravity DevOps Agent"
      }
    }
  }
}
```

### Escenario 3: Sesión conectada por Cable Directo Gigabit (IP Estática)
* PC Hub (`NAREDIGITAL-MAN`): Ethernet `192.168.2.1` / Máscara `255.255.255.0`
* PC Cliente (`NAREDIGITAL-CRY`): Ethernet `192.168.2.2` / Máscara `255.255.255.0`
* URL de conexión: `RAYRABBIT_HUB_URL = "http://192.168.2.1:8005"`

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
