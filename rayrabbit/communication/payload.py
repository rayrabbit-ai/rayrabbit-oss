"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

SPDX-License-Identifier: AGPL-3.0-only
"""
from typing import Any, Dict, List, Optional, Union
import json


class UniversalPayloadUnwrapper:
    """
    Normalizador Canónico de Capa L3 (AI TCP/IP Envelope Unboxing).
    
    Extrae de forma determinista y recursiva la carga útil semántica limpia
    desde cualquier sobre o contenedor de protocolo (TaskEngine, Google A2A,
    Anthropic MCP, IBM ACP, o frameworks cognitivos heterogéneos) sin acoplamiento.
    """

    @staticmethod
    def extract_result(data: Any, max_depth: int = 8) -> Any:
        """
        Extrae recursivamente la estructura semántica o primitiva de datos.
        """
        if data is None or max_depth <= 0:
            return data
        
        if isinstance(data, (str, int, float, bool)):
            return data
            
        if isinstance(data, dict):
            # 1. Si es un sobre de error
            if "error" in data and len(data) <= 3:
                err = data["error"]
                if isinstance(err, dict) and "message" in err:
                    return f"Error: {err['message']}"
                return f"Error: {err}"
                
            # 2. Desanidar sobre TaskEngine event o envelope general {"payload": ...}
            if "payload" in data and isinstance(data["payload"], (dict, list, str)):
                return UniversalPayloadUnwrapper.extract_result(data["payload"], max_depth - 1)
                
            # 3. Desanidar sobre A2A / JSON-RPC / MCP standard result container {"result": ...}
            if "result" in data and isinstance(data["result"], (dict, list, str, int, float, bool)):
                return UniversalPayloadUnwrapper.extract_result(data["result"], max_depth - 1)
                
            # 4. Desanidar sobre de salida {"output": ...} (LangChain, Agent frameworks)
            if "output" in data and isinstance(data["output"], (dict, list, str, int, float, bool)):
                return UniversalPayloadUnwrapper.extract_result(data["output"], max_depth - 1)
                
            # 5. Desanidar sobre MCP / Message content {"content": ...}
            if "content" in data and data["content"] is not None:
                # Si content es lista de bloques MCP (ej. [{"type": "text", "text": "..."}])
                if isinstance(data["content"], list):
                    texts = []
                    for block in data["content"]:
                        if isinstance(block, dict) and block.get("type") == "text" and "text" in block:
                            texts.append(str(block["text"]))
                        else:
                            unwrapped_b = UniversalPayloadUnwrapper.extract_result(block, max_depth - 1)
                            if unwrapped_b:
                                texts.append(str(unwrapped_b))
                    if texts:
                        return "\n".join(texts)
                elif isinstance(data["content"], (dict, str)):
                    return UniversalPayloadUnwrapper.extract_result(data["content"], max_depth - 1)

            # 6. Desanidar bloque con clave "text"
            if "text" in data and isinstance(data["text"], str) and len(data) <= 3:
                return data["text"]

            # Si es un diccionario de dominio rico con múltiples campos, devolverlo tal cual
            return data

        if isinstance(data, list):
            # Si es una lista de 1 elemento, desempaquetarlo
            if len(data) == 1:
                return UniversalPayloadUnwrapper.extract_result(data[0], max_depth - 1)
            return [UniversalPayloadUnwrapper.extract_result(item, max_depth - 1) for item in data]

        return data

    @staticmethod
    def extract_text(data: Any) -> str:
        """
        Extrae una representación textual limpia en lenguaje natural legible para narrativas UI.
        Evita volcar bloques de JSON crudos al usuario.
        """
        result = UniversalPayloadUnwrapper.extract_result(data)
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if isinstance(result, (int, float, bool)):
            return str(result)
        if isinstance(result, dict):
            # 1. Si contiene claves directas de texto o resumen
            for k in ["summary", "narrative", "message", "description", "details", "text", "output", "result"]:
                if k in result and isinstance(result[k], str) and result[k].strip():
                    return result[k].strip()
            # 2. Si es una entidad de dominio (ej. SAP TM / Logística / Crypto)
            parts = []
            if "pedido_id" in result or "order_id" in result:
                pid = result.get("pedido_id") or result.get("order_id")
                parts.append(f"Pedido: {pid}")
            if "estado" in result or "status" in result:
                st = result.get("estado") or result.get("status")
                parts.append(f"Estado: {st}")
            if "ruta_actual" in result or "route" in result:
                rt = result.get("ruta_actual") or result.get("route")
                parts.append(f"Ruta: {rt}")
            if "carrier" in result or "transportista" in result:
                cr = result.get("carrier") or result.get("transportista")
                parts.append(f"Transportista: {cr}")
            if "prioridad" in result or "priority" in result:
                pr = result.get("prioridad") or result.get("priority")
                parts.append(f"Prioridad: {pr}")
            if "recomendaciones" in result and isinstance(result["recomendaciones"], list):
                recs = ", ".join(str(r) for r in result["recomendaciones"])
                parts.append(f"Recomendaciones: {recs}")
            if parts:
                return " • ".join(parts)
            # 3. Fallback genérico legible
            human_items = [f"{k}: {v}" for k, v in result.items() if not str(k).startswith("_")]
            return " • ".join(human_items) if human_items else ""
        if isinstance(result, list):
            return ", ".join(UniversalPayloadUnwrapper.extract_text(item) for item in result if item)
        return str(result)
