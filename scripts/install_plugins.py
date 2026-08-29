#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RayRabbit Official Plugins Installer CLI
Copyright © 2024-2026 RayRabbit Labs, Inc.

Permite instalar y configurar con un solo comando los plugins oficiales de interoperabilidad
para Google Antigravity, Anthropic Claude Code y OpenAI Codex / Cursor sobre la malla L3.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

# Configurar encoding seguro para Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def install_antigravity(root: Path):
    print("📦 [1/3] Configurando Plugin para Google Antigravity...")
    plugin_dir = root / ".agent" / "plugins" / "antigravity"
    if not plugin_dir.exists():
        print(f"  ❌ Directorio no encontrado: {plugin_dir}")
        return False
    print(f"  ✅ Plugin Antigravity verificado en: {plugin_dir}")
    print(f"  ℹ️ Configuración MCP: {plugin_dir / 'mcp_config.json'}")
    return True

def install_claude(root: Path):
    print("🧠 [2/3] Configurando Plugin para Anthropic Claude Code / Claude Desktop...")
    claude_src = root / "plugins" / "claude-code"
    if not claude_src.exists():
        print(f"  ❌ Directorio origen no encontrado: {claude_src}")
        return False

    # Detectar config de Claude Desktop si existe
    home = Path.home()
    desktop_configs = [
        home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
        home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        home / ".config" / "claude" / "claude_desktop_config.json"
    ]

    target_config = None
    for cfg in desktop_configs:
        if cfg.parent.exists():
            target_config = cfg
            break

    if target_config:
        try:
            existing_data = {}
            if target_config.exists():
                try:
                    existing_data = json.loads(target_config.read_text(encoding="utf-8"))
                except Exception:
                    existing_data = {}
            
            if "mcpServers" not in existing_data:
                existing_data["mcpServers"] = {}
                
            existing_data["mcpServers"]["rayrabbit_mesh"] = {
                "url": "http://127.0.0.1:8005/api/mcp/sse",
                "transport": "sse"
            }
            target_config.write_text(json.dumps(existing_data, indent=2), encoding="utf-8")
            print(f"  ✅ Claude Desktop configurado exitosamente en: {target_config}")
        except Exception as e:
            print(f"  ⚠️ No se pudo escribir en Claude Desktop config: {e}")
    else:
        print("  ℹ️ Claude Desktop no detectado en paths estándar. Configuración local lista en:")
        print(f"     {claude_src / '.mcp.json'}")

    print("  💡 Para Claude Code CLI, ejecuta:")
    print("     claude mcp add rayrabbit http://127.0.0.1:8005/api/mcp/sse")
    return True

def install_codex(root: Path):
    print("⚡ [3/3] Configurando Plugin para OpenAI Codex / Cursor...")
    codex_src = root / "plugins" / "codex"
    if not codex_src.exists():
        print(f"  ❌ Directorio origen no encontrado: {codex_src}")
        return False

    # Configurar .cursor en la raíz si aplica
    cursor_dir = root / ".cursor"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    mcp_target = cursor_dir / "mcp.json"
    
    src_mcp = codex_src / ".cursor" / "mcp.json"
    if src_mcp.exists():
        shutil.copy2(src_mcp, mcp_target)
        print(f"  ✅ Archivo .cursor/mcp.json copiado a: {mcp_target}")

    rules_target = root / ".cursorrules"
    src_rules = codex_src / ".cursorrules"
    if src_rules.exists() and not rules_target.exists():
        shutil.copy2(src_rules, rules_target)
        print(f"  ✅ Reglas .cursorrules configuradas en la raíz del proyecto.")

    return True

def main():
    parser = argparse.ArgumentParser(description="Instalador Oficial de Plugins RayRabbit Sovereign Mesh")
    parser.add_argument("--plugin", choices=["antigravity", "claude", "codex", "all"], default="all",
                        help="Plugin a instalar (antigravity, claude, codex, o all por defecto)")
    parser.add_argument("--all", action="store_true", help="Instala todos los plugins")
    args = parser.parse_args()

    selected = "all" if args.all else args.plugin
    root = get_project_root()
    print("=" * 70)
    print("🐰 RAYRABBIT SOVEREIGN MESH — INSTALADOR DE PLUGINS DE ASISTENTES")
    print(f"Raíz del Proyecto: {root}")
    print("=" * 70)

    if selected in ("antigravity", "all"):
        install_antigravity(root)
        print()

    if selected in ("claude", "all"):
        install_claude(root)
        print()

    if selected in ("codex", "all"):
        install_codex(root)
        print()

    print("=" * 70)
    print("🎉 ¡Configuración de plugins finalizada!")
    print("Inicia el Hub de RayRabbit en puerto :8005 para habilitar el transporte SSE.")
    print("=" * 70)

if __name__ == "__main__":
    main()
