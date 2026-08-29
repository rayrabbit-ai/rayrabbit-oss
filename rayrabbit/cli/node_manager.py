"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Gestor de Nodos Soberanos para la CLI.
Maneja la instalación automatizada y el aislamiento de dependencias para los frameworks externos
en modo 'Playground Local', preservando la regla de Autonomía del Framework.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from colorama import Fore, Style

def get_base_python_executable(root_dir: Path = None) -> str:
    """Retorna el intérprete Python base del sistema o del venv raíz (Cross-Platform)."""
    if root_dir is None:
        root_dir = Path.cwd()
    is_windows = sys.platform == "win32"
    root_venv_py = root_dir / ("venv/Scripts/python.exe" if is_windows else "venv/bin/python")
    if root_venv_py.exists():
        return str(root_venv_py)
    if not getattr(sys, 'frozen', False):
        return sys.executable
    for candidate in ["python", "python3"]:
        found = shutil.which(candidate)
        if found:
            return found
    return sys.executable

def get_python_executable_for_venv(venv_dir: Path) -> str:
    """Retorna la ruta al ejecutable de Python dentro de un venv según el SO."""
    if sys.platform == "win32":
        return str(venv_dir / "Scripts" / "python.exe")
    return str(venv_dir / "bin" / "python")

def ensure_venv(service_dir: Path, service_name: str, force_reinstall: bool = False) -> bool:
    """
    Garantiza que un servicio tenga su entorno virtual (venv) creado y sus dependencias instaladas.
    Si el venv ya existe y force_reinstall es False, asume que está listo y lo omite rápido.
    """
    venv_dir = service_dir / "venv"
    requirements_path = service_dir / "requirements.txt"
    
    # Si ya existe y no forzamos reinstalación, omitimos (Arranque rápido)
    if venv_dir.exists() and not force_reinstall:
        return True

    print(f"{Fore.CYAN}[NodeManager]{Style.RESET_ALL} Preparando entorno aislado para '{service_name}'...")
    
    # Limpieza en caso de force_reinstall o corrupción
    if venv_dir.exists():
        try:
            shutil.rmtree(venv_dir)
        except Exception as e:
            print(f"{Fore.RED}[NodeManager]{Style.RESET_ALL} Error limpiando venv antiguo para {service_name}: {e}")
            return False

    try:
        # 1. Crear VENV con el Python base real
        base_py = get_base_python_executable()
        subprocess.run([base_py, "-m", "venv", str(venv_dir)], check=True, capture_output=True)
        
        # Preparar logs de auditoría para la instalación
        audit_dir = Path.cwd() / "audit_logs"
        audit_dir.mkdir(exist_ok=True)
        log_stdout = audit_dir / f"{service_name}_install_stdout.log"
        log_stderr = audit_dir / f"{service_name}_install_stderr.log"
        
        python_exe = get_python_executable_for_venv(venv_dir)
        
        # 2. Actualizar PIP
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], 
                       check=True, capture_output=True)
        
        # 3. Instalar Dependencias (Si existe requirements.txt)
        if requirements_path.exists():
            print(f"  -> Instalando dependencias de {service_name} (Esto puede tomar unos segundos)...")
            with open(log_stdout, "w") as out_f, open(log_stderr, "w") as err_f:
                res = subprocess.run([python_exe, "-m", "pip", "install", "-r", str(requirements_path)],
                                     stdout=out_f, stderr=err_f, text=True)
                if res.returncode != 0:
                    print(f"{Fore.RED}  -> [ERROR] Falló la instalación de {service_name}. Revisa: {log_stderr}{Style.RESET_ALL}")
                    return False
        
        print(f"{Fore.GREEN}  -> Entorno para '{service_name}' instalado y listo.{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}[NodeManager]{Style.RESET_ALL} Error crítico aprovisionando {service_name}: {e}")
        return False

def force_install_all(config_mgr):
    """
    Itera sobre todos los servicios externos definidos en config.yaml y fuerza su instalación
    solo si están configurados en mode: local.
    """
    ext_services = config_mgr.data.custom.get('external_services', [])
    root_dir = Path.cwd()
    installed_count = 0
    
    print(f"\n{Fore.MAGENTA}=== Instalador de Nodos del Playground de RayRabbit ==={Style.RESET_ALL}")
    
    for svc in ext_services:
        mode = svc.get('mode', 'local')
        full_name = svc.get('name', 'unknown')
        
        if mode != 'local':
            print(f"[{Fore.YELLOW}OMITIDO{Style.RESET_ALL}] '{full_name}' está en mode: remote. Su instalación es gestionada externamente (Enterprise/BYOA).")
            continue
            
        # Determinar ruta del servicio
        s_base_name = full_name.replace("_service", "")
        service_dir = root_dir / "examples" / "services" / s_base_name
        
        if not service_dir.exists():
            print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] No se encontró el directorio para '{full_name}' en {service_dir}")
            continue
            
        success = ensure_venv(service_dir, full_name, force_reinstall=True)
        if success:
            installed_count += 1
            
    print(f"\n{Fore.GREEN}Instalación completada. {installed_count} nodos locales aprovisionados exitosamente.{Style.RESET_ALL}")
