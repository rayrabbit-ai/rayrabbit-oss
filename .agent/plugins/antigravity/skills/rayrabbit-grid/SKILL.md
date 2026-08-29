---
name: rayrabbit-grid
description: Operational playbooks and guidelines for interacting with the RayRabbit Sovereign Mesh, monitoring telemetry, and exchanging inter-session messages.
version: 0.1.0
author: RayRabbit Labs, Inc.
---

# RayRabbit Grid Operational Playbook

## Overview
This skill provides operational workflows for AI Coding Assistants to interact with the **RayRabbit Sovereign Mesh (L3)** using native MCP tools.

## Core Operations

### 1. Peer Discovery & Node Health
Check active agents connected to the cluster:
```python
# Call rayrabbit_list_agents() MCP tool
agents = await mcp.call_tool("rayrabbit_list_agents", {})
```

### 2. Inter-Agent & Inter-Session Messaging
Send A2A cryptographic messages across workspaces or remote machines:
```python
# Call rayrabbit_send_message() MCP tool
await mcp.call_tool("rayrabbit_send_message", {
    "recipient_id": "antigravity_devops",
    "content": {"proposal": "Update deployment manifests to v0.2.0"}
})
```

### 3. Reading Inbox Messages
Fetch pending inbox notifications:
```python
inbox = await mcp.call_tool("rayrabbit_read_inbox", {})
```

### 4. L3 Sovereign Memory Persistence
Persist shared facts into L3 memory:
```python
await mcp.call_tool("rayrabbit_publish_fact", {
    "key": "cluster_status",
    "value": "READY_FOR_DEPLOYMENT"
})
```
