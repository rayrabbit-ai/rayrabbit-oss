"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import asyncio
import time
import hashlib
import datetime
import secrets
from enum import Enum
from typing import Callable, Any, Optional, Dict
from ..utils.logger import get_logger

class CoolingState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    COOLING = "cooling"
    FROZEN = "frozen"

class FunctionCooler:
    """
    Implementación avanzada de Circuit Breaker (Function Cooling) con backoff exponencial.
    Protege al sistema de fallos en cascada y agentes saturados.
    """
    
    def __init__(self, 
                 name: str,
                 max_failures: int = 5, 
                 base_cooldown: float = 5.0, 
                 max_cooldown: float = 300.0,
                 audit_manager: Optional[Any] = None):
        self.name = name
        self.state = CoolingState.HEALTHY
        self.failure_count = 0
        self.max_failures = max_failures
        self.base_cooldown = base_cooldown
        self.max_cooldown = max_cooldown
        self.audit_manager = audit_manager
        self.logger = get_logger(f"FunctionCooler_{name}")
        self.last_failure_time: float = 0
        self._lock = asyncio.Lock()

    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """Ejecuta una operación asíncrona envuelta en el circuit breaker."""
        async with self._lock:
            if self.state == CoolingState.FROZEN:
                cooldown_remaining = self._get_current_cooldown() - (time.time() - self.last_failure_time)
                if cooldown_remaining > 0:
                    self.logger.warning(f"Operación bloqueada por cooling state ({self.name}). Quedan {cooldown_remaining:.2f}s")
                    raise RuntimeError(f"Function '{self.name}' is frozen. Cooldown remaining: {cooldown_remaining:.2f}s")
                else:
                    self.logger.info(f"Periodo de cooling finalizado para {self.name}. Intentando recuperación (Half-Open)...")
                    self.state = CoolingState.COOLING

        try:
            result = await operation(*args, **kwargs)
            
            async with self._lock:
                if self.state != CoolingState.HEALTHY:
                    self.logger.info(f"Función {self.name} recuperada exitosamente.")
                    await self._log_audit("RECOVERY_SUCCESS", "SUCCESS")
                
                self.failure_count = 0
                self.state = CoolingState.HEALTHY
            return result

        except Exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                old_state = self.state
                self._transition_state()
                
                if self.state != old_state:
                    self.logger.warning(f"Transición de estado en {self.name}: {old_state.value} -> {self.state.value} debido a: {e}")
                    await self._log_audit("STATE_TRANSITION", "FAILURE", {"error": str(e), "old_state": old_state.value, "new_state": self.state.value})
                
                raise e

    def _transition_state(self):
        """Calcula el nuevo estado basado en el historial de fallos."""
        if self.failure_count >= self.max_failures:
            self.state = CoolingState.FROZEN
        elif self.failure_count > 0:
            self.state = CoolingState.DEGRADED
        else:
            self.state = CoolingState.HEALTHY

    def _get_current_cooldown(self) -> float:
        """Calcula el cooldown usando backoff exponencial."""
        # 2^(failures - max_failures) * base_cooldown
        exponent = max(0, self.failure_count - self.max_failures)
        cooldown = min(self.max_cooldown, self.base_cooldown * (2 ** exponent))
        return cooldown

    async def _log_audit(self, event_type: str, result: str, details: Optional[Dict] = None):
        """Registra el evento en MAESTRO si está disponible."""
        if self.audit_manager:
            from ..security.auditing import AuditLevel, EventCategory
            self.audit_manager.log_event(
                event_type=f"COOLER_{event_type}",
                level=AuditLevel.WARNING if result == "FAILURE" else AuditLevel.INFO,
                category=EventCategory.SYSTEM_CHANGE,
                action="cooling_protection",
                result=result,
                agent_id="resilience_engine",
                details={
                    "cooler_name": self.name,
                    "failure_count": self.failure_count,
                    "current_state": self.state.value,
                    **(details or {})
                }
            )
