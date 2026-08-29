"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import argparse
import sys
import platform
from pathlib import Path
from rayrabbit.version import __version__

def set_process_branding():
    """Configura el título de la consola y branding del proceso multiplataforma."""
    if platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW("RayRabbit Ecosystem")
        except Exception:
            pass

def cli_entry_ecosystem():
    """Punto de entrada directo para 'rayrabbit-ecosystem'."""
    set_process_branding()
    cwd = Path.cwd()
    cluster_script = cwd / "run_local_rayrabbit_cluster.py"
    if cluster_script.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("run_local_rayrabbit_cluster", cluster_script)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.main()
            return
    try:
        import run_local_rayrabbit_cluster
        run_local_rayrabbit_cluster.main()
    except Exception as e:
        print(f"Error cargando el ecosistema: {e}")
        print("Asegúrate de ejecutar este comando desde la raíz del proyecto (donde está config.yaml).")
        sys.exit(1)

def cli_entry():
    """Punto de entrada principal para la CLI 'rayrabbit'."""
    set_process_branding()
    parser = argparse.ArgumentParser(
        description="RayRabbit OSS CLI - Infraestructura de Interoperabilidad de IA"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"RayRabbit CLI v{__version__}",
        help="Muestra la versión de RayRabbit CLI y finaliza."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Comando 'cluster' / 'ecosystem'
    subparsers.add_parser("cluster", help="Levanta el ecosistema soberano (Hub + Servicios federados)")
    subparsers.add_parser("ecosystem", help="Levanta el ecosistema soberano (Alias de cluster)")
    
    # Comando 'chat'
    chat_parser = subparsers.add_parser("chat", help="Lanza el cliente interactivo A2UI Chatbot")
    chat_parser.add_argument("-q", "--query", type=str, help="Ejecuta una consulta one-shot en vez de interactivo", default=None)
    
    # Comando 'start' (Todo en Uno)
    subparsers.add_parser("start", help="[UX] Inicia el ecosistema en una nueva ventana y abre el chat aquí")
    
    # Comando 'install'
    subparsers.add_parser("install", help="Aprovisiona los entornos virtuales (venvs) para los nodos locales")
    
    # Parse args
    args = parser.parse_args()
    
    if args.command in ("cluster", "ecosystem"):
        cli_entry_ecosystem()
            
    elif args.command == "chat":
        try:
            from rayrabbit.cli import chatbot
            if args.query:
                sys.argv = ["chatbot", "-q", args.query]
            else:
                sys.argv = ["chatbot"]
            chatbot.main()
        except ImportError as e:
            print(f"Error cargando el chatbot: {e}")
            sys.exit(1)
            
    elif args.command == "start":
        import subprocess
        import time
        import shutil
        
        print("\n=== RayRabbit Ecosystem Launcher ===")
        cmd = ["rayrabbit", "cluster"] if shutil.which("rayrabbit") else [sys.executable, "-m", "rayrabbit.cli.main", "cluster"]
        
        if platform.system() == "Windows":
            print("-> Levantando el ecosistema en una nueva ventana de diagnóstico...")
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            print("-> Levantando el ecosistema en segundo plano (logs redirigidos a cluster.log)...")
            log_file = Path("cluster.log").open("w", encoding="utf-8")
            subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
            
        print("-> Aguardando a que el Hub (Puerto 8005) esté saludable...")
        import urllib.request
        hub_ready = False
        max_wait_seconds = 90
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                req = urllib.request.Request("http://127.0.0.1:8005/health", headers={"User-Agent": "RayRabbit-CLI"})
                with urllib.request.urlopen(req, timeout=1.5) as response:
                    if response.status == 200:
                        hub_ready = True
                        break
            except Exception:
                pass
            time.sleep(1.5)
            print(".", end="", flush=True)
        print()
        
        if hub_ready:
            print("-> ¡Hub en línea y saludable! Iniciando interfaz interactiva...\n")
        else:
            print("-> [Aviso] El Hub está tardando en iniciar (posiblemente instalando venvs). Intentando conectar de todas formas...\n")
        
        try:
            from rayrabbit.cli import chatbot
            sys.argv = ["chatbot"]
            chatbot.main()
        except ImportError as e:
            print(f"Error cargando el chatbot: {e}")
            sys.exit(1)
            
    elif args.command == "install":
        try:
            from rayrabbit.cli.node_manager import force_install_all
            from rayrabbit.utils.config import ConfigManager
            config_mgr = ConfigManager()
            config_file = Path.cwd() / "config.yaml"
            if config_file.exists():
                config_mgr.load_from_file(config_file)
            force_install_all(config_mgr)
        except ImportError as e:
            print(f"Error cargando los módulos de instalación: {e}")
            sys.exit(1)
            
    else:
        parser.print_help()

if __name__ == "__main__":
    cli_entry()

