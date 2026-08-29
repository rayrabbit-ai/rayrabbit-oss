"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from ..utils.logger import get_logger

class AgentsMdParser:
    """
    Parser para el estándar NODOS.md de la AAIF.
    Permite extraer metadata estructurada de archivos Markdown para descubrimiento dinámico.
    """
    
    def __init__(self):
        self.logger = get_logger("AgentsMdParser")

    def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        Parsea el contenido de un NODOS.md y retorna una lista de agentes estructurados.
        Soporta múltiples agentes definidos por secciones H2 o H1 con su propia metadata.
        """
        agents_found = []
        
        # Dividir por secciones que parezcan definir un nuevo agente (H1 o H2)
        sections = re.split(r'\n(?=#|##)', "\n" + content)
        
        for section in sections:
            if not section.strip(): continue
            
            metadata = {
                "name": "Unknown Agent",
                "id": None,
                "protocols": [],
                "capabilities": [],
                "endpoints": {},
                "description": ""
            }
            
            # 1. Extraer Nombre (Primer encabezado de la sección)
            name_match = re.search(r'^[#]+\s+(.+)$', section, re.MULTILINE)
            if name_match:
                metadata["name"] = name_match.group(1).strip()
            
            # 2. Extraer ID
            id_match = re.search(r'-\s+\*?\*?ID\*?\*?:\s*[`"]?([\w\-_]+)[`"]?', section, re.IGNORECASE)
            if id_match:
                metadata["id"] = id_match.group(1).strip()
            else:
                continue # Si no hay ID, no es una definición de agente válida para nosotros
            
            # 3. Extraer Protocolos (manejando ["a", "b"] o a, b)
            protocols_match = re.search(r'-\s+\*?\*?Protocols\*?\*?:\s*(.+)', section, re.IGNORECASE)
            if protocols_match:
                raw_p = protocols_match.group(1).strip()
                # Limpiar corchetes y comillas
                raw_p = re.sub(r'[\[\]"\'` ]', '', raw_p)
                metadata["protocols"] = [p.lower() for p in raw_p.split(',') if p]
                
            # 4. Extraer Capacidades
            caps_match = re.search(r'-\s+\*?\*?Capabilities\*?\*?:\s*(.+)', section, re.IGNORECASE)
            if caps_match:
                raw_c = caps_match.group(1).strip()
                raw_c = re.sub(r'[\[\]"\'`]', '', raw_c) # No quitamos espacios aquí por si son frases
                metadata["capabilities"] = [c.strip() for c in raw_c.split(',') if c]

            # 5. Extraer Endpoints
            # Busca patrones tipo "- a2a: http://..."
            # Agregamos soporte para urls locales y ws
            endpoint_matches = re.finditer(r'-\s+\*?\*?([\w\-]+)\*?\*?:\s*[`"]?((?:https?|ws?s?)://[^\s`"]+)[`"]?', section, re.IGNORECASE)
            for match in endpoint_matches:
                protocol = match.group(1).lower()
                url = match.group(2).strip()
                if protocol not in ["id", "protocols", "capabilities", "description"]:
                   metadata["endpoints"][protocol] = url

            # 6. Descripción
            # Tomar todo el texto después de - Description: o bajo el encabezado Description
            desc_match = re.search(r'-\s+Description:\s*(.+)', section, re.IGNORECASE | re.MULTILINE)
            if desc_match:
                metadata["description"] = desc_match.group(1).strip()
            
            agents_found.append(metadata)
            
        return agents_found

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Lee y parsea un archivo NODOS.md, retornando una lista de agentes."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return self.parse(f.read())
        except Exception as e:
            self.logger.error(f"Error parseando {file_path}: {e}")
            return []
