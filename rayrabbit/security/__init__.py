# -*- coding: utf-8 -*-
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
MAESTRO Security Orchestrator
Conceptual Framework: Ken Huang (Cloud Security Alliance, 2025)
Production Implementation: RayRabbit Labs
"""
"""Módulo de inicialización de seguridad para RayRabbit OSS.

Expone de manera limpia las clases y tipos requeridos por la infraestructura,
realizando la transición quirúrgica hacia las implementaciones reales.
"""

from .auditing import AuditEvent, AuditLevel, AuditManager, EventCategory
from .maestro import MAESTROSecurity
from .standalone_security import StandaloneKeyStore as FileKeyStore


from .encryption_defs import EncryptionAlgorithm, KeyType, EncryptionKey


__all__ = [
    "MAESTROSecurity",
    "AuditManager",
    "FileKeyStore",
    "AuditLevel",
    "EventCategory",
    "AuditEvent",
    "EncryptionAlgorithm",
    "KeyType",
    "EncryptionKey",
]
