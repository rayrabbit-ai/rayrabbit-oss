# MAESTRO Security Setup (RayRabbit OSS)


RayRabbit implements a strict **Zero-Trust** architecture using the MAESTRO framework. To prevent critical vulnerabilities and default passwords in production environments, the OSS version **strictly requires** the configuration of strong cryptographic secrets before the Hub can be started.

If you attempt to start the cluster without configuring these secrets, the system will throw a `RuntimeError` and halt as a protection measure.

---

## 1. Generating Cryptographic Secrets

You need to generate two secure hexadecimal values:
1. **Master Secret:** Used to derive the AES-256-GCM key that encrypts your RSA-4096 private keys at rest.
2. **Salt:** Used in the PBKDF2HMAC to strengthen key derivation against dictionary attacks.

You can easily generate them by executing the following Python commands in your terminal:

### Generate Master Secret (32 bytes)
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Generate Salt (16 bytes)
```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

---

## 2. Injecting Secrets (Configuration)

Once generated, you have two options to inject them into your infrastructure:

### Option A: `config.yaml` File (Recommended for Local Development)
Open your `config.yaml` file in the project root and paste them under the `security` section:

```yaml
security:
  enable_auth: true
  encryption_enabled: true
  keystore_path: "keystore"
  master_secret: "YOUR_GENERATED_MASTER_SECRET_HERE"
  salt: "YOUR_GENERATED_SALT_HERE"
```

### Option B: Environment Variables (Recommended for Production / CI/CD)
If you don't want to hardcode secrets in your YAML file, you can export them directly in your OS or `.env` file:

```bash
export RAYRABBIT_SECURITY_MASTER_SECRET="YOUR_GENERATED_MASTER_SECRET_HERE"
export RAYRABBIT_SECURITY_SALT="YOUR_GENERATED_SALT_HERE"
```

---

## 3. Security Folder Architecture (Bidirectional Handshake)

Upon successfully starting with the configured secrets, RayRabbit will automatically distribute the cryptographic files in the Hub's `.rayrabbit_data` folder following the isolation principle:

- **`.rayrabbit_data/identity/`**: Ultra-secure folder. This is where the local node's (e.g., the Hub's) private (`.key`) and public keys are stored. Private keys are encrypted at rest with AES-256-GCM using the `master_secret` you generated in step 1. **NEVER share the contents of this folder.**
- **`.rayrabbit_data/keystore/`**: Acts as the public directory or "trust database." This is where the `.pem` files (public keys) of External Agents (LangChain, CrewAI, AutoGen) that successfully complete the **HTTP Bidirectional Handshake (Mutual PoP)** with the Hub will be dynamically stored.

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# Configuración de Seguridad MAESTRO (RayRabbit OSS)
RayRabbit implementa una arquitectura estricta de **Zero-Trust** utilizando el framework MAESTRO. Para evitar vulnerabilidades críticas y contraseñas por defecto en entornos de producción, la versión OSS **requiere obligatoriamente** la configuración de secretos criptográficos fuertes antes de poder arrancar el Hub.

Si intentas iniciar el clúster sin configurar estos secretos, el sistema arrojará un `RuntimeError` y se detendrá como medida de protección.

---

## 1. Generación de Secretos Criptográficos

Necesitas generar dos valores hexadecimales seguros:
1. **Master Secret:** Usado para derivar la llave AES-256-GCM que encripta tus llaves privadas RSA-4096 en reposo.
2. **Salt:** Usado en el PBKDF2HMAC para fortalecer la derivación de la llave contra ataques de diccionario.

Puedes generarlos fácilmente ejecutando los siguientes comandos en tu terminal con Python:

### Generar Master Secret (32 bytes)
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Generar Salt (16 bytes)
```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

---

## 2. Inyección de Secretos (Configuración)

Una vez generados, tienes dos opciones para inyectarlos en tu infraestructura:

### Opción A: Archivo `config.yaml` (Recomendado para desarrollo local)
Abre tu archivo `config.yaml` en la raíz del proyecto y pégalos en la sección `security`:

```yaml
security:
  enable_auth: true
  encryption_enabled: true
  keystore_path: "keystore"
  master_secret: "ACA_TU_MASTER_SECRET_GENERADO"
  salt: "ACA_TU_SALT_GENERADO"
```

### Opción B: Variables de Entorno (Recomendado para Producción / CI/CD)
Si no deseas quemar secretos en tu archivo YAML, puedes exportarlos directamente en tu sistema operativo o archivo `.env`:

```bash
export RAYRABBIT_SECURITY_MASTER_SECRET="ACA_TU_MASTER_SECRET_GENERADO"
export RAYRABBIT_SECURITY_SALT="ACA_TU_SALT_GENERADO"
```

---

## 3. Arquitectura de Carpetas de Seguridad (Handshake Bidireccional)

Al arrancar exitosamente con los secretos configurados, RayRabbit distribuirá automáticamente los archivos criptográficos en la carpeta `.rayrabbit_data` del Hub siguiendo el principio de aislamiento:

- **`.rayrabbit_data/identity/`**: Carpeta ultra-segura. Aquí se guardan las llaves privadas (`.key`) y públicas del nodo local (por ejemplo, el Hub). Las llaves privadas están cifradas en reposo con AES-256-GCM utilizando el `master_secret` que generaste en el paso 1. **JAMÁS debes compartir el contenido de esta carpeta**.
- **`.rayrabbit_data/keystore/`**: Actúa como el directorio público o "base de datos de confianza". Aquí se almacenarán dinámicamente los archivos `.pem` (llaves públicas) de los Agentes Externos (LangChain, CrewAI, AutoGen) que completen exitosamente el **Handshake Bidireccional HTTP (Mutual PoP)** con el Hub.

</details>
