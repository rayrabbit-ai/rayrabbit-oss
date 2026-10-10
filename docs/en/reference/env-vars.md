# Environment Variables Reference

This reference lists all environmental variables recognized by the core RayRabbit engine and its Multi-LLM inference backends.

---

## RayRabbit Core Variables

| Variable | Type | Default Value | Description |
|----------|------|---------------|-------------|
| `RAYRABBIT_HOME` | `Path` | `~/.rayrabbit` | Root directory containing local databases, cached models, and session data. |
| `RAYRABBIT_CONFIG` | `Path` | `./config.yaml` | Path to the active `config.yaml` parameters file. |
| `RAYRABBIT_HUB_URL` | `URL` | `http://127.0.0.1:8005` | Endpoint address of the Core API Server. |
| `RAYRABBIT_KEYSTORE` | `Path` | `./keystore` | Path to the directory where identity private/public key pairs are saved. |
| `RAYRABBIT_LOG_LEVEL` | `String` | `INFO` | Output verbosity filter: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `RAYRABBIT_INGEST_KEY` | `Hex` | `None` | Authentication token required to push events directly to Port 8005 `/api/v1/events/ingest`. |

---

## Multi-LLM & LiteLLM Variables

RayRabbit coordinates model access via **LiteLLM**. Ensure you export keys matching your active agent providers:

| Variable | Provider | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | **Google Gemini** | Authentic Google Developer token (Required for LangChain inventory node by default). |
| `OPENAI_API_KEY` | **OpenAI** | Standard OpenAI secret key (e.g. `sk-...`). |
| `ANTHROPIC_API_KEY` | **Anthropic** | Anthropic API key (e.g. `sk-ant-...`). |
| `GROQ_API_KEY` | **Groq** | Groq developer token for low-latency inference pipelines. |
| `OLLAMA_API_BASE` | **Ollama** | Base address of local Ollama server (defaults to `http://localhost:11434`). |

---

!!! enterprise "RayRabbit Enterprise: Vault Binding"
    In corporate production nodes running **RayRabbit Enterprise**, exporting secrets in environment variables is blocked by the runtime. The **ARK** fetches these tokens dynamically from cloud storage repositories (such as Google Secret Manager or enterprise KMS) using JIT short-lived authorization tokens, keeping them strictly in volatile memory.
