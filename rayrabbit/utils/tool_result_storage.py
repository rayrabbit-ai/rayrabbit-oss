"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Módulo de Persistencia en Disco de Resultados Masivos (Tool Result Storage).
Patrón de Persistencia de 3 Capas de RayRabbit Agent.
Evita el desbordamiento de la ventana de contexto del LLM volcando salidas > 50k chars a disco.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger("rayrabbit.utils.tool_result_storage")

DEFAULT_MAX_CHARS = 50_000
DEFAULT_PREVIEW_SIZE = 2_000

PERSISTED_OUTPUT_TAG = "<persisted-output>"
PERSISTED_OUTPUT_CLOSING_TAG = "</persisted-output>"

def _get_storage_dir() -> Path:
    storage_dir = Path.cwd() / ".rayrabbit_data" / "tmp" / "tool_results"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir

def generate_preview(content: str, max_chars: int = DEFAULT_PREVIEW_SIZE) -> Tuple[str, bool]:
    """Genera una vista previa del contenido truncando al último salto de línea dentro de max_chars."""
    if len(content) <= max_chars:
        return content, False
    truncated = content[:max_chars]
    last_nl = truncated.rfind("\n")
    if last_nl > max_chars // 2:
        truncated = truncated[:last_nl + 1]
    return truncated, True

def maybe_persist_tool_result(
    content: str,
    tool_name: str,
    max_chars: int = DEFAULT_MAX_CHARS
) -> str:
    """
    Evalúa si la respuesta de una herramienta supera el presupuesto máximo de caracteres.
    Si lo supera:
    - Escribe el resultado completo en un archivo `.txt` local en `.rayrabbit_data/tmp/tool_results/`.
    - Sustituye la salida por un bloque con la etiqueta `<persisted-output>`, vista previa y ruta.
    """
    if not isinstance(content, str) or len(content) <= max_chars:
        return content

    storage_dir = _get_storage_dir()
    call_id = uuid.uuid4().hex[:8]
    clean_tool_name = "".join([c for c in tool_name if c.isalnum() or c == "_"])
    file_name = f"{clean_tool_name}_{call_id}.txt"
    file_path = storage_dir / file_name

    try:
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Persistido resultado masivo de herramienta '{tool_name}' ({len(content)} chars) en {file_path}")
    except Exception as e:
        logger.error(f"Fallo al escribir persistencia en disco de herramienta '{tool_name}': {e}")
        # Fallback a truncamiento inline si falla el disco
        preview, _ = generate_preview(content, DEFAULT_PREVIEW_SIZE)
        return f"{preview}\n\n[Truncado: La salida superaba los {len(content)} caracteres y no se pudo escribir en disco.]"

    preview, has_more = generate_preview(content, DEFAULT_PREVIEW_SIZE)
    original_size = len(content)
    size_kb = original_size / 1024.0

    msg = f"{PERSISTED_OUTPUT_TAG}\n"
    msg += f"Esta salida de herramienta era demasiado grande ({original_size:,} caracteres, {size_kb:.1f} KB).\n"
    msg += f"Respuesta completa guardada en disco: {file_path.absolute()}\n"
    msg += "Puedes utilizar la herramienta read_file con offset y limit para acceder a secciones específicas de este resultado.\n\n"
    msg += f"Vista previa (primeros {len(preview)} caracteres):\n"
    msg += preview
    if has_more:
        msg += "\n..."
    msg += f"\n{PERSISTED_OUTPUT_CLOSING_TAG}"

    return msg
