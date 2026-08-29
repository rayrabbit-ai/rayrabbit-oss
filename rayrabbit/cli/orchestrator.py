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
rayrabbit/cli/orchestrator.py - Professional Sovereign Cluster Manager.
📦 Maneja el ciclo de vida de los N nodos de RayRabbit en una sola terminal (Cross-Platform).
"""

import subprocess
import sys
import os
import signal
import threading
import time
import queue
from datetime import datetime
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

def disable_windows_quickedit():
    """Deshabilita el modo QuickEdit en Windows para evitar que clics de mouse congelen la ejecución I/O."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            hInput = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE = -10
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(hInput, ctypes.byref(mode)):
                ENABLE_QUICK_EDIT_MODE = 0x0040
                ENABLE_EXTENDED_FLAGS = 0x0080
                new_mode = (mode.value & ~ENABLE_QUICK_EDIT_MODE) | ENABLE_EXTENDED_FLAGS
                kernel32.SetConsoleMode(hInput, new_mode)
        except Exception:
            pass

class SovereignOrchestrator:
    def __init__(self, services):
        """
        Inicializa el orquestador profesional.
        services: Lista de diccionarios con {name, cmd, color}
        """
        disable_windows_quickedit()
        self.services = services
        self.processes = []
        self.running = False
        self.log_queue = queue.Queue()
        self.root_dir = Path.cwd()
        self.logs_dir = self.root_dir / ".rayrabbit_data" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _get_timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def _log_to_file(self, service_name, line):
        """Escribe logs persistentes en el disco con encoding UTF-8."""
        log_file = self.logs_dir / f"{service_name.lower().replace(' ', '_')}.log"
        try:
            with open(log_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"[{self._get_timestamp()}] {line}\n")
        except Exception as e:
            # Fallback silencioso si falla la escritura en disco para no bloquear el stream
            pass

    def _reader_thread(self, name, pipe, color):
        """Lee el pipe de un proceso y lo enruta al multiplexor y al disco."""
        for line in iter(pipe.readline, b''):
            if not self.running:
                break
            try:
                # Intenta decodificar como UTF-8, reemplazando caracteres inválidos
                decoded_line = line.decode('utf-8', errors='replace').strip()
                if decoded_line:
                    # Enviar a la terminal central con colores y flush inmediato
                    print(f"{color}[{name}]{Style.RESET_ALL} {decoded_line}", flush=True)
                    # Persistir en disco
                    self._log_to_file(name, decoded_line)
            except Exception as e:
                # No imprimo errores de logeo para evitar bucles de ruido
                pass
        pipe.close()

    def start(self):
        """Lanza todos los servicios configurados que aún no estén corriendo."""
        if not self.running:
            self.running = True
            print(f"\n{Fore.CYAN}{Style.BRIGHT}>> INICIANDO INFRAESTRUCTURA SOBERANA RAYRABBIT...")
            print(f"{Fore.WHITE}Directorio Raíz: {self.root_dir}")
            print(f"{Fore.WHITE}Logs persistentes en: {self.logs_dir}\n")

        for svc in self.services:
            # Evitar lanzar duplicados si ya están en self.processes
            if any(name == svc["name"] for p, name in self.processes):
                continue
            self.start_node(svc)
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}--- ECOSISTEMA ONLINE. Presiona Ctrl+C para finalizar. ---\n")

    def start_node(self, svc):
        """Lanza un único nodo configurando su entorno soberano."""
        self.running = True
        name = svc["name"]
        cmd = svc["cmd"]
        color = svc.get("color", Fore.WHITE)
            
        # Preparar entorno del subproceso
        env = os.environ.copy()
        
        # Robustez de PYTHONPATH (Cross-Platform)
        existing_pythonpath = env.get("PYTHONPATH", "")
        new_pythonpath = str(self.root_dir)
        if existing_pythonpath:
            env["PYTHONPATH"] = f"{new_pythonpath}{os.pathsep}{existing_pythonpath}"
        else:
            env["PYTHONPATH"] = new_pythonpath
            
        env["PYTHONUNBUFFERED"] = "1"
        
        # Fuerza UTF-8 para evitar UnicodeEncodeError en Windows
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        
        # Inyectar RAYRABBIT_HOME para centralizar persistencia (Cross-Platform)
        # Asegurar que solo el HUB y nodos Core usen la raíz para no romper la Soberanía
        if name in ["HUB", "NS", "BOT", "A2UI"]:
            if "RAYRABBIT_HOME" not in env:
                env["RAYRABBIT_HOME"] = str(self.root_dir / ".rayrabbit_data")
        else:
            if "RAYRABBIT_HOME" in env:
                del env["RAYRABBIT_HOME"]
        
        # Determinar CWD soberano: si el servicio define su propio cwd, usarlo
        service_cwd = str(Path(svc["cwd"]).resolve()) if svc.get("cwd") else str(self.root_dir)

        try:
            # Lanzamiento agnóstico de procesos
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=service_cwd,
                env=env,
                bufsize=0,
                universal_newlines=False # Manejo manual de bytes para mayor control de encoding
            )
            self.processes.append((p, name))
            
            # Hilo de streaming dedicado para multiplexación
            threading.Thread(
                target=self._reader_thread, 
                args=(name, p.stdout, color), 
                daemon=True
            ).start()
            
            print(f" {Fore.GREEN}* {Fore.WHITE}Soberano '{name}' lanzado (PID: {p.pid})")
            time.sleep(0.3) # Pequeña pausa para no saturar el arranque del Hub
        except Exception as e:
            print(f" {Fore.RED}X Error lanzando '{name}': {e}")

    def shutdown(self, signum=None, frame=None):
        """Cierre atómico y ordenado de todos los subprocesos."""
        if not self.running:
            return
        self.running = False
        print(f"\n\n{Fore.YELLOW}[SHUTDOWN] Deteniendo infraestructura RayRabbit...")
        
        # Invertir orden de cierre (Cerrar primero los clientes, luego el Hub)
        for p, name in reversed(self.processes):
            if p.poll() is None:
                print(f"  Finalizando {name}...")
                p.terminate()
                try:
                    p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    p.kill()
        
        print(f"{Fore.GREEN}[SUCCESS] Infraestructura cerrada correctamente.{Style.RESET_ALL}")
        # Pequeño delay para asegurar que los procesos hijos se retiren
        time.sleep(0.5)
        os._exit(0) # Salida forzada para evitar hilos colgados

def register_shutdown(orchestrator):
    """Asocia señales de interrupción al orquestador."""
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, orchestrator.shutdown)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, orchestrator.shutdown)
