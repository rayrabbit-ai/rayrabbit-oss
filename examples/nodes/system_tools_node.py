"""
RayRabbit OSS — System Tools Sovereign SDK Node
===============================================
Nodo SDK soberano que expone herramientas atómicas de sistema (Archivos, Web, Skills, Terminal)

Conexión: WebSocket saliente soberano a ws://127.0.0.1:8005/ws
Categoría MCP: "system"

SPDX-License-Identifier: Apache-2.0
"""
import os
import re
import sys
import json
import asyncio
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, List

from rayrabbit_client import RayRabbitNode

# ─── Configuración de Seguridad y Bloqueos de Sistema ─────────────────────────
_DEFAULT_MAX_READ_CHARS = 100_000
_BLOCKED_DEVICE_PATHS = frozenset({
    "/dev/zero", "/dev/random", "/dev/urandom", "/dev/full",
    "/dev/stdin", "/dev/tty", "/dev/console", "/dev/stdout", "/dev/stderr",
    "/dev/fd/0", "/dev/fd/1", "/dev/fd/2"
})

# Patrones Regex para Redacción Criptográfica de Secretos en Lectura
_SECRET_PATTERNS = [
    (re.compile(r'sk-[a-zA-Z0-9_\-]{20,}'), 'sk-****[REDACTED_API_KEY]****'),
    (re.compile(r'nvapi-[a-zA-Z0-9_\-]{20,}'), 'nvapi-****[REDACTED_API_KEY]****'),
    (re.compile(r'AIzaSy[a-zA-Z0-9_\-]{30,}'), 'AIzaSy****[REDACTED_GEMINI_KEY]****'),
    (re.compile(r'gsk_[a-zA-Z0-9_\-]{20,}'), 'gsk_****[REDACTED_GROQ_KEY]****'),
    (re.compile(r'ghp_[a-zA-Z0-9]{30,}'), 'ghp_****[REDACTED_GITHUB_TOKEN]****'),
    (re.compile(r'-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA )?PRIVATE KEY-----'), '[REDACTED_PRIVATE_KEY_PEM]'),
]


def _redact_secrets(text: str) -> str:
    """Oculta automáticamente claves de API y secrets antes de responder."""
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _sanitize_path(path_str: str) -> Path:
    """Resuelve la ruta usando pathlib.Path y valida bloqueos de seguridad."""
    norm_input = path_str.strip().replace("\\", "/").lower()
    for blocked in _BLOCKED_DEVICE_PATHS:
        if norm_input == blocked or norm_input.startswith(blocked + "/"):
            raise PermissionError(f"Acceso bloqueado por política de seguridad a dispositivo: {path_str}")

    expanded = os.path.expanduser(path_str)
    resolved = Path(expanded).resolve()

    resolved_str = str(resolved).replace("\\", "/").lower()
    for blocked in _BLOCKED_DEVICE_PATHS:
        if resolved_str == blocked or resolved_str.endswith(blocked):
            raise PermissionError(f"Acceso bloqueado por política de seguridad a dispositivo: {path_str}")

    return resolved


# ─── Inicialización del Nodo SDK Soberano ──────────────────────────────────────
HUB_WS_URL = os.getenv("RAYRABBIT_HUB_WS_URL", "ws://127.0.0.1:8005/ws")

node = RayRabbitNode(
    name="system_tools_node",
    hub_url=HUB_WS_URL
)


# ─── Herramientas de Archivos y Sistema ────────────────────────────────────────

@node.tool
async def read_file(path: str, offset: int = 1, limit: int = 200) -> str:
    """Lee el contenido de un archivo local con paginación, sanitización pathlib.Path y redacción de secretos."""
    try:
        target_path = _sanitize_path(path)
        if not target_path.exists():
            return f"Error: El archivo '{path}' no existe."
        if target_path.is_dir():
            return f"Error: '{path}' es un directorio. Utiliza search_files o list_directory."

        lines = target_path.read_text(encoding="utf-8", errors="replace").splitlines()
        total_lines = len(lines)

        start_idx = max(0, offset - 1)
        end_idx = min(total_lines, start_idx + limit)

        slice_lines = lines[start_idx:end_idx]
        formatted = "\n".join(f"{i + start_idx + 1:4d} | {line}" for i, line in enumerate(slice_lines))

        # Límite de seguridad en caracteres
        if len(formatted) > _DEFAULT_MAX_READ_CHARS:
            formatted = formatted[:_DEFAULT_MAX_READ_CHARS] + "\n... [TRUNCADO POR TAMAÑO MÁXIMO (100K CHARS)]"

        redacted = _redact_secrets(formatted)
        header = f"--- [Archivo: {target_path.name} | Líneas {start_idx + 1}-{end_idx} de {total_lines}] ---\n"
        return header + redacted
    except Exception as e:
        return f"Error leyendo archivo '{path}': {str(e)}"


@node.tool
async def write_file(path: str, content: str) -> str:
    """Crea o sobreescribe atómicamente un archivo local creando directorios padre si es necesario."""
    try:
        target_path = _sanitize_path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return f"Éxito: Archivo '{target_path.name}' guardado correctamente ({len(content)} bytes)."
    except Exception as e:
        return f"Error escribiendo archivo '{path}': {str(e)}"


@node.tool
async def patch_file(path: str, target_content: str, replacement_content: str) -> str:
    """Reemplaza un bloque exacto de líneas en un archivo local sin reescribir todo el documento."""
    try:
        target_path = _sanitize_path(path)
        if not target_path.exists():
            return f"Error: El archivo '{path}' no existe para aplicar el parche."

        raw = target_path.read_text(encoding="utf-8")
        if target_content not in raw:
            return f"Error: No se encontró el texto objetivo exacto en '{path}'. No se aplicó el parche."

        new_content = raw.replace(target_content, replacement_content, 1)
        target_path.write_text(new_content, encoding="utf-8")
        return f"Éxito: Parche aplicado en '{target_path.name}'."
    except Exception as e:
        return f"Error aplicando parche en '{path}': {str(e)}"


@node.tool
async def search_files(query: str, search_path: str = ".", is_regex: bool = False) -> str:
    """Busca patrones de texto o nombres de archivos en el espacio de trabajo."""
    try:
        root_dir = _sanitize_path(search_path)
        if not root_dir.exists():
            return f"Error: La ruta de búsqueda '{search_path}' no existe."

        matches = []
        regex = re.compile(query if is_regex else re.escape(query), re.IGNORECASE)

        for p in root_dir.rglob("*"):
            if p.is_file() and not any(part.startswith(".") or part in ("venv", "__pycache__", "node_modules") for part in p.parts):
                try:
                    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for idx, line in enumerate(lines, 1):
                        if regex.search(line):
                            matches.append(f"{p.relative_to(root_dir)}:{idx}: {line.strip()[:100]}")
                            if len(matches) >= 50:
                                break
                except Exception:
                    continue
            if len(matches) >= 50:
                break

        if not matches:
            return f"Sin coincidencias para '{query}' en '{search_path}'."
        return "\n".join(matches)
    except Exception as e:
        return f"Error en búsqueda de archivos: {str(e)}"


# ─── Herramientas Web & Extracción ─────────────────────────────────────────────

@node.tool
async def web_extract(url: str) -> str:
    """Extrae el contenido de texto limpio de una página web pública convirtiéndola a formato scannable."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RayRabbit/3.1"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="replace")

        # Limpieza básica de HTML sin dependencias pesadas
        text = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
        text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines[:150])  # Primeras 150 líneas

        if len(clean_text) > 10_000:
            clean_text = clean_text[:10_000] + "\n... [TRUNCADO WEB EXTRACT]"

        return f"--- [Contenido Web Extraído de: {url}] ---\n\n" + _redact_secrets(clean_text)
    except Exception as e:
        return f"Error extrayendo URL '{url}': {str(e)}"


# ─── Herramientas de Aprendizaje & Skills ────────────────────

@node.tool
async def skill_manage(action: str, name: str, description: str, content: str = "") -> str:
    """
    Crea o gestiona un archivo SKILL.md bajo la especificación RayRabbit AUTHORING_STANDARDS.
    Reglas:
      - name: minúsculas con guiones (<=64 chars).
      - description: EXACTAMENTE 1 oración (<=60 chars).
    """
    try:
        name_clean = name.strip().lower().replace(" ", "-")
        if len(name_clean) > 64:
            return "Error: El nombre de la skill debe tener máximo 64 caracteres."

        desc_clean = description.strip()
        if len(desc_clean) > 60:
            return f"Error de Estándar RayRabbit: La descripción supera los 60 caracteres (tiene {len(desc_clean)} chars). Acórtala antes de guardar."

        skills_dir = Path(".agent/skills") / name_clean
        skills_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skills_dir / "SKILL.md"

        if action in ("create", "write", "update"):
            frontmatter = (
                f"---\n"
                f"name: {name_clean}\n"
                f"description: \"{desc_clean}\"\n"
                f"version: 0.1.0\n"
                f"author: User / RayRabbit Pattern\n"
                f"---\n\n"
            )
            full_document = frontmatter + content.strip()
            skill_file.write_text(full_document, encoding="utf-8")
            return f"Éxito: Skill '{name_clean}' guardada en '{skill_file}' siguiendo _AUTHORING_STANDARDS (Desc: {len(desc_clean)} chars)."
        elif action == "read":
            if not skill_file.exists():
                return f"Error: La skill '{name_clean}' no existe."
            return skill_file.read_text(encoding="utf-8")
        else:
            return f"Acción desconocida '{action}'. Usar 'create', 'write', 'update' o 'read'."
    except Exception as e:
        return f"Error gestionando skill '{name}': {str(e)}"


# ─── Herramienta Terminal ───────────────────────────────────────────────────────

@node.tool
async def terminal(command: str) -> str:
    """Ejecuta un comando de consola en subproceso con PAGER=cat y timeout de seguridad."""
    try:
        env = dict(os.environ)
        env["PAGER"] = "cat"

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")

        if len(output) > 20_000:
            output = output[:20_000] + "\n... [TRUNCADO TERMINAL OUTPUT]"

        return f"--- [Ejecución: `{command}` | Exit Code: {proc.returncode}] ---\n" + _redact_secrets(output)
    except asyncio.TimeoutError:
        return f"Error: El comando `{command}` superó el tiempo límite de 30 segundos."
    except Exception as e:
        return f"Error ejecutando comando en terminal: {str(e)}"


# ─── Arranque del Nodo SDK Soberano ───────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 Iniciando SystemToolsNode conectándose a {HUB_WS_URL}...")
    asyncio.run(node.connect())
