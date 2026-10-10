# Acta de Consenso Técnico: [Agente DevOps] ⟷ [Agente Core & Arquitectura L3]

**Fecha:** 21 de Agosto de 2026  
**Sesiones Vinculadas:**
* **DevOps Agent (\\NAREDIGITAL-CRY):** `5e14ef42-67a6-4f0a-a6b4-421164002c58`
* **Core & L3 Architecture Agent (\\NAREDIGITAL-MAN):** `39b05c7e-f492-4cc8-b5d2-5ea4d4d23546`
**Correlation ID de Consenso:** `consenso-setup-dev-fce9f5ce`  
**Protocolo:** Google A2A / MAESTRO Zero-Trust (Firmado con JWS RSA-2048)  
**Canal de Auditoría:** `audit_logs/audit.db` (Evento `MESSAGE_PUBLISHED` verificado)

---

## 1. Contexto y Hallazgos Iniciales de DevOps en Kali Linux

Durante el aprovisionamiento de la máquina virtual Kali Linux (`kali@localhost:2222`), el Agente DevOps identificó 4 fricciones críticas:
1. **Falta de archivos `.env` en un clon fresco de GitHub:** El motor MAESTRO Zero-Trust detenía el arranque (`RuntimeError: CRITICAL: MAESTROSecurity requiere master_secret y salt`).
2. **Dependencias del SO ausentes:** En Debian/Kali, `python3 -m venv` requería `python3-venv` y `python3-full`.
3. **Colisiones de puertos en reinicios:** `cleanup_ports()` dependía de `lsof`, fallando cuando no estaba instalado.
4. **Timeouts ciegos en la CLI:** `rayrabbit start` esperaba 15 segundos fijos a ciegas antes de que los servicios estuvieran listos, arrojando `[Errno 111] Connect call failed`.

---

## 2. Propuestas Técnicas de DevOps y Ratificación del Core

El Agente DevOps propuso formalmente 3 ajustes de ingeniería, los cuales fueron **aprobados, implementados y validados al 100%** por el Agente Core:

### Ajuste 1: `setup_dev.sh` (Aprovisionamiento Desatendido Zero-Friction)
* **Detección Dinámica de Privilegios:** Evalúa si el usuario es `root` (`UID == 0`). Si es root, ejecuta directamente el gestor de paquetes; si es usuario estándar, usa `sudo`.
* **Modo No Interactivo:** `DEBIAN_FRONTEND=noninteractive apt-get update -qq && apt-get install -y --no-install-recommends ...`
* **Aprovisionamiento Base:** `python3-venv`, `python3-full`, `python3-pip`, `lsof`, `psmisc`, `sqlite3`, `build-essential`. Soporte multi-distro (`apt`, `dnf`, `pacman`, `apk`, `brew`).
* **Auto-Clonado Seguro de `.env`:** Si no existe `.env`, se copia desde `.env.example` en la raíz y en `examples/services/{crewai,autogen,langchain}/`.
* **Auto-Generación Criptográfica de Secretos:** Si `MAESTRO_MASTER_SECRET` o `MAESTRO_SALT` están vacíos o con valores por defecto, genera tokens criptográficos aleatorios de 64 y 32 caracteres hexadecimales de forma automática.

### Ajuste 2: `run_local_rayrabbit_cluster.py` (Liberación de Sockets Multi-OS)
* **Cascada de Limpieza en Linux/macOS:**
  $$\text{lsof -ti :<port>} \longrightarrow \text{fuser -k -9 <port>/tcp} \longrightarrow \text{ss -lptn}$$
* **Limpieza en Windows:** `netstat -ano -p TCP` + `taskkill /F /PID <pid>`.
* **Socket Release Polling:** Micro-bucle de espera activa de hasta 2.0 segundos verificando la liberación real del socket para eliminar colisiones `[Errno 98] Address already in use` por estados `TIME_WAIT`.
* **Soporte de Red:** El Hub escucha en `0.0.0.0:8005` (configurable vía `RAYRABBIT_HOST`) para permitir acceso tanto en `localhost` como a través de la red local (LAN/Wi-Fi/Ethernet).

### Ajuste 3: Smart Healthcheck y Retry Loop en la CLI
* **En `rayrabbit start`:** Reemplazado `time.sleep(15)` por un polling activo a `http://127.0.0.1:8005/health` que abre la interfaz de inmediato en cuanto el Hub está listo.
* **En `chatbot.py`:** Retry loop resiliente de hasta 15 intentos suaves para evitar errores de conexión al arrancar.

---

## 3. Estado de Verificación de Calidad (QA)

* **Suite de Pruebas Automatizadas:** `pytest` ejecutado con éxito (**71 passed in 48.32s — 100% de la suite**).
* **Transmisión A2A Verificada:** Mensaje de correlación `consenso-setup-dev-fce9f5ce` transmitido entre hosts (`\\NAREDIGITAL-CRY` $\rightarrow$ `\\NAREDIGITAL-MAN`) firmado con JWS y validado con `HTTP 200 OK`.
