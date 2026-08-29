"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
from abc import ABC, abstractmethod
import os
import inspect # Importar inspect
from dotenv import load_dotenv
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .framework import RayRabbitFramework

class BaseProject(ABC):
    """
    Clase Base Abstracta que define el contrato para todos los proyectos ejecutables
    dentro de la infraestructura RayRabbit.
    """

    def __init__(self, project_name: str) -> None:
        """
        Inicializa el proyecto.

        Args:
            project_name (str): El nombre del directorio del proyecto.
        """
        self.project_name = project_name
        self.framework: Optional["RayRabbitFramework"] = None

    def set_framework(self, framework: "RayRabbitFramework") -> None:
        """
        Inyecta la instancia principal del framework en el proyecto.
        """
        self.framework = framework

    @abstractmethod
    async def execute(self, payload: dict) -> Any:
        """
        El punto de entrada principal para la lógica del proyecto.
        """
        pass

    def get_oauth_handler(self) -> Optional[Any]:
        """
        Método opcional para obtener un manejador de autenticación OAuth 2.0.

        Si un proyecto soporta un flujo de OAuth para su integración, debe sobrescribir
        este método para devolver una instancia de un manejador compatible (ej. OAuth2Handler).
        El servidor API genérico utilizará este manejador para orquestar el flujo de login
        y callback de forma agnóstica.

        Returns:
            Optional[Any]: Una instancia de un manejador de OAuth, o None si el proyecto
                           no soporta OAuth.
        """
        return None