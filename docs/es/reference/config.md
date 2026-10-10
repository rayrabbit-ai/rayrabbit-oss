# Referencia de config.yaml

Esta sección detalla el esquema estructurado de parámetros que rigen el comportamiento del clúster de RayRabbit en el archivo `config.yaml`.

---

## Esquema del Archivo de Configuración

```yaml
# ====================================================================
# Esquema de Configuración Core de RayRabbit
# ====================================================================

# Configuración del MessageBus
message_bus:
  instance_id: "default_instance" # Identificador físico del clúster
  enable_persistence: true        # Habilitar persistencia física en disco
  max_message_history: 1000       # Histórico de mensajes en memoria RAM

# Logger del sistema
logging:
  level: "INFO"                   # DEBUG, INFO, WARNING, ERROR
  format_type: "colored"          # colored, json (use json en producción)

# Parámetros del AuditManager (Base de datos SQLite local)
auditing:
  enable_audit: true              # Habilitar auditoría de transacciones
  storage_provider: "sqlite"      # sqlite o proveedor remoto
  sqlite_db_path: "audit_logs/audit.db" # Ruta física de almacenamiento (relativa a CWD)

# Parámetros criptográficos de MAESTRO
security:
  enable_auth: true               # Activar autenticación por firmas JWS
  encryption_enabled: true        # Habilitar cifrado simétrico AES-256-GCM
  keystore_path: "keystore"       # Carpeta de custodia de llaves RSA
  master_secret: "b40ff79..."     # Semilla secreta de derivación
  salt: "1f07447a8c4cda..."       # Salt fijo para derivación de claves

# Integraciones y puertos dinámicos
custom:
  # Ingestion API para sistemas externos (Gatekeeper Legacy)
  ingestion_api:
    host: "127.0.0.1"
    port: 8005
    api_key: "a7b3c9f8d2e1a6b0c8d4e2f1..." # Llave API estática

  # Servidor nativo de MCP Anthropic
  mcp_server:
    host: "0.0.0.0"
    port: 8008

  # Estrategia de descubrimiento y comunicación
  discovery:
    strategy: "static"            # static (lee AGENTS.md) o dynamic
    communication_mode: "p2p"     # bridge o p2p (Handshake directo)
    p2p_timeout: 300              # Timeout en segundos para enlaces P2P

  # Registro estático de micro-servicios federados
  external_services:
    - name: "crewai_service"
      description: "Servicio optimizador de rutas en CrewAI"
      mode: "local"               # local o remote
      address: "http://127.0.0.1:8001"
      topics: ["crewai_service_bridge"] # Canales pub/sub asociados
      network:
        timeout_total: 90
        timeout_connect: 15
        timeout_read: 90
        keepalive_timeout: 90
        max_retries: 5
        retry_delay_seconds: 3
```

---

## Filtros de Entrada: API Key Estática vs Handshake JWS (Zero-Trust)

Es fundamental comprender la diferencia en el control de acceso según las fronteras de red de RayRabbit:

### 1. Llave API de Ingestión (`custom.ingestion_api.api_key`)
Esta es una **llave API estática estándar**. Se utiliza **EXCLUSIVAMENTE** por sistemas externos y heredados (como webhooks, servidores backend tradicionales o simples activadores cron) para ingestar eventos directamente en la cola en la dirección `/api/v1/events/ingest` (Puerto 8005).

### 2. Handshake JWS Descentralizado (Zero-Trust Peer-to-Peer)
Los agentes de IA soberanos **NO** utilizan esta llave estática para conectarse ni para autenticarse. En su lugar, se registran en caliente en el endpoint del Hub `POST /api/security/register` mediante el **Handshake JWS**:
* El agente genera localmente su par de claves claves asimétricas de alta seguridad.
* Firma digitalmente un reto con sello de tiempo (Proof of Possession o PoP, bloqueando ataques de replay).
* El Hub valida la firma, guarda su clave pública PEM localmente y le devuelve la clave pública del Hub, configurando un **Handshake Bidireccional**.
* Todo mensaje futuro en el MessageBus requiere cabeceras con firmas JWS únicas del agente. Esto garantiza que un token de API estático comprometido jamás pueda ser utilizado para suplantar o hackear la identidad de un agente de IA en la red.
