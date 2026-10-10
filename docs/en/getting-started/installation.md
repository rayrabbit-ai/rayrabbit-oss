# Multi-Platform Installation Guide

This guide covers installing RayRabbit OSS on Windows, Linux, and macOS, including optional dependencies for running sovereign LangChain, CrewAI, AutoGen microservices and the visual A2UI telemetry engine.

---

## Prerequisites

Before proceeding, ensure your environment meets the following requirements:
* **Python**: Versions `3.10`, `3.11`, `3.12`, and `3.13` supported.
* **OpenSSL**: Version `1.1.1` or higher (required for JWS signatures and RSA-4096 cryptocells).
* **Node.js**: Version `18+` (optional, required only for `@rayrabbit-client` and `@rayrabbit-a2ui` frontend development).

---

## 1. Zero-Friction Bootstrap from Source

The recommended path to initialize the complete development environment with isolated microservice environments:

```bash
# 1. Clone the repository
git clone https://github.com/rayrabbit-ai/rayrabbit-oss.git
cd rayrabbit-oss

# 2. Run the automated bootstrap installer
# On Windows:
setup_dev.bat

# On Linux / macOS:
chmod +x setup_dev.sh
./setup_dev.sh
```

The script automatically detects Python, creates an isolated virtual environment, installs core and service dependencies, and registers the `rayrabbit` CLI globally.

---

## 2. Client SDKs Installation

### Python Client SDK (`rayrabbit_client` - Apache 2.0)
```bash
pip install -e clients/python
```

### TypeScript / JavaScript SDKs (`@rayrabbit-client` & `@rayrabbit-a2ui`)
```bash
cd clients/javascript
npm install
npm run build
```

---

## 3. Platform Specific Notes

### Windows (PowerShell)
If you encounter permission errors when creating data folders under `~/.rayrabbit_data`:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux (Ubuntu/Debian)
Ensure your build-essential and OpenSSL development headers are installed:

```bash
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev
```

---

!!! enterprise "RayRabbit Enterprise: Enterprise Registries & Multi-Cloud SDKs"
    For enterprise SDK access, custom private registries, and hardware HSM key custody, contact our solutions architecture team at [Contact RayRabbit Development Team](mailto:sdichiera@duck.com?subject=Enterprise%20Architecture%20Inquiry).