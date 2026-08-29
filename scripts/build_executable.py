"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.
SPDX-License-Identifier: AGPL-3.0-only
"""
import sys
import platform
import subprocess
from pathlib import Path

def ensure_icons(project_root: Path):
    """Genera y valida los iconos oficiales en todos los formatos requeridos con esquinas redondeadas."""
    icons_dir = project_root / "rayrabbit" / "resources" / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    src_png = project_root / "rayrabbit" / "resources" / "a2ui-dashboard" / "rayrabbit-ai.png"
    if not src_png.exists():
        print(f"Advertencia: No se encontró {src_png}")
        return
        
    try:
        from PIL import Image, ImageDraw
        img = Image.open(src_png).convert("RGBA")
        size = img.size
        
        # Super-muestreo 4x para máscara redondeada anti-aliasing
        scale = 4
        mask_size = (size[0] * scale, size[1] * scale)
        mask = Image.new("L", mask_size, 0)
        draw = ImageDraw.Draw(mask)
        
        radius = int(mask_size[0] * 0.22)  # Radio squircle estándar
        draw.rounded_rectangle([(0, 0), (mask_size[0] - 1, mask_size[1] - 1)], radius=radius, fill=255)
        
        # Redimensionar máscara con LANCZOS
        mask = mask.resize(size, Image.Resampling.LANCZOS)
        img.putalpha(mask)
        
        # Guardar PNG redondeado
        img.save(icons_dir / "rayrabbit-ai.png", format="PNG")
        
        # ICO multi-resolución con transparencia
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(icons_dir / "rayrabbit-ai.ico", format="ICO", sizes=icon_sizes)
        
        # ICNS macOS
        try:
            img.save(icons_dir / "rayrabbit-ai.icns", format="ICNS")
        except Exception:
            pass
            
        print(f">> Iconos redondeados generados en {icons_dir}")
    except ImportError:
        print("Pillow no está instalado en el entorno principal. Utilizando iconos existentes.")

def build():
    """Ejecuta la compilación de RayRabbit Ecosystem y el enlace de escritorio."""
    project_root = Path.cwd()
    print("=" * 60)
    print("  [RayRabbit] COMPILADOR INDUSTRIAL: RAYRABBIT ECOSYSTEM")
    print("=" * 60)
    print(f"Sistema Operativo: {platform.system()} ({platform.machine()})")
    print(f"Directorio Raiz: {project_root}\n")
    
    # 1. Asegurar iconos
    ensure_icons(project_root)
    
    # 2. Generar metadatos Windows PE si aplica
    if platform.system() == "Windows":
        import importlib.util
        win_ver_script = project_root / "scripts" / "windows_version_info.py"
        spec = importlib.util.spec_from_file_location("windows_version_info", win_ver_script)
        win_ver_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(win_ver_mod)
        ver_file = win_ver_mod.generate_version_info(project_root / "scripts" / "file_version_info.txt")
        print(f">> Metadatos Windows VersionInfo generados en: {ver_file}")
        
    # 3. Compilar usando PyInstaller
    spec_file = project_root / "rayrabbit_ecosystem.spec"
    print(f">> Iniciando compilacion con especificacion: {spec_file.name}...")
    
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        str(spec_file)
    ]
    
    try:
        subprocess.run(pyinstaller_cmd, check=True)
        print("\n>> Compilacion finalizada exitosamente en directorio 'dist/'")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Fallo la compilacion de PyInstaller: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error inesperado en compilacion: {e}")
        return False
        
    # 4. Crear acceso directo de escritorio
    try:
        import importlib.util
        shortcut_script = project_root / "scripts" / "create_desktop_shortcut.py"
        spec = importlib.util.spec_from_file_location("create_desktop_shortcut", shortcut_script)
        shortcut_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(shortcut_mod)
        shortcut = shortcut_mod.setup_desktop_shortcut(project_root)
        print(f">> Acceso directo de escritorio creado: {shortcut}")
    except Exception as e:
        print(f">> Nota: No se pudo crear el acceso directo de escritorio: {e}")
        
    print("\n" + "=" * 60)
    print("  [OK] RAYRABBIT ECOSYSTEM COMPILADO Y LISTO")
    print("=" * 60)
    return True

if __name__ == "__main__":
    build()
