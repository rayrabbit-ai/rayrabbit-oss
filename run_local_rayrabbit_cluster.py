"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
"""
run_rayrabbit_cluster.py - Lanzador Unificado Dinámico del Ecosistema Soberano.
Una sola ventana, N nodos dinámicos, entornos virtuales soberanos (Cross-Platform).
"""

import sys
import os
import time
import socket
import re
import platform
import subprocess
import webbrowser
import shutil
from pathlib import Path
from colorama import Fore, Style, init

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
# import hunter  # Requerido: pip install hunter

# --- Rastreador de Flujo Real-time ---
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# seen_files = set()

# def trace_component_flow(event):
    # filename = os.path.abspath(event.filename)
    # fname = os.path.basename(filename)

    # # Solo rastrear archivos .py del proyecto y excluir el entorno virtual
    # is_venv = "venv_rayrabbit" in filename or ".venv" in filename or "site-packages" in filename
    # if not fname.endswith(".py") or not filename.startswith(PROJECT_ROOT) or is_venv:
        # return

    # # Evitar duplicidad en consola
    # if filename in seen_files:
        # return

    # rel_path = os.path.relpath(filename, PROJECT_ROOT)
    # print(f"{Fore.MAGENTA}[FLOW] {rel_path}{Style.RESET_ALL}")
    # seen_files.add(filename)

# # Activar tracing ANTES de la orquestación
# hunter.trace(
    # stdlib=False,
    # action=trace_component_flow,
# )

from rayrabbit.cli.orchestrator import SovereignOrchestrator, register_shutdown
from rayrabbit.utils.config import ConfigManager

# Inicialización de colores para Windows
init(autoreset=True)

# Puertos conocidos del ecosistema RayRabbit
CLUSTER_PORTS = [8001, 8002, 8003, 8005, 8006, 8007]

def get_remote_ports() -> set:
    """Identifica puertos de servicios configurados como 'remote' en config.yaml.
    Estos puertos NO deben ser limpiados ya que son gestionados externamente."""
    remote_ports = set()
    try:
        config_mgr = ConfigManager()
        config_file = Path.cwd() / "config.yaml"
        if not config_file.exists():
            return remote_ports
        config_mgr.load_from_file(config_file)
        ext_services = config_mgr.data.custom.get('external_services', [])
        for svc in ext_services:
            mode = svc.get('mode', 'local')
            address = svc.get('address', '')
            if mode != 'local' and address:
                # Extraer puerto de la URL (e.g. http://127.0.0.1:8001 -> 8001)
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(address)
                    if parsed.port:
                        remote_ports.add(parsed.port)
                except Exception:
                    pass
    except Exception:
        pass
    return remote_ports

def check_service_alive(url: str) -> bool:
    """Verifica si un servicio remoto responde via HTTP (Cross-Platform)."""
    if not url: return False
    try:
        from urllib import request, error
        import ssl
        req = request.Request(url, method='GET')
        req.add_header('User-Agent', 'RayRabbit-HealthCheck')
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with request.urlopen(req, timeout=3, context=ctx) as response:
            return True
    except error.HTTPError:
        # Si devuelve 404/401/500, el servidor web EXISTE y responde.
        return True
    except Exception:
        return False

def cleanup_ports(ports_to_clean):
    """Mata procesos huérfanos que retienen puertos del cluster anterior (Cross-Platform con cascada y polling)."""
    is_windows = platform.system() == "Windows"
    killed = []
    
    for port in ports_to_clean:
        try:
            if is_windows:
                # 1. Windows: netstat para encontrar PID en el puerto
                result = subprocess.run(
                    ["netstat", "-ano", "-p", "TCP"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        pid = parts[-1].strip()
                        if pid.isdigit() and int(pid) != os.getpid():
                            subprocess.run(["taskkill", "/F", "/PID", pid],
                                         capture_output=True, timeout=5)
                            killed.append((port, pid))
            else:
                # 2. Linux / macOS: Cascada multinivel (lsof -> fuser -> ss)
                port_killed = False
                
                # Nivel 1: lsof
                if shutil.which("lsof"):
                    try:
                        result = subprocess.run(
                            ["lsof", "-ti", f":{port}"],
                            capture_output=True, text=True, timeout=5
                        )
                        for pid in result.stdout.strip().splitlines():
                            if pid.isdigit() and int(pid) != os.getpid():
                                subprocess.run(["kill", "-9", pid], capture_output=True, timeout=5)
                                killed.append((port, pid))
                                port_killed = True
                    except Exception:
                        pass
                
                # Nivel 2: fuser (si lsof no encontró o no existe)
                if not port_killed and shutil.which("fuser"):
                    try:
                        res = subprocess.run(
                            ["fuser", "-k", "-9", f"{port}/tcp"],
                            capture_output=True, text=True, timeout=5
                        )
                        if res.returncode == 0:
                            killed.append((port, "fuser"))
                            port_killed = True
                    except Exception:
                        pass
                
                # Nivel 3: ss (Socket Statistics de iproute2)
                if not port_killed and shutil.which("ss"):
                    try:
                        res = subprocess.run(
                            ["ss", "-lptn", f"sport = :{port}"],
                            capture_output=True, text=True, timeout=5
                        )
                        for pid_match in re.finditer(r"pid=(\d+)", res.stdout):
                            pid = pid_match.group(1)
                            if pid.isdigit() and int(pid) != os.getpid():
                                subprocess.run(["kill", "-9", pid], capture_output=True, timeout=5)
                                killed.append((port, pid))
                    except Exception:
                        pass
        except Exception:
            pass
    
    if killed:
        print(f"{Fore.YELLOW}[CLEANUP] Procesos huerfanos eliminados: {', '.join(f':{p}(PID:{pid})' for p, pid in killed)}{Style.RESET_ALL}")
    
    # Micro-bucle de Socket Release Polling (evita [Errno 98] Address already in use por estados TIME_WAIT)
    start_poll = time.time()
    max_wait = 2.0
    while time.time() - start_poll < max_wait:
        all_free = True
        for port in ports_to_clean:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.05)
                    if s.connect_ex(("127.0.0.1", port)) == 0:
                        all_free = False
                        break
            except Exception:
                pass
        if all_free:
            break
        time.sleep(0.1)


def get_core_python_executable(root_dir: Path = None) -> str:
    """Detecta el intérprete Python base para el Hub y procesos del núcleo (Cross-Platform)."""
    if root_dir is None:
        root_dir = Path.cwd()
    is_windows = platform.system() == "Windows"
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

def get_python_executable(service_dir: Path, root_dir: Path = None) -> list:
    """
    Detecta el ejecutable de Python/uv correcto para el servicio.
    Prioriza el venv soberano, luego uv si está disponible, y finalmente el Python del núcleo.
    """
    is_windows = platform.system() == "Windows"
    
    # 1. Buscar venv soberano
    # Windows: venv/Scripts/python.exe | Linux/Mac: venv/bin/python
    venv_python = service_dir / ("venv/Scripts/python.exe" if is_windows else "venv/bin/python")
    
    if venv_python.exists():
        return [str(venv_python)]

    # 2. uv disponible en PATH → gestión automática sin venv manual
    if shutil.which("uv"):
        pyproject = service_dir / "pyproject.toml"
        req_txt = service_dir / "requirements.txt"
        if pyproject.exists() or req_txt.exists():
            return ["uv", "run", "--directory", str(service_dir), "python"]
            
    # 3. Fallback al Python del núcleo
    return [get_core_python_executable(root_dir)]

def get_dynamic_services():
    """
    Carga y mapea los servicios dinámicamente desde config.yaml.
    """
    config_mgr = ConfigManager()
    root_dir = Path.cwd()
    services = []
    
    # Cargar Configuración
    config_file = root_dir / "config.yaml"
    if not config_file.exists():
        print(f"{Fore.RED}[ERROR] config.yaml no encontrado en {root_dir}")
        sys.exit(1)
    
    config_mgr.load_from_file(config_file)
    core_py = get_core_python_executable(root_dir)
    
    # 1. Nodo CORE (HUB) - Siempre local con el entorno del núcleo (escuchando en todas las interfaces para red local/remota)
    hub_bind_host = os.getenv("RAYRABBIT_HOST", "0.0.0.0")
    services.append({
        "name": "HUB",
        "color": Fore.CYAN,
        "cmd": [core_py, "-m", "uvicorn", "api.server:app", "--port", "8005", "--host", hub_bind_host, "--log-level", "warning"],
        "cwd": str(root_dir)
    })

    # Dar tiempo al HUB para bindeo e inyectar keystore root
    # os.environ["RAYRABBIT_KEYSTORE"] = str(root_dir / "keystore")

    # 2. Descubrimiento de Servicios Externos Soberanos (LC, CR, AG, etc.)
    ext_services = config_mgr.data.custom.get('external_services', [])
    color_map = [Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.LIGHTMAGENTA_EX, Fore.LIGHTBLUE_EX]
    
    for i, svc in enumerate(ext_services):
        full_name = svc.get('name', 'unknown')
        mode = svc.get('mode', 'local')
        address = svc.get('address', '')
        
        if mode != 'local':
            # --- MODO REMOTE: Servicio federado o en la nube ---
            label = "".join([part[0].upper() for part in full_name.split('_') if part not in ['service', 'bridge']])
            if not label: label = full_name[:2].upper()
            
            # Verificar disponibilidad remota
            is_alive = check_service_alive(address) if address else False
            status = f"{Fore.GREEN}ONLINE{Style.RESET_ALL}" if is_alive else f"{Fore.RED}OFFLINE{Style.RESET_ALL}"
            print(f"  {Fore.CYAN}[REMOTE]{Style.RESET_ALL} {full_name} en {address} -> {status}")
            continue
            
        # Acrónimo Dinámico (LC, CR, AG, etc.)
        label = "".join([part[0].upper() for part in full_name.split('_') if part not in ['service', 'bridge']])
        if not label: label = full_name[:2].upper()
        
        # Localización de la carpeta del servicio
        s_base_name = full_name.replace("_service", "")
        service_dir = root_dir / "examples" / "services" / s_base_name
        script_path = service_dir / f"{full_name}.py"
        
        if script_path.exists():
            from rayrabbit.cli.node_manager import ensure_venv
            # Auto-provisioning del entorno virtual aislado (zero-friction UX)
            ensure_venv(service_dir, full_name, force_reinstall=False)
            
            # Detectar ejecutable soberano (su propio venv)
            python_cmd = get_python_executable(service_dir, root_dir)
            
            services.append({
                "name": label,
                "color": color_map[i % len(color_map)],
                "cmd": python_cmd + [str(script_path)],
                "cwd": str(service_dir)  # CWD soberano para carga de .env local
            })
        else:
            print(f"{Fore.YELLOW}[WARN] Script no encontrado para {full_name} en {script_path}")

    # 3. Servicios de Capa de Aplicación (UI, NS, BOT)
    # Estos nodos se leen dinámicamente desde la configuración. El orquestador base no debe
    # acoplarse a ningún caso de uso específico (ej. logística).
    app_nodes = config_mgr.data.custom.get('app_nodes', [])
    
    for node in app_nodes:
        full_path = root_dir / node["path"]
        if full_path.exists():
            services.append({
                "name": node.get("name", "APP"),
                "color": getattr(Fore, node.get("color", "WHITE").upper(), Fore.WHITE),
                "cmd": [core_py, str(full_path)],
                "cwd": str(root_dir)
            })

    return services

def set_process_branding():
    """Configura el título de la consola y branding del proceso multiplataforma."""
    if platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW("RayRabbit Ecosystem")
        except Exception:
            pass

def main():
    set_process_branding()
    # Identificar puertos remotos ANTES de la limpieza para no matarlos
    remote_ports = get_remote_ports()
    local_ports = [p for p in CLUSTER_PORTS if p not in remote_ports]
    
    if remote_ports:
        print(f"{Fore.CYAN}[REMOTE] Puertos federados detectados (excluidos de cleanup): {', '.join(f':{p}' for p in sorted(remote_ports))}{Style.RESET_ALL}")
    
    # Limpieza de puertos del cluster anterior (evita Errno 10048)
    # Solo limpia puertos de servicios LOCALES, respeta los remotos
    cleanup_ports(local_ports)
    
    # Obtener arquitectura de nodos
    all_services = get_dynamic_services()
    
    if not all_services:
        print(f"{Fore.RED}[ERROR] No se identificaron nodos locales para lanzar.")
        sys.exit(1)

    # Inyectar UTF-8 universal en el orquestador
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if platform.system() == "Windows":
        os.environ["PYTHONUTF8"] = "1"
        
    # Inyectar PYTHONPATH para resolver SDK local y herramientas (Evita sys.path/os.path en agentes)
    root_dir = Path.cwd()
    sdk_path = root_dir / "clients" / "python" / "rayrabbit_client" / "src"
    logistics_tools_path = root_dir / "examples" / "use_cases" / "logistics" / "tools"
    
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    paths_to_add = [str(sdk_path), str(logistics_tools_path)]
    if current_pythonpath:
        os.environ["PYTHONPATH"] = os.pathsep.join(paths_to_add + [current_pythonpath])
    else:
        os.environ["PYTHONPATH"] = os.pathsep.join(paths_to_add)
    
    # Inyectar RAYRABBIT_HOME para centralizar persistencia (Cross-Platform)
    # Removido para prevenir contaminación global. Se gestionará per-nodo en el Orchestrator.
    # os.environ["RAYRABBIT_HOME"] = str(Path.cwd() / ".rayrabbit_data")

    # --- SEPARACIÓN DE NODOS PARA LANZAMIENTO SECUENCIAL ---
    pre_req_services = [s for s in all_services if s['name'] in ['HUB']]
    agent_services = [s for s in all_services if s['name'] not in ['HUB', 'A2UI']]
    ui_services = [s for s in all_services if s['name'] == 'A2UI']

    # Inicializar orquestador con el Hub
    orchestrator = SovereignOrchestrator(pre_req_services)
    register_shutdown(orchestrator)
    orchestrator.start()
    
    # --- ESPERA ROBUSTA: Polling de Salud del Hub ---
    print(f"\n{Fore.YELLOW}Aguardando a que el Hub (Puerto 8005) esté saludable...{Style.RESET_ALL}")
    hub_ready = False
    for i in range(15):
        try:
            import httpx
            with httpx.Client(timeout=1.0) as client:
                resp = client.get("http://127.0.0.1:8005/health")
                if resp.status_code == 200:
                    print(f"{Fore.GREEN} Hub detectado y saludable.{Style.RESET_ALL}")
                    hub_ready = True
                    break
        except Exception:
            pass
        print(f"   {Fore.YELLOW}Hub no listo (Intento {i+1}/15)...{Style.RESET_ALL}")
        time.sleep(1)
    
    if not hub_ready:
        print(f"{Fore.RED} El Hub no respondió en 15s. Abortando cluster.{Style.RESET_ALL}")
        orchestrator.shutdown()
        sys.exit(1)
    
    # Lanzar Agentes
    if agent_services:
        print(f"\n{Fore.YELLOW}Lanzando Agentes Soberanos...{Style.RESET_ALL}")
        for svc in agent_services:
            orchestrator.start_node(svc)
    
    # Lanzar UI
    if ui_services:
        print(f"\n{Fore.YELLOW}Lanzando A2UI Dashboard Service...{Style.RESET_ALL}")
        for svc in ui_services:
            orchestrator.start_node(svc)

    # --- ESPERA ESTRATÉGICA PARA AGENTES ---
    provider = os.getenv("LLM_PROVIDER", "google").lower()
    is_local_model = provider in ["ollama", "local", "lmstudio"]
    
    if is_local_model:
        print(f"\n{Fore.YELLOW}Aguardando 120s para que los Agentes estabilicen sus servicios (Modelos Locales - Prewarm)...{Style.RESET_ALL}")
        time.sleep(120)
    else:
        print(f"\n{Fore.YELLOW}Aguardando 30s para que los Agentes estabilicen sus servicios (Modelos Cloud)...{Style.RESET_ALL}")
        time.sleep(30)
    
    # Lanzamiento de BOTs de validación omitido (nodos BOT obsoletos eliminados)
    
    print(f"\n{Fore.WHITE}Ecosistema RayRabbit: Todos los nodos lanzados.{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Dashboard: http://127.0.0.1:8005/dashboard/index.html")
    print(f"{Fore.CYAN}----------------------------------")
    
    # Autocarga de la UI con parámetros dinámicos del agente universal
    try:
        webbrowser.open("http://127.0.0.1:8005/dashboard/index.html?agentId=universal_a2ui_agent&streamId=default_dashboard")
    except:
        pass
    
    # Bucle infinito para orquestación persistente
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        orchestrator.shutdown()

if __name__ == "__main__":
    main()
