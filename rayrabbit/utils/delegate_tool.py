"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Módulo de Delegación Progresiva de Tareas, Subagentes y Gating de Etapas (Delegate Tool & Stage Gating).
Arquitectura de delegación de RayRabbit Agent adaptada a la infraestructura L3 de RayRabbit.

Provee:
1. ProgressiveStageDelegator: Divulgación progresiva de herramientas (Stage-Gating) vía BM25.
2. DelegateTaskManager: Ejecución paralela y secuencial de subtareas agénticas con telemetría de eventos.
3. Detección automática de etapas en lenguaje natural para metas multi-agente (CLI y A2UI).
"""

from __future__ import annotations

import re
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Set, Callable
from pathlib import Path

from rayrabbit.utils.tool_search_engine import BM25ToolIndex, match_top_k_tools

logger = logging.getLogger("rayrabbit.utils.delegate_tool")

# Herramientas de bajo nivel o sistema que nunca deben delegarse a subagentes de hojas
DELEGATE_BLOCKED_TOOLS = frozenset({
    "delegate_task",
    "clarify",
    "cronjob",
    "execute_code"
})


@dataclass
class StageGatingPlan:
    """Representa el plan de ejecución y gating de etapas para una meta multi-agente."""
    total_stages: int
    current_stage_index: int
    active_stage_text: str
    is_completed: bool
    pending_stages: List[str]
    executed_tools: List[str]
    active_tool_name: Optional[str] = None


@dataclass
class SubtaskResult:
    """Resultado estructurado de la ejecución de una subtarea delegada."""
    task_index: int
    goal: str
    status: str  # "completed" | "error" | "timeout"
    summary: Optional[str] = None
    error: Optional[str] = None
    tool_name: Optional[str] = None
    duration_seconds: float = 0.0
    output_tail: List[Dict[str, Any]] = field(default_factory=list)


class ProgressiveStageDelegator:
    """
    Gestiona la divulgación progresiva de herramientas y la delegación por etapas.
    Descompone metas complejas en cláusulas y determina la etapa activa
    utilizando BM25 contra el catálogo de herramientas vivas de RayRabbit Hub.
    """

    def __init__(self, tools_list: List[Dict[str, Any]]):
        self.tools_list = tools_list
        self.cognitive_tools = [
            t for t in tools_list
            if any(k in (t.get("category", "") or "") for k in ("cognitive", "framework"))
        ]
        self.executable_tools = [
            t for t in tools_list
            if not any(k in (t.get("category", "") or "") for k in ("memory", "sovereign_memory_node"))
        ]

    def decompose_goal_into_stages(self, user_goal: str) -> List[str]:
        """Descompone un objetivo de usuario en cláusulas o etapas secuenciales."""
        if not user_goal:
            return []
        
        # Si contiene prefijo con dos puntos ':' (ej. "Pipeline multi-etapa: 1. ...")
        target_text = user_goal
        if ":" in user_goal:
            parts = user_goal.split(":", 1)
            prefix = parts[0].strip()
            rest = parts[1].strip()
            # Si el resto contiene lista numerada o el prefijo es un título introductorio genérico
            if rest and (re.search(r'\b1[\.\)]\s*', rest) or re.search(r'^\s*(?:pipeline|flujo|proceso|objetivo|meta|caso)\b', prefix, re.IGNORECASE)):
                target_text = rest
            else:
                target_text = user_goal

        raw_parts = re.split(
            r'\r?\n+|\b\d+[\.\)]\s*|;\s*|,\s*|\.(?:\s+|$)|->|\s+-\s+|\|\s*|\b(?:y\s+)?luego\b|\bdespu[eé]s\b|\bposteriormente\b|\bacto seguido\b|\ba continuaci[oó]n\b|\bseguidamente\b|\bfinalmente\b|\bpor [uú]ltimo\b|\b(?:y|e)\s+(?=(?:[a-zA-Z0-9_-]+\s+(?:en|con|para|de)|etapa|fase|paso|verific|analiz|revis|utiliz|ejecut|activ))',
            target_text,
            flags=re.IGNORECASE
        )
        stages = [p.strip().rstrip(":") for p in raw_parts if len(p.strip().rstrip(":")) > 3]
        return stages if stages else [user_goal]

    def resolve_stage_plan(self, user_goal: str, executed_tools: List[str]) -> StageGatingPlan:
        """
        Determina la etapa activa y si el plan ha sido completado,
        emparejando cada cláusula de la meta con herramientas ejecutables (dominio y cognitivas) vía BM25.
        """
        stages = self.decompose_goal_into_stages(user_goal)
        executed_set = set(executed_tools or [])
        
        target_pool = self.executable_tools if self.executable_tools else self.tools_list
        if not stages or not target_pool:
            return StageGatingPlan(
                total_stages=max(len(stages), 1),
                current_stage_index=0,
                active_stage_text=user_goal,
                is_completed=bool(executed_set),
                pending_stages=stages,
                executed_tools=executed_tools
            )

        indexer = BM25ToolIndex(target_pool)
        
        # 1. Evaluar qué herramientas coinciden con cada etapa
        stage_tool_mapping: List[Tuple[str, Optional[str]]] = []
        for stage in stages:
            scores = indexer.score(stage)
            matched = None
            if any(s > 0 for s in scores):
                best_idx = max(range(len(scores)), key=lambda i: scores[i])
                if scores[best_idx] > 0.3:
                    matched = target_pool[best_idx].get("name")
            stage_tool_mapping.append((stage, matched))

        # Determinar la lista ordenada de herramientas requeridas por las etapas
        required_tools: List[str] = []
        for stage, matched in stage_tool_mapping:
            if matched and matched not in required_tools:
                required_tools.append(matched)

        # Si ninguna etapa tuvo match directo > 0.3, evaluar el objetivo completo (goal global)
        if not required_tools:
            overall_scores = indexer.score(user_goal)
            if any(s > 0 for s in overall_scores):
                best_idx = max(range(len(overall_scores)), key=lambda i: overall_scores[i])
                if overall_scores[best_idx] > 0:
                    required_tools.append(target_pool[best_idx].get("name"))

        # Evaluar herramientas pendientes
        pending_tools = [t for t in required_tools if t not in executed_set]
        
        is_completed = (len(pending_tools) == 0 and len(executed_set) > 0)
        active_tool_name = pending_tools[0] if pending_tools else None

        active_stage_text = ""
        active_stage_idx = 0
        if active_tool_name:
            for idx, (st_text, m_tool) in enumerate(stage_tool_mapping):
                if m_tool == active_tool_name:
                    active_stage_text = st_text
                    active_stage_idx = idx
                    break
            if not active_stage_text:
                active_stage_text = stages[0] if stages else user_goal
        else:
            active_stage_idx = len(stages)
            active_stage_text = "Completado" if is_completed else (stages[0] if stages else user_goal)

        return StageGatingPlan(
            total_stages=max(len(required_tools), 1),
            current_stage_index=len(required_tools) - len(pending_tools),
            active_stage_text=active_stage_text,
            is_completed=is_completed,
            pending_stages=pending_tools,
            executed_tools=executed_tools,
            active_tool_name=active_tool_name
        )

    def get_scoped_tools_for_active_stage(
        self,
        user_goal: str,
        executed_tools: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retorna ÚNICAMENTE las herramientas relevantes a la etapa activa (Progressive Tool Disclosure).
        Excluye herramientas de etapas futuras y herramientas ya ejecutadas hasta que la etapa activa concluya.
        """
        plan = self.resolve_stage_plan(user_goal, executed_tools)
        memory_tools = [
            t for t in self.tools_list
            if any(k in (t.get("category", "") or "") for k in ("memory", "sovereign_memory_node"))
        ]

        if plan.is_completed:
            return memory_tools

        executed_set = set(executed_tools or [])
        future_stage_tools = set(plan.pending_stages[1:]) if len(plan.pending_stages) > 1 else set()
        unexecuted_tools = [
            t for t in self.tools_list
            if t.get("name") not in executed_set and t.get("name") not in future_stage_tools
        ]
        query = plan.active_stage_text or user_goal
        matched_tools = match_top_k_tools(
            prompt=query,
            tools_list=unexecuted_tools,
            top_k=top_k,
            agent_role="universal"
        )
        # Asegurar que la herramienta activa si existe esté en los candidatos
        if plan.active_tool_name:
            active_tool_obj = next((t for t in self.tools_list if t.get("name") == plan.active_tool_name), None)
            if active_tool_obj and active_tool_obj not in matched_tools and active_tool_obj.get("name") not in executed_set:
                matched_tools.insert(0, active_tool_obj)
                
        return matched_tools


class DelegateTaskManager:
    """
    Gestor de ejecución de subtareas delegadas a frameworks cognitivos en RayRabbit.
    Coordina la invocación de herramientas, captura de trazas y generación de resúmenes.
    """

    def __init__(self, execute_tool_fn: Callable[[str, Dict[str, Any]], Any]):
        self.execute_tool_fn = execute_tool_fn

    async def execute_subtask(
        self,
        task_index: int,
        goal: str,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> SubtaskResult:
        """Ejecuta una subtarea invocando la herramienta MCP correspondiente vía el Hub."""
        start_time = time.monotonic()
        logger.info(f"🚀 [DELEGATE] Ejecutando subtarea {task_index + 1}: '{goal}' vía '{tool_name}'...")
        try:
            res = await self.execute_tool_fn(tool_name, tool_args)
            duration = round(time.monotonic() - start_time, 2)
            summary = str(res)
            return SubtaskResult(
                task_index=task_index,
                goal=goal,
                status="completed",
                summary=summary,
                tool_name=tool_name,
                duration_seconds=duration,
                output_tail=[{"tool": tool_name, "preview": summary[:300], "is_error": False}]
            )
        except Exception as exc:
            duration = round(time.monotonic() - start_time, 2)
            logger.error(f"❌ [DELEGATE] Error en subtarea {task_index + 1}: {exc}")
            return SubtaskResult(
                task_index=task_index,
                goal=goal,
                status="error",
                error=str(exc),
                tool_name=tool_name,
                duration_seconds=duration,
                output_tail=[{"tool": tool_name, "preview": str(exc)[:300], "is_error": True}]
            )
