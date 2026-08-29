---
name: rayrabbit-grid
description: Guías operativas y runbooks para interactuar con la malla soberana de RayRabbit, monitorear telemetría y enviar mensajes inter-sesión.
version: 0.1.0
author: RayRabbit Labs, Inc.
---

# Runbook Operativo de la Malla RayRabbit

## Visión General
Esta habilidad proporciona flujos de trabajo operativos para que los Asistentes de Código IA interactúen con la **Malla Soberana RayRabbit (L3)** usando herramientas MCP nativas.

## Operaciones Principales

### 1. Descubrimiento de Nodos y Salud del Clúster
Consulta los agentes activos conectados a la malla:
```python
# Invocar la herramienta MCP rayrabbit_list_agents()
agents = await mcp.call_tool("rayrabbit_list_agents", {})
```

### 2. Mensajería Inter-Agente e Inter-Sesión
Envía mensajes criptográficos A2A entre espacios de trabajo o máquinas remotas:
```python
# Invocar la herramienta MCP rayrabbit_send_message()
await mcp.call_tool("rayrabbit_send_message", {
    "recipient_id": "antigravity_devops",
    "content": {"proposal": "Actualizar manifiestos de despliegue a v0.2.0"}
})
```

### 3. Lectura de Bandeja de Entrada
Consulta las notificaciones y tareas pendientes en el buzón:
```python
inbox = await mcp.call_tool("rayrabbit_read_inbox", {})
```

### 4. Persistencia en Memoria Soberana L3
Publica hechos compartidos de forma inmutable:
```python
await mcp.call_tool("rayrabbit_publish_fact", {
    "key": "cluster_status",
    "value": "READY_FOR_DEPLOYMENT"
})
```
