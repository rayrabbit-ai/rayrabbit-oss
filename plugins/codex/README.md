# RayRabbit Plugin for OpenAI Codex, Cursor & OpenAI CLI

Official plugin connecting OpenAI Codex, Cursor IDE, and CLI agents to the **RayRabbit Sovereign Mesh L3 (AI TCP/IP + TLS + HTTP)** via **Realtime MCP Server-Sent Events (SSE)**.

## Features
* **IDE & CLI Integration**: Integrates directly with Cursor, Codex CLI, and VSCode MCP extensions.
* **Bidirectional Invocation**: Consume tools or expose local Python scripts as sovereign tools over WebSockets.
* **MAESTRO Zero-Trust**: RSA-4096 cryptographic signatures and AES-256-GCM encrypted keystore.

## Quickstart

```bash
# 1. Install plugin globally
python scripts/install_plugins.py --plugin codex

# 2. Add to Cursor or Codex MCP configuration:
# Server URL: http://127.0.0.1:8005/api/mcp/sse
```

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# Plugin de RayRabbit para OpenAI Codex, Cursor y CLI

Plugin oficial para conectar OpenAI Codex, el editor Cursor IDE y agentes CLI a la **Malla Soberana RayRabbit L3 (AI TCP/IP + TLS + HTTP)** mediante **Server-Sent Events (SSE) en tiempo real**.

## Características
* **Integración con IDE y CLI**: Compatible directamente con Cursor, Codex CLI y extensiones MCP de VSCode.
* **Invocación Bidireccional**: Consume herramientas o expone scripts locales de Python como herramientas soberanas por WebSockets.
* **Seguridad MAESTRO Zero-Trust**: Firmas criptográficas RSA-4096 y almacén de claves cifrado con AES-256-GCM.

## Inicio Rápido

```bash
# 1. Instalar plugin globalmente
python scripts/install_plugins.py --plugin codex

# 2. Añadir a la configuración MCP de Cursor o Codex:
# Server URL: http://127.0.0.1:8005/api/mcp/sse
```

</details>
