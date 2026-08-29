# config.yaml Reference

This reference documents the complete structure of the `config.yaml` file governing the core RayRabbit runtime parameters.

---

## Schema Structure

```yaml
# ====================================================================
# RayRabbit Core Configuration Schema
# ====================================================================

# Central Message Bus parameters
message_bus:
  instance_id: "default_instance" # Unique ID of this physical cluster
  enable_persistence: true        # Persist unconsumed queue items to disk
  max_message_history: 1000       # Keep last 1000 messages in memory cache

# Structured Logging parameters
logging:
  level: "INFO"                   # DEBUG, INFO, WARNING, ERROR
  format_type: "colored"          # colored, json (use json in production)

# Structured audit parameters (audit engine)
auditing:
  enable_audit: true              # Toggle SQLite transaction auditing
  storage_provider: "sqlite"      # Storage engine (sqlite or remote)
  sqlite_db_path: "audit_logs/audit.db" # Database storage path (relative to CWD)

# MAESTRO Cryptographic defaults
security:
  enable_auth: true               # Enable JWS verification on endpoints
  encryption_enabled: true        # Enable AES-256-GCM transport encryption
  keystore_path: "keystore"       # Path to directory hosting keys
  master_secret: "b40ff79..."     # Hex string used as salt seed
  salt: "1f07447a8c4cda..."       # Fixed cryptocenter salt

# Custom Integration parameters
custom:
  # Ingestion API for external systems (Legacy Gatekeeper)
  ingestion_api:
    host: "127.0.0.1"
    port: 8005
    api_key: "a7b3c9f8d2e1a6b0c8d4e2f1..." # Static ingestion API Key

  # Anthropic MCP Server config
  mcp_server:
    host: "0.0.0.0"
    port: 8008

  # Discovery & P2P parameters
  discovery:
    strategy: "static"            # static (uses AGENTS.md) or dynamic
    communication_mode: "p2p"     # bridge or p2p (Direct handshakes)
    p2p_timeout: 300              # Direct connection timeout seconds

  # External micro-services wrapper configurations
  external_services:
    - name: "crewai_service"
      description: "CrewAI node optimization manager"
      mode: "local"               # local or remote
      address: "http://127.0.0.1:8001"
      topics: ["crewai_service_bridge"] # Pub/Sub channels to map
      network:
        timeout_total: 90
        timeout_connect: 15
        timeout_read: 90
        keepalive_timeout: 90
        max_retries: 5
        retry_delay_seconds: 3
```

---

## Security Gatekeepers: Ingestion API Key vs JWS Handshake

It is vital to distinguish how RayRabbit secures different boundaries:

### 1. Ingestion API Key (`custom.ingestion_api.api_key`)
This is a **static gatekeeper token**. It is used **ONLY** by external, non-agent legacy systems (such as traditional webhooks, backend servers, or simple cron triggers) to push events directly to Port 8005 `/api/v1/events/ingest`. It represents standard API-level security.

### 2. Peer-to-Peer JWS Handshake (Zero-Trust)
Sovereign agents do **NOT** use the static ingestion API Key to connect or authenticate. Instead, they register dynamically at Port 8005 `POST /api/security/register` using the **Multipath JWS Handshake**:
* The agent generates asymmetric encryption keys locally.
* It signs a dynamic time-fleshed challenge using its private key (proving *Proof of Possession* or PoP, which prevents replay attacks).
* The Hub verifies the signature, registers the agent's public key PEM, and returns the Hub's public key to establish a **Bidirectional Handshake**.
* All future MessageBus transmissions require unique JWS headers signed by the agent's unique key, guaranteeing that a compromised static API key can never be used to spoof an agent.
