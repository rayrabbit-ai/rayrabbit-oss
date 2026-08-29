"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""

import subprocess
import sys
import os
import signal
import time
import importlib.util
from urllib import request, error
import argparse

# --- Configuración ---
# --- Configuración Base ---
CORE_MODULE = "uvicorn"
# Nota: api.server debe ser importable. En modo dev (-e .), el root está en path.
CORE_ARGS = ["api.server:app", "--host", "0.0.0.0", "--port", "8005", "--log-level", "info"]

RAYRABBIT_API_URL = "http://127.0.0.1:8005"
HEALTH_ENDPOINT = f"{RAYRABBIT_API_URL}/api/health"

# --- Estado Global ---
processes = []

def signal_handler(sig, frame):
    print("\n[CLI] Deteniendo Ecosistema RayRabbit...")
    terminate_all()
    sys.exit(0)

def terminate_all():
    """Detiene todos los subprocesos registrados."""
    for p, name in processes:
        if p.poll() is None:
            print(f"[CLI] Deteniendo {name} (PID: {p.pid})...")
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill() # Forzar si no responde
    print("[CLI] Limpieza completada.")

def check_health(url, retries=30, delay=1):
    """Espera a que un endpoint HTTP devuelva 200 OK."""
    print(f"[CLI] Esperando {url}...", end="", flush=True)
    for i in range(retries):
        try:
            with request.urlopen(url) as response:
                if response.getcode() == 200:
                    print(" OK!")
                    return True
        except error.URLError:
            pass
        except ConnectionResetError:
            pass
            
        print(".", end="", flush=True)
        time.sleep(delay)
    print(" TIMEOUT!")
    return False

def run_module(module_name, args=[], name="Unknown", background=False, new_console=False):
    """
    Ejecuta un módulo Python como script (-m) de forma agnóstica.
    """
    cmd = [sys.executable, "-m", module_name] + args
    
    print(f"[CLI] Iniciando {name}...")
    print(f"      CMD: {' '.join(cmd)}")
    
    # IMPORTANTE: Heredamos el entorno actual, que debe tener configurado el PATH correctly
    kwargs = {
        "env": os.environ.copy(),
        "cwd": os.getcwd() # Ejecuta en el directorio actual (útil para configs locales)
    }

    if new_console and os.name == 'nt':
        # En Windows, abrir nueva ventana para servicios externos
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    
    if background:
         pass

    p = subprocess.Popen(cmd, **kwargs)
    processes.append((p, name))
    return p

def main():
    parser = argparse.ArgumentParser(description="RayRabbit CLI Runner")
    parser.add_argument("--services", required=True, help="Módulo de servicios externos a iniciar (ej. my_app.services)")
    parser.add_argument("--validation", required=True, help="Módulo de validación AAIF a ejecutar (ej. my_app.validation)")
    args = parser.parse_args()

    # Registrar manejo de Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    print("="*60)
    print(" RAYRABBIT INFRASTRUCTURE RUNNER (Managed CLI) ".center(60, "="))
    print("="*60)
    print(f"Python: {sys.executable}")
    print(f"CWD:    {os.getcwd()}")
    print("-" * 60)

    # 1. Iniciar Core (API Server)
    # Usamos uvicorn como módulo directamente
    core_process = run_module(CORE_MODULE, CORE_ARGS, name="RayRabbit Core (API)", background=True)
    
    # 2. Esperar a que el Core esté listo
    if not check_health(HEALTH_ENDPOINT):
        print("[ERROR] El servidor Core no inició correctamente.")
        terminate_all()
        sys.exit(1)

    # 3. Iniciar Servicios Externos
    # En Windows, nueva consola para ver sus logs separados. En Unix, background.
    use_new_console = (os.name == 'nt')
    services_process = run_module(args.services, [], name="External Services Cluster", background=True, new_console=use_new_console)
    
    # Esperamos un poco a que arranquen los servicios (el propio script de servicios tarda un poco)
    print("[CLI] Esperando inicialización de servicios (10s)...")
    time.sleep(10)

    # 4. Iniciar Validación E2E (AAIF)
    # Este corre en foreground (bloqueante) hasta terminar
    print("\n[CLI] Ejecutando Validación AAIF...")
    validation_process = run_module(args.validation, [], name="AAIF Validator")
    
    exit_code = validation_process.wait()
    
    print("-" * 60)
    if exit_code == 0:
        print("[CLI] ✅ Validación completada exitosamente.")
    else:
        print(f"[CLI] ❌ Validación falló con código {exit_code}.")

    print("[CLI] Presiona Ctrl+C para detener el ecosistema restante.")
    
    try:
        core_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
