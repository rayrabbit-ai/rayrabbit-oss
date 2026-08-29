# RayRabbit Plugin for Anthropic Claude Code & Claude Desktop

Official plugin connecting Claude Code to the **RayRabbit Sovereign Mesh L3 (AI TCP/IP + TLS + HTTP)** via **Realtime MCP Server-Sent Events (SSE)**.

## Features
* **Zero Config Setup**: Seamlessly register with `claude mcp add`.
* **Full Mesh Access**: Discover and execute distributed tools, stream telemetry to A2UI, and exchange A2A messages.
* **MAESTRO Zero-Trust**: Automatic cryptographic verification on all inter-agent communications.

## Quickstart

```bash
# 1. Install plugin globally
python scripts/install_plugins.py --plugin claude-code

# 2. Add to Claude Code CLI
claude mcp add rayrabbit -- http://127.0.0.1:8005/api/mcp/sse
```

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# Plugin de RayRabbit para Anthropic Claude Code y Claude Desktop

Plugin oficial para conectar Claude Code a la **Malla Soberana RayRabbit L3 (AI TCP/IP + TLS + HTTP)** mediante **Server-Sent Events (SSE) en tiempo real**.

## Características
* **Configuración Sin Fricción**: Registro inmediato con `claude mcp add`.
* **Acceso Total a la Malla**: Descubre y ejecuta herramientas distribuidas, emite telemetría a A2UI e intercambia mensajes A2A.
* **Seguridad MAESTRO Zero-Trust**: Verificación criptográfica automática en todas las comunicaciones inter-agente.

## Inicio Rápido

```bash
# 1. Instalar plugin globalmente
python scripts/install_plugins.py --plugin claude-code

# 2. Registrar en Claude Code CLI
claude mcp add rayrabbit -- http://127.0.0.1:8005/api/mcp/sse
```

</details>
