"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
"""
SimpleAgent - Implementación básica de agente para RayRabbit

Proporciona una implementación simple y directa de un agente
para casos de uso básicos y como ejemplo de implementación.
"""

import asyncio
from typing import Dict, Any, Optional, Callable, List, cast

from ..core.agent import Agent
from ..communication.message import Message, MessageType


class SimpleAgent(Agent):
    """
    Implementación simple de un agente RayRabbit con capacidades de auto-respuesta y ejecución de comandos.
    """

    def __init__(self, agent_id: str, name: str, description: str = ""):
        """
        Inicializa el SimpleAgent.
        """
        super().__init__(agent_id, name, description)
        self.auto_responses: Dict[str, str] = {}
        self.commands: Dict[str, Callable[..., Any]] = {}
        self.response_patterns: List[tuple[Callable[..., bool], Callable[..., Any]]] = []
        
        # Sobrescribir o extender la configuración base si es necesario
        self.config.update({
            "auto_respond": True,
            "case_sensitive": False,
            "response_delay": 0.1,
        })

    def add_auto_response(self, trigger: str, response: str) -> None:
        """
        Añade una respuesta automática para un trigger específico.
        """
        key = trigger if self.config.get("case_sensitive") else trigger.lower()
        self.auto_responses[key] = response
        self.logger.info(f"Respuesta automática añadida: '{key}'")

    def add_command(self, command_name: str, command_func: Callable[..., Any]) -> None:
        """
        Añade un comando ejecutable al agente.
        """
        self.commands[command_name.lower()] = command_func
        if command_name not in self.capabilities:
            self.add_capability(command_name)
        self.logger.info(f"Comando '{command_name}' añadido.")

    def add_response_pattern(self, pattern_func: Callable[..., bool], response_func: Callable[..., Any]) -> None:
        """
        Añade un patrón de respuesta personalizado.
        """
        self.response_patterns.append((pattern_func, response_func))
        self.logger.info("Patrón de respuesta personalizado añadido.")

    # --- Sobrescritura de Handlers de Mensajes ---

    async def _handle_request(self, message: Message) -> Optional[Message]:
        """
        Maneja mensajes de tipo REQUEST, aplicando lógica de auto-respuesta y patrones.
        """
        text = message.content.get("text", "") if isinstance(message.content, dict) else ""
        
        # 1. Buscar respuesta automática
        response_text = self._find_auto_response(text)
        if response_text:
            return message.create_response(
                content={"text": response_text, "type": "auto_response"}
            )

        # 2. Buscar patrón personalizado
        for pattern_func, response_func in self.response_patterns:
            if pattern_func(text):
                try:
                    response_content = await self._call_response_func(response_func, message, text)
                    return message.create_response(content=response_content)
                except Exception as e:
                    self.logger.error(f"Error en patrón de respuesta: {e}", exc_info=True)
                    # Continúa para no bloquear por un patrón fallido

        # 3. Si no hay lógica específica, delegar al manejador base
        return await super()._handle_request(message)

    async def _handle_command(self, message: Message) -> Optional[Message]:
        """
        Maneja mensajes de tipo COMMAND, ejecutando funciones registradas.
        """
        if not isinstance(message.content, dict):
            return await super()._handle_command(message)

        command_name = message.content.get("command", "").lower()
        
        if command_name in self.commands:
            args = message.content.get("args", [])
            kwargs = message.content.get("kwargs", {})
            try:
                result = await self._execute_command(command_name, args, kwargs)
                return message.create_response(
                    content={"result": result, "status": "success"}
                )
            except Exception as e:
                self.logger.error(f"Error ejecutando comando '{command_name}': {e}", exc_info=True)
                return message.create_response(
                    content={"error": f"Error ejecutando comando: {e}"},
                    message_type=MessageType.ERROR
                )

        # Si el comando no se encuentra, delega al manejador base (para 'status', 'ping', etc.)
        return await super()._handle_command(message)

    # --- Métodos de Ayuda Internos ---

    def _find_auto_response(self, text: str) -> Optional[str]:
        """Busca una respuesta automática para el texto dado."""
        search_text = text if self.config.get("case_sensitive") else text.lower()
        
        # Búsqueda exacta
        if search_text in self.auto_responses:
            return self.auto_responses[search_text]
        
        # Búsqueda por contención
        for trigger, response in self.auto_responses.items():
            if trigger in search_text:
                return response
        return None

    async def _execute_command(self, command_name: str, args: list, kwargs: dict) -> Any:
        """Ejecuta un comando de forma segura."""
        command_func = self.commands[command_name]
        if asyncio.iscoroutinefunction(command_func):
            return await command_func(*args, **kwargs)
        else:
            # Considerar ejecutar en un executor para no bloquear el loop
            return await asyncio.to_thread(command_func, *args, **kwargs)

    async def _call_response_func(self, response_func: Callable, message: Message, text: str) -> Dict[str, Any]:
        """Llama a una función de respuesta personalizada."""
        if asyncio.iscoroutinefunction(response_func):
            return cast(Dict[str, Any], await response_func(message, text))
        else:
            return cast(Dict[str, Any], await asyncio.to_thread(response_func, message, text))
