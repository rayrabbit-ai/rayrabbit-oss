# Guía de Instalación Multiplataforma

Esta guía detalla cómo instalar RayRabbit OSS en Windows, Linux y macOS, incluyendo las dependencias opcionales para ejecutar los microservicios soberanos independientes de LangChain, CrewAI, AutoGen y el motor visual de telemetría A2UI.

---

## Requisitos Previos

Antes de proceder, asegúrese de cumplir con los siguientes requisitos en su entorno:
* **Python**: Versiones soportadas `3.10`, `3.11`, `3.12` y `3.13`.
* **OpenSSL**: Versión `1.1.1` o superior (para firmas criptográficas JWS y claves RSA-4096).
* **Node.js**: Versión `18+` (opcional, requerida únicamente para desarrollo en `@rayrabbit-client` y `@rayrabbit-a2ui`).

---

## 1. Instalación Rápida con Scripts Bootstrap

La forma recomendada para inicializar el entorno de desarrollo con dependencias completas y entornos aislados:

```bash
# 1. Clonar el repositorio
git clone https://github.com/rayrabbit-ai/rayrabbit-oss.git
cd rayrabbit-oss

# 2. Ejecutar el instalador automatizado
# En Windows:
setup_dev.bat

# En Linux / macOS:
chmod +x setup_dev.sh
./setup_dev.sh
```

El script detecta la versión de Python, genera un entorno virtual aislado (`venv`), instala las dependencias del Core y de los microservicios, y configura la CLI `rayrabbit` de forma global.

---

## 2. Instalación de SDKs de Cliente

### SDK para Python (`rayrabbit_client` - Apache 2.0)
```bash
pip install -e clients/python
```

### SDKs para TypeScript / JavaScript (`@rayrabbit-client` y `@rayrabbit-a2ui`)
```bash
cd clients/javascript
npm install
npm run build
```

---

## 3. Notas Específicas del Sistema Operativo

### Windows (PowerShell)
Si experimenta fallos de permisos al crear carpetas de datos criptográficos o bases de datos en `~/.rayrabbit_data`:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux (Ubuntu/Debian)
Asegúrese de instalar las herramientas de compilación para los módulos criptográficos:

```bash
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev
```

---

!!! enterprise "RayRabbit Enterprise: Repositorios y SDKs Corporativos"
    Para acceder al SDK empresarial, aprovisionamiento automatizado en clústeres multi-cloud y gestión de claves HSM, contacte a nuestro equipo de arquitectura en [Contact RayRabbit Development Team](mailto:sdichiera@duck.com?subject=Consulta%20Arquitectura%20Enterprise).