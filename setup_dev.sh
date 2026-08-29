#!/usr/bin/env bash
# =========================================================================
# RayRabbit OSS - Universal Zero-Friction Bootstrap & Dev Setup (Unix/Linux/macOS)
# Copyright © 2024-2026 RayRabbit Labs, Inc.
# =========================================================================

set -e

# Colores para output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}==========================================================${NC}"
echo -e "${CYAN} RayRabbit OSS — Bootstrap Zero-Friction (L3 Infrastructure)${NC}"
echo -e "${CYAN}==========================================================${NC}"

# 1. Anclaje en Memoria (Directorio Raíz)
REPO_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$REPO_PATH"
echo -e "[Info] Directorio anclado: ${REPO_PATH}"

# 2. Detección Dinámica de Privilegios (Root vs Usuario Estándar)
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo &> /dev/null; then
        SUDO="sudo"
    else
        echo -e "${RED}[X] Se requieren privilegios de superusuario o tener 'sudo' instalado.${NC}"
        exit 1
    fi
fi

# 3. Detección e Instalación de Dependencias del Sistema Multi-Distro
echo -e "${CYAN}-> Verificando paquetes del sistema base (python3, venv, lsof, sqlite3, rustc)...${NC}"

if command -v apt-get &> /dev/null; then
    echo -e "  -> Gestor detectado: apt-get (Debian/Kali/Ubuntu/Mint)"
    $SUDO env DEBIAN_FRONTEND=noninteractive apt-get update -qq
    $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 python3-venv python3-full python3-pip lsof psmisc sqlite3 build-essential cargo rustc
elif command -v dnf &> /dev/null; then
    echo -e "  -> Gestor detectado: dnf (Fedora/RHEL/CentOS/Rocky)"
    $SUDO dnf install -y python3-devel python3-pip lsof psmisc sqlite gcc cargo rust
elif command -v pacman &> /dev/null; then
    echo -e "  -> Gestor detectado: pacman (Arch/Manjaro)"
    $SUDO pacman -S --noconfirm python python-pip lsof psmisc sqlite base-devel rust
elif command -v apk &> /dev/null; then
    echo -e "  -> Gestor detectado: apk (Alpine Linux)"
    $SUDO apk add --no-cache python3 py3-pip lsof psmisc sqlite build-base cargo rust
elif command -v brew &> /dev/null; then
    echo -e "  -> Gestor detectado: Homebrew (macOS)"
    brew install lsof sqlite python3 rust
else
    echo -e "${YELLOW}[!] Gestor de paquetes no reconocido. Asegurando que Python 3.10+ esté en el PATH.${NC}"
fi

# Seleccionar la mejor versión disponible de Python (preferir 3.13, 3.12, 3.11 sobre 3.14 alpha)
PY_BIN="python3"
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &> /dev/null; then
        PY_MAJOR=$($candidate -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo 0)
        PY_MINOR=$($candidate -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo 0)
        if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 10 ] && [ "$PY_MINOR" -le 13 ]; then
            PY_BIN="$candidate"
            break
        fi
    fi
done

PY_VERSION=$($PY_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}[OK] Intérprete Python seleccionado: ${PY_BIN} (v${PY_VERSION})${NC}"

# Validar módulo venv
if ! $PY_BIN -m venv -h &> /dev/null; then
    echo -e "${RED}[X] Error crítico: El módulo 'venv' de Python no está disponible en este sistema.${NC}"
    echo -e "    En Debian/Ubuntu/Kali ejecuta: apt install -y python3-venv"
    exit 1
fi

# 4. Configuración de Archivos de Entorno (.env) según Arquitectura Soberana
echo -e "${CYAN}-> Verificando archivos de entorno (.env) y configuración de nodos...${NC}"

generate_secret() {
    local bytes=$1
    $PY_BIN -c "import secrets; print(secrets.token_hex($bytes))" 2>/dev/null || openssl rand -hex "$bytes" 2>/dev/null || echo "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"
}

# A. .env del Core (ÚNICO lugar que almacena secretos de seguridad MAESTRO del Hub)
ROOT_ENV="${REPO_PATH}/.env"
if [ ! -f "$ROOT_ENV" ]; then
    ROOT_SECRET=$(generate_secret 32)
    ROOT_SALT=$(generate_secret 16)
    cat <<EOF > "$ROOT_ENV"
# ====================================================================
# RayRabbit OSS - Variables de Entorno & Seguridad MAESTRO
# ====================================================================
RAYRABBIT_MASTER_SECRET=${ROOT_SECRET}
RAYRABBIT_SALT=${ROOT_SALT}
RAYRABBIT_HOST=0.0.0.0
RAYRABBIT_PORT=8005
RAYRABBIT_LOG_LEVEL=INFO
EOF
    echo -e "  [🔒] Creado .env del Core con RAYRABBIT_MASTER_SECRET y RAYRABBIT_SALT generados."
else
    # Si existe pero le falta el secreto maestro, generarlo
    if ! grep -q "RAYRABBIT_MASTER_SECRET=" "$ROOT_ENV" || grep -q "RAYRABBIT_MASTER_SECRET=CHANGE_ME" "$ROOT_ENV" || grep -q 'RAYRABBIT_MASTER_SECRET=""' "$ROOT_ENV"; then
        ROOT_SECRET=$(generate_secret 32)
        sed -i "s/RAYRABBIT_MASTER_SECRET=.*/RAYRABBIT_MASTER_SECRET=${ROOT_SECRET}/g" "$ROOT_ENV" 2>/dev/null || echo "RAYRABBIT_MASTER_SECRET=${ROOT_SECRET}" >> "$ROOT_ENV"
        echo -e "  [🔒] Actualizado RAYRABBIT_MASTER_SECRET en .env del Core."
    fi
    if ! grep -q "RAYRABBIT_SALT=" "$ROOT_ENV" || grep -q "RAYRABBIT_SALT=CHANGE_ME" "$ROOT_ENV" || grep -q 'RAYRABBIT_SALT=""' "$ROOT_ENV"; then
        ROOT_SALT=$(generate_secret 16)
        sed -i "s/RAYRABBIT_SALT=.*/RAYRABBIT_SALT=${ROOT_SALT}/g" "$ROOT_ENV" 2>/dev/null || echo "RAYRABBIT_SALT=${ROOT_SALT}" >> "$ROOT_ENV"
        echo -e "  [🔒] Actualizado RAYRABBIT_SALT en .env del Core."
    fi
fi

# B. .env de Servicios Federados (Solo copian su plantilla .env.example, SIN MASTER_SECRET ni SALT)
copy_service_template() {
    local svc_example="$1"
    local svc_env="$2"
    if [ -f "$svc_example" ] && [ ! -f "$svc_env" ]; then
        mkdir -p "$(dirname "$svc_env")"
        cp "$svc_example" "$svc_env"
        echo -e "  [+] Inicializada plantilla de servicio: ${svc_env}"
    fi
}

copy_service_template "${REPO_PATH}/examples/services/crewai/.env.example" "${REPO_PATH}/examples/services/crewai/.env"
copy_service_template "${REPO_PATH}/examples/services/autogen/.env.example" "${REPO_PATH}/examples/services/autogen/.env"
copy_service_template "${REPO_PATH}/examples/services/langchain/.env.example" "${REPO_PATH}/examples/services/langchain/.env"
copy_service_template "${REPO_PATH}/rayrabbit/examples/.env.example" "${REPO_PATH}/rayrabbit/examples/.env"
copy_service_template "${REPO_PATH}/rayrabbit/examples/logistics_use_case/.env.example" "${REPO_PATH}/rayrabbit/examples/logistics_use_case/.env"

# 5. Creación del Entorno Virtual (VENV)
VENV_PATH="${REPO_PATH}/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${CYAN}-> Creando Entorno Virtual Soberano con ${PY_BIN} en 'venv/'...${NC}"
    $PY_BIN -m venv "$VENV_PATH"
else
    echo -e "[Info] Entorno Virtual existente en 'venv/'."
fi

PIP_EXE="${VENV_PATH}/bin/pip"
if [ ! -f "$PIP_EXE" ]; then
    echo -e "${RED}[X] Pip no encontrado en ${VENV_PATH}/bin/pip.${NC}"
    exit 1
fi

# 6. Instalación de Dependencias
echo -e "${CYAN}-> Actualizando pip, setuptools y wheel...${NC}"
"$PIP_EXE" install --upgrade pip setuptools wheel --quiet

echo -e "${CYAN}-> Instalando RayRabbit OSS en modo Editable (dev + all)...${NC}"
"$PIP_EXE" install -e ".[dev,all]"

# 7. Configuración de Identidad Visual y Acceso Directo de Escritorio
echo -e "${CYAN}-> Configurando identidad visual y acceso directo en el Escritorio...${NC}"
"${VENV_PATH}/bin/python" "${REPO_PATH}/scripts/create_desktop_shortcut.py" || true

# 8. Mensaje de Éxito y Resumen de Arranque
echo -e "${GREEN}==========================================================${NC}"
echo -e "${GREEN}✅ Infraestructura RayRabbit OSS Instalada Correctamente.${NC}"
echo -e "${GREEN}==========================================================${NC}"
echo ""
echo -e " Puedes iniciar el sistema con doble clic en el acceso directo '${CYAN}RayRabbit Ecosystem${NC}' en tu Escritorio,"
echo -e "   o activar el entorno en esta terminal con:"
echo -e "    ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo -e "Comandos principales:"
echo -e "    ${YELLOW}rayrabbit start${NC}     # Inicia el ecosistema completo"
echo -e "    ${YELLOW}rayrabbit cluster${NC}   # Inicia en consola interactiva"
echo -e "    ${YELLOW}rayrabbit stop${NC}      # Detiene todos los procesos del clúster"
echo ""
