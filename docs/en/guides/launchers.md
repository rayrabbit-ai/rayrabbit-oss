# CLI Commands & Sovereign Launchers

RayRabbit provides a unified command-line interface (`rayrabbit`) and automated bootstrap scripts to manage the microservice lifecycle, cryptographic keys, and interactive terminal clients.

---

## The `rayrabbit` CLI Reference

| Command | Operational Purpose |
| :--- | :--- |
| **`rayrabbit start`** | Launches the complete cluster in the background and opens the interactive terminal chatbot session immediately. |
| **`rayrabbit cluster`** | Boots the entire sovereign ecosystem (Hub :8005, MCP :8008, Services :8001–8003, A2UI Web Portal :8006). |
| **`rayrabbit chat`** | Opens an interactive terminal client to talk to federated agents and observe real-time reasoning. |
| **`rayrabbit install`** | Automatically provisions and configures isolated virtual environments (`venvs`) for local framework nodes. |

---

## Development Bootstrap Scripts (`setup_dev`)

To initialize the repository for the first time from source:

```bash
# On Windows:
setup_dev.bat

# On Linux / macOS:
chmod +x setup_dev.sh
./setup_dev.sh
```

The installer detects the Python runtime, creates virtual environments, compiles service dependencies, and links the global `rayrabbit` CLI.

---

## Sovereign Cluster Port Allocation

| Port | Service / Component | Protocol / Transport | Operational Purpose |
| :---: | :--- | :--- | :--- |
| **`8005`** | **FastAPI Core Hub** | HTTP REST & WebSocket (`/ws`) | MessageBus routing, A2ARouter, message ingress, and JWS validation. |
| **`8008`** | **Hub MCP Server** | WebSocket Native | Dynamic tool catalog (`tools/list`, `tools/call`) and TaskEngine MCPv2. |
| **`8006`** | **A2UI Web Portal Node** | HTTP & WebSocket (`/ws/a2ui`) | Declarative reactive telemetry and visual management console. |
| **`8001`** | **CrewAI Sovereign Node** | DeclarativeBridge / HTTP | Multi-agent collaborative squads (`execute_crew_task`). |
| **`8002`** | **LangChain Sovereign Node** | DeclarativeBridge / HTTP | LCEL data parsing and extraction chains (`run_lcel_chain`). |
| **`8003`** | **AutoGen Sovereign Node** | DeclarativeBridge / HTTP | Multi-agent dialogue and consensus chats (`start_autogen_chat`). |

---

## Distributed Cluster Launcher

For multi-host or hybrid multicloud environments where services are federated over public networks:

```bash
python run_distributed_rayrabbit_cluster.py
```

### Key Distributed Capabilities:
1. **Strict RSA-4096 JWS Enforcement**: Rejects incoming packets lacking compact non-repudiation headers.
2. **mTLS / HTTPS Gateway**: Encapsulates and encrypts outbound payloads routed across public internet perimeters.
3. **Disconnection Tolerance (OfflineToleranceService)**: Persists and replays queued messages with exponential backoff during temporary network partitions.
