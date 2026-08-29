"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Módulo de Búsqueda Dinámica BM25 de Herramientas (Tool Search Engine).
Patrón de Divulgación Progresiva de RayRabbit Agent.
Permite una selección 100% agnóstica sin listas ni palabras clave hardcodeadas.
"""

import math
import re
import logging
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger("rayrabbit.utils.tool_search_engine")

# Parámetros BM25 estándar
BM25_K1 = 1.5
BM25_B = 0.75

STOPWORDS: Set[str] = {
    "de", "del", "en", "el", "la", "los", "las", "un", "una", "unos", "unas",
    "y", "o", "a", "por", "para", "con", "sin", "sobre", "este", "esta", "estos",
    "estas", "como", "su", "sus", "al", "que", "se", "es", "son",
    "the", "an", "and", "or", "in", "on", "at", "for", "with", "by", "of", "to", "is", "it"
}

class BM25ToolIndex:
    """
    Motor de búsqueda BM25 en memoria para la selección dinámica y agnóstica de herramientas MCP.
    Indexa dinámicamente el nombre, descripción y parámetros de los esquemas vivos de GET /api/mcp/tools.
    """

    def __init__(self, tools_list: List[Dict[str, Any]]):
        self.tools_list = tools_list
        self.doc_count = len(tools_list)
        self.doc_lengths: List[int] = []
        self.doc_tokens: List[List[str]] = []
        self.avg_doc_length: float = 0.0
        self.df: Dict[str, int] = {}
        
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        # Separar snake_case y camelCase en tokens individuales
        text_clean = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
        text_clean = text_clean.replace('_', ' ').replace('-', ' ').replace('/', ' ')
        raw_tokens = re.findall(r'[A-Za-z0-9]+', text_clean.lower())
        # Filtrar stopwords estándar
        tokens = [t for t in raw_tokens if t not in STOPWORDS and len(t) > 1]
        return tokens

    def _extract_searchable_text(self, tool: Dict[str, Any]) -> str:
        name = tool.get("name", "")
        cat = tool.get("category", "") or ""
        desc = tool.get("description", "") or ""
        schema = tool.get("input_schema") or tool.get("inputSchema") or tool.get("parameters") or {}
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        param_names = " ".join(props.keys()) if isinstance(props, dict) else ""
        return f"{name} {name} {cat} {cat} {desc} {param_names}"

    def _build_index(self):
        total_len = 0
        for tool in self.tools_list:
            text = self._extract_searchable_text(tool)
            tokens = self._tokenize(text)
            self.doc_tokens.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len
            
            seen_tokens: Set[str] = set(tokens)
            for t in seen_tokens:
                self.df[t] = self.df.get(t, 0) + 1

        self.avg_doc_length = (total_len / self.doc_count) if self.doc_count > 0 else 1.0

    def _idf(self, term: str) -> float:
        n_q = self.df.get(term, 0)
        if n_q == 0:
            return 0.0
        # Fórmula Robertson-Spärck Jones IDF
        val = (self.doc_count - n_q + 0.5) / (n_q + 0.5)
        return math.log(1.0 + max(0.0, val))

    def score(self, query: str) -> List[float]:
        query_tokens = self._tokenize(query)
        scores = [0.0] * self.doc_count
        if not query_tokens or self.doc_count == 0:
            return scores

        for idx, doc_toks in enumerate(self.doc_tokens):
            if not doc_toks:
                continue
            doc_len = self.doc_lengths[idx]
            tok_counts: Dict[str, int] = {}
            for t in doc_toks:
                tok_counts[t] = tok_counts.get(t, 0) + 1

            doc_score = 0.0
            for q_term in query_tokens:
                if q_term not in tok_counts:
                    continue
                tf = tok_counts[q_term]
                idf = self._idf(q_term)
                num = tf * (BM25_K1 + 1.0)
                den = tf + BM25_K1 * (1.0 - BM25_B + BM25_B * (doc_len / self.avg_doc_length))
                doc_score += idf * (num / den)
                
            scores[idx] = doc_score

        return scores


def match_top_k_tools(
    prompt: str,
    tools_list: List[Dict[str, Any]],
    top_k: int = 4,
    target_category: Optional[str] = None,
    target_tools: Optional[str] = None,
    agent_role: str = "cognitive_framework"
) -> List[Dict[str, Any]]:
    """
    Selecciona dinámicamente las herramientas más relevantes del catálogo MCP viva.
    - Soporta listas explícitas de herramientas (`target_tools`).
    - Soporta filtrado por categorías separadas por comas (`target_category`).
    - Si no hay parámetros explícitos, ejecuta coincidencia semántica BM25 Top-K.
    - SIEMPRE incluye las herramientas de memoria declarativa para continuidad de estado.
    - Utiliza `agent_role` para restringir topológicamente el acceso a herramientas de forma 100% agnóstica por metadatos (sin nombres hardcodeados).
    """
    if not tools_list:
        return []

    # 1. Parsear filtros explícitos si existen
    allowed_tools = [t.strip().lower() for t in target_tools.split(",")] if target_tools else []
    allowed_cats = [c.strip().lower() for c in target_category.split(",")] if target_category else []

    selected: List[Dict[str, Any]] = []
    memory_tools: List[Dict[str, Any]] = []
    candidate_tools: List[Dict[str, Any]] = []

    for tool in tools_list:
        name = tool.get("name", "")
        cat = (tool.get("category", "") or "general").lower()
        
        if not name:
            continue

        # Taxonomía agnóstica de categorías por metadatos MCP
        is_cognitive = any(keyword in cat for keyword in ("cognitive", "framework"))
        is_memory = any(keyword in cat for keyword in ("memory", "sovereign_memory_node"))
        is_system = any(keyword in cat for keyword in ("system", "system_tools_node", "os", "shell", "terminal"))
        is_hub_native = (cat == "hub_native" or tool.get("agent_id") == "hub_native")

        # ── Control de Visibilidad Topológica por Rol en el Hub ──
        if agent_role == "cognitive_framework":
            # Frameworks cognitivos (LangChain, CrewAI, AutoGen, etc.)
            # Excluir herramientas cognitivas y hub_native para evitar recursión infinita
            if is_cognitive or is_hub_native:
                continue
            # Excluir herramientas de bajo nivel de OS/sistema a menos que target_category las pida explícitamente
            if is_system and not any("system" in ac for ac in allowed_cats):
                continue
        elif agent_role == "system_admin":
            # Agentes de administración de sistema
            if not (is_system or is_memory):
                continue
        # Nota: 'orchestrator', 'universal' y cualquier agente consumidor ven todas las herramientas (dominio, memoria, cognitivo)

        # Separa herramientas de memoria (siempre prioritarias para continuidad de estado)
        if is_memory:
            memory_tools.append(tool)
            continue

        # Filtrado por `target_tools` explícito
        if allowed_tools:
            name_lower = name.lower()
            matched = any(at in name_lower or name_lower in at for at in allowed_tools)
            if not matched:
                t_toks = [tok for tok in name_lower.replace('-', '_').split('_') if len(tok) > 3]
                matched = any(any(tok in at or at in tok for tok in t_toks) for at in allowed_tools)
            
            if matched:
                selected.append(tool)
            continue

        # Filtrado por `target_category` explícito
        if allowed_cats:
            if any(ac in cat or cat in ac for ac in allowed_cats):
                candidate_tools.append(tool)
            continue

        # Si no hay filtro explícito, califica para selección semántica BM25
        candidate_tools.append(tool)

    # Si se solicitaron herramientas explícitamente por nombre y hubo coincidencias, retornar
    if allowed_tools and selected:
        return memory_tools + selected

    # 2. Ejecutar selección dinámica BM25 sobre los candidatos válidos
    if candidate_tools:
        if not prompt or not prompt.strip():
            selected.extend(candidate_tools[:top_k])
        else:
            indexer = BM25ToolIndex(candidate_tools)
            scores = indexer.score(prompt)
            
            # Emparejar herramientas con su puntuación
            scored_candidates = list(zip(scores, candidate_tools))
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            
            # Tomar únicamente las herramientas con puntuación positiva BM25 > 0
            bm25_selected = [t for sc, t in scored_candidates if sc > 0][:top_k]
            
            # Si no hubo coincidencia BM25 positiva pero se solicitó target_category o el agente es orchestrator, devolver los primeros candidatos
            if not bm25_selected and (allowed_cats or agent_role == "orchestrator"):
                bm25_selected = candidate_tools[:top_k]
                
            selected.extend(bm25_selected)

    # Retornar herramientas de memoria + seleccionadas deterministamente por BM25
    return memory_tools + selected
