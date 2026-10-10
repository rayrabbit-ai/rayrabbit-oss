# Configuration & Environment Variables

RayRabbit is fully configurable via a static configuration file (`config.yaml`) and system environment variables. The platform utilizes **LiteLLM** for native multi-LLM inference support, ensuring that changing providers requires zero code changes.

---

## The config.yaml Schema

The `config.yaml` file resides in the root directory of your project. It governs parameters for the **MessageBus**, logging, SQLite auditing, MAESTRO security keys, and static service discovery.

Here is a typical production-ready layout:

```yaml
# Core MessageBus Configuration
message_bus:
  instance_id: "production_cluster_01"
  enable_persistence: true
  max_message_history: 1000

# Auditing Configuration (SQLite DB storage)
auditing:
  enable_audit: true
  storage_provider: "sqlite"
  sqlite_db_path: "audit_logs/audit.db"

# MAESTRO Security configuration
security:
  enable_auth: true
  encryption_enabled: true
  keystore_path: "keystore"
  master_secret: "b40ff79100d990716c3ea51c138fc48f4eed6a490fcba004a2fa067ff8aef440"
  salt: "1f07447a8c4cdae07da8f6c942ade4d7"

custom:
  mcp_server:
    host: "0.0.0.0"
    port: 8008

  discovery:
    strategy: "static"
    communication_mode: "p2p"  # "bridge" or "p2p" (Direct A2A handshake)
    p2p_timeout: 300           # Latency tolerance for slow CPU inference

  # Registry of heterogeneous services
  external_services:
    - name: "crewai_service"
      address: "http://127.0.0.1:8001"
      mode: "local"
      topics: ["crewai_service_bridge"]
      network:
        timeout_total: 90
        max_retries: 5
```

---

## Multi-LLM Environment Variables

Since RayRabbit acts as an infrastructure, it does not lock you into any single LLM provider. Its multi-LLM backend is powered by **LiteLLM**, allowing seamless transitions between cloud models (Gemini, OpenAI, Anthropic, Groq) and local open models (Ollama, vLLM).

Ensure you export the keys matching your configured providers in your shell:

```bash
# Google Gemini (Primary Recommended)
export GEMINI_API_KEY="AIzaSy..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Groq (Ultra-fast inference)
export GROQ_API_KEY="gsk_..."

# Ollama local endpoints (if configured in LiteLLM)
export OLLAMA_API_BASE="http://localhost:11434"
```

---

## RayRabbit Core System Variables

These parameters control the runtime paths and global network parameters of the core RayRabbit engine:

| Environment Variable | Purpose | Default Value |
|----------------------|---------|---------------|
| `RAYRABBIT_HOME` | Absolute path containing local databases, caches, and logs. | `~/.rayrabbit` |
| `RAYRABBIT_HUB_URL` | The endpoint address of the Core API Server. | `http://127.0.0.1:8005` |
| `RAYRABBIT_KEYSTORE` | Path to the local identity key store. | `./keystore` |
| `RAYRABBIT_CONFIG` | Absolute path to the custom `config.yaml` file. | `./config.yaml` |
| `RAYRABBIT_LOG_LEVEL` | Verbosity of stdout structured logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | `INFO` |

---

!!! enterprise "RayRabbit Enterprise: Sovereign Secret Management"
    Stashing critical master secrets, keys, or LLM tokens inside plain environment variables or static YAML files violates corporate **Zero-Trust** security parameters.
    
    The **RayRabbit ARK** disables environment-based variable resolution in production. Instead, it binds to secure cloud vaults (such as **HashiCorp Vault**, **AWS Secrets Manager**, or **Google Secret Manager**) natively.
    
    Upon bootstrapping, the enterprise shield uses dynamic client-side certificate rotation (mTLS) to fetch credentials on-the-fly, keeping them exclusively in volatile RAM and ensuring they are never written to physical disk.
