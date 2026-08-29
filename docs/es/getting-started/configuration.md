# Configuración y Variables de Entorno

RayRabbit centraliza sus parámetros mediante un archivo de configuración estático (`config.yaml`) y variables de entorno del sistema operativo. La inferencia multi-modelo se realiza nativamente a través de **LiteLLM**, lo que permite alternar proveedores de LLM sin alterar una sola línea de código fuente.

---

## El Esquema de config.yaml

El archivo `config.yaml` se sitúa en la raíz de su espacio de trabajo. Gobierna el comportamiento de colas persistentes del **MessageBus**, logging estructurado, auditorías forenses SQLite, credenciales MAESTRO y el ruteo estático del clúster.

A continuación se detalla su estructura típica para producción:

```yaml
# Configuración del MessageBus Core
message_bus:
  instance_id: "production_cluster_01"
  enable_persistence: true
  max_message_history: 1000

# Parámetros del gestor de auditoría (SQLite local)
auditing:
  enable_audit: true
  storage_provider: "sqlite"
  sqlite_db_path: "audit_logs/audit.db"

# Suite de Seguridad criptográfica MAESTRO
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
    communication_mode: "p2p"  # "bridge" o "p2p" (Handshake directo entre agentes)
    p2p_timeout: 300           # Tolerancia en segundos ante inferencias lentas en CPUs locales

  # Registro físico de micro-servicios externos
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

## Variables de Entorno Multi-LLM (LiteLLM)

RayRabbit no introduce bloqueos de proveedor (vendor lock-in) sobre modelos de lenguaje. Su pasarela de inferencia está impulsada por **LiteLLM**, facilitando la integración transparente con modelos en la nube (Gemini, OpenAI, Anthropic, Groq OpenRouter, etc) u locales (Ollama, vLLM).

Exporta las llaves criptográficas correspondientes en su terminal de comandos:

```bash
# Google Gemini (Inferencia principal recomendada)
export GEMINI_API_KEY="AIzaSy..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Groq (Inferencia de ultra-baja latencia)
export GROQ_API_KEY="gsk_..."

# Ollama local (si utiliza servidores open-source en localhost)
export OLLAMA_API_BASE="http://localhost:11434"
```

---

## Variables Core de RayRabbit

Parámetros internos del ciclo de vida y rutas de la infraestructura:

| Variable de Entorno | Propósito | Valor por Defecto |
|---------------------|-----------|-------------------|
| `RAYRABBIT_HOME` | Ruta absoluta para guardar logs, bases de datos locales y caches. | `~/.rayrabbit` |
| `RAYRABBIT_HUB_URL` | Dirección de red del Servidor Core API del clúster. | `http://127.0.0.1:8005` |
| `RAYRABBIT_KEYSTORE` | Directorio local donde se custodian las llaves RSA. | `./keystore` |
| `RAYRABBIT_CONFIG` | Ruta absoluta al archivo `config.yaml` de ejecución. | `./config.yaml` |
| `RAYRABBIT_LOG_LEVEL` | Filtro de verbosidad del terminal (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | `INFO` |

---

!!! enterprise "RayRabbit Enterprise: Gestión Soberana de Secretos"
    Custodiar llaves criptográficas de LLMs o master secrets de seguridad en archivos YAML planos o variables de entorno expuestas incumple las normativas corporativas **Zero-Trust**.
    
    El SDK **RayRabbit ARK** anula la resolución de credenciales desde variables del sistema en producción. En su lugar, se conecta nativamente a bóvedas de secretos empresariales (**HashiCorp Vault**, **AWS Secrets Manager**, **Google Secret Manager**) mediante certificados mTLS. Las llaves se recuperan JIT, existiendo estrictamente en la RAM y sin tocar jamás el almacenamiento físico.
