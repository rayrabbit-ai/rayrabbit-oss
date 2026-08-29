# Referencia de Variables de Entorno

Esta guía consolida la totalidad de variables de entorno consumidas por el núcleo de RayRabbit y sus motores de inferencia multi-LLM (LiteLLM).

---

## Variables Core de RayRabbit

| Variable | Tipo de Dato | Valor por Defecto | Descripción |
|----------|--------------|-------------------|-------------|
| `RAYRABBIT_HOME` | `Ruta` | `~/.rayrabbit` | Carpeta raíz que custodia bases de datos locales, logs e históricos. |
| `RAYRABBIT_CONFIG` | `Ruta` | `./config.yaml` | Ruta absoluta al archivo `config.yaml` de variables de ejecución. |
| `RAYRABBIT_HUB_URL` | `URL` | `http://127.0.0.1:8005` | Dirección física de red del Servidor API Core. |
| `RAYRABBIT_KEYSTORE` | `Ruta` | `./keystore` | Carpeta local encargada de custodiar los certificados e identidades RSA. |
| `RAYRABBIT_LOG_LEVEL` | `Texto` | `INFO` | Filtro de auditoría y stdout: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `RAYRABBIT_INGEST_KEY`| `Hex` | `Ninguno` | Llave API necesaria para ingestar eventos externos en la ruta de red `/api/v1/events/ingest`. |

---

## Variables de Inferencia Multi-LLM (LiteLLM)

RayRabbit automatiza y estandariza el consumo de modelos de lenguaje mediante **LiteLLM**. Exporta los tokens correspondientes en su máquina virtual:

| Variable de Entorno | Proveedor de LLM | Descripción |
|---------------------|------------------|-------------|
| `GEMINI_API_KEY` | **Google Gemini** | Token de desarrollador de Google AI Studio (Requerido por defecto en LangChain). |
| `OPENAI_API_KEY` | **OpenAI** | Llave secreta estándar de la API de OpenAI (ej. `sk-...`). |
| `ANTHROPIC_API_KEY` | **Anthropic** | Llave de acceso del portal de Anthropic Console (ej. `sk-ant-...`). |
| `GROQ_API_KEY` | **Groq** | Token de la API de Groq para ejecuciones lógicas ultra-rápidas. |
| `OLLAMA_API_BASE` | **Ollama** | URL del servidor local de Ollama (por defecto es `http://localhost:11434`). |

---

!!! enterprise "RayRabbit Enterprise: Integración Vault"
    En clústeres regulados bajo **RayRabbit Enterprise**, inyectar tokens de IA o claves maestras directamente en variables de entorno del sistema operativo está bloqueado. El módulo **ARK** interactúa de forma directa con bóvedas corporativas (**KMS corporativo** o **AWS KMS**) usando credenciales mTLS temporales, manteniendo los secretos estrictamente en memoria volátil de forma segura.
