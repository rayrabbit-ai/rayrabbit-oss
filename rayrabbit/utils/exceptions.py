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
Excepciones personalizadas para el framework RayRabbit.
"""

class RayRabbitError(Exception):
    """
    Clase base para todas las excepciones personalizadas en el framework RayRabbit.
    """
    pass

class ConfigurationError(RayRabbitError):
    """
    Excepción levantada cuando hay un error en la configuración del framework.
    """
    pass

class PublicKeyNotFound(RayRabbitError):
    """
    Se lanza cuando no se encuentra una clave pública para un destinatario.
    """
    pass

class ProjectNotFound(RayRabbitError):
    """
    Se lanza cuando el ProjectFactory no puede encontrar un proyecto solicitado.
    """
    pass

class ClassNotFound(RayRabbitError):
    """
    Se lanza cuando el ProjectFactory no puede encontrar la clase de proyecto principal.
    """
    pass
