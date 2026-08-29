"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.
SPDX-License-Identifier: AGPL-3.0-only
"""
import sys
import platform
import subprocess
from pathlib import Path

def get_desktop_dir() -> Path:
    """Obtiene la ruta del Escritorio del usuario de forma agnóstica."""
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        # Fallback a directorio home si no existe Desktop
        return Path.home()
    return desktop

def refresh_windows_shell():
    """Invalida la caché de iconos de Windows Shell y fuerza el redibujado del escritorio."""
    if platform.system() == "Windows":
        try:
            import ctypes
            # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0x0000
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        except Exception:
            pass

def create_windows_shortcut(target_exe: Path, icon_path: Path, working_dir: Path, arguments: str = "") -> Path:
    """Crea un acceso directo .lnk en el Escritorio de Windows usando PowerShell WScript.Shell."""
    desktop = get_desktop_dir()
    shortcut_path = desktop / "RayRabbit Ecosystem.lnk"
    
    # Eliminar acceso directo previo para forzar a Windows a leer el nuevo icono
    if shortcut_path.exists():
        try:
            shortcut_path.unlink()
        except Exception:
            pass
            
    ps_script = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path.resolve()}")
    $Shortcut.TargetPath = "{target_exe.resolve()}"
    $Shortcut.Arguments = "{arguments}"
    $Shortcut.WorkingDirectory = "{working_dir.resolve()}"
    $Shortcut.Description = "RayRabbit Ecosystem - Universal Interoperability Infrastructure"
    $Shortcut.IconLocation = "{icon_path.resolve()}, 0"
    $Shortcut.Save()
    """
    
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True)
    refresh_windows_shell()
    return shortcut_path

def create_linux_shortcut(target_exe: Path, icon_path: Path, working_dir: Path, arguments: str = "") -> Path:
    """Crea un acceso directo .desktop en el Escritorio de Linux."""
    desktop = get_desktop_dir()
    shortcut_path = desktop / "RayRabbit Ecosystem.desktop"
    
    exec_cmd = f'"{target_exe.resolve()}" {arguments}'.strip()
    content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=RayRabbit Ecosystem
GenericName=AI Interoperability Infrastructure L3
Comment=Universal Interoperability Infrastructure for AI Agents (AI TCP/IP + TLS + HTTP)
Exec={exec_cmd}
Path="{working_dir.resolve()}"
Icon={icon_path.resolve()}
Terminal=true
Categories=Development;System;Network;
StartupNotify=true
StartupWMClass=RayRabbit Ecosystem
"""
    shortcut_path.write_text(content, encoding="utf-8")
    shortcut_path.chmod(0o755)
    return shortcut_path

def create_macos_shortcut(target_app: Path) -> Path:
    """Crea un alias/enlace simbólico en el Escritorio de macOS."""
    desktop = get_desktop_dir()
    shortcut_path = desktop / "RayRabbit Ecosystem"
    if shortcut_path.exists() or shortcut_path.is_symlink():
        shortcut_path.unlink(missing_ok=True)
    shortcut_path.symlink_to(target_app.resolve())
    return shortcut_path

def setup_desktop_shortcut(project_root: Path = None) -> Path:
    """Detecta la plataforma y crea el acceso directo corporativo en el Escritorio."""
    if project_root is None:
        project_root = Path.cwd()
        
    system = platform.system()
    icon_ico = project_root / "rayrabbit" / "resources" / "icons" / "rayrabbit-ecosystem.ico"
    icon_png = project_root / "rayrabbit" / "resources" / "icons" / "rayrabbit-ecosystem.png"
    
    # 1. Buscar binario compilado preferente en dist/
    compiled_exe_win = project_root / "dist" / "rayrabbit-ecosystem.exe"
    compiled_bin_unix = project_root / "dist" / "rayrabbit-ecosystem"
    compiled_app_mac = project_root / "dist" / "RayRabbit Ecosystem.app"
    
    if system == "Windows":
        if compiled_exe_win.exists():
            created = create_windows_shortcut(compiled_exe_win, icon_ico, project_root, arguments="")
        else:
            python_exe = project_root / "venv" / "Scripts" / "python.exe"
            created = create_windows_shortcut(python_exe, icon_ico, project_root, arguments="run_local_rayrabbit_cluster.py")
    elif system == "Darwin":
        target = compiled_app_mac if compiled_app_mac.exists() else compiled_bin_unix
        created = create_macos_shortcut(target)
    else:
        if compiled_bin_unix.exists():
            created = create_linux_shortcut(compiled_bin_unix, icon_png, project_root, arguments="")
        else:
            python_bin = project_root / "venv" / "bin" / "python"
            created = create_linux_shortcut(python_bin, icon_png, project_root, arguments="run_local_rayrabbit_cluster.py")
        
    print(f">> Acceso directo de escritorio creado con éxito: {created}")
    return created

if __name__ == "__main__":
    setup_desktop_shortcut()
