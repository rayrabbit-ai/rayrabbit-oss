from __future__ import annotations

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
"""Definiciones criptográficas fundamentales de RayRabbit.

Establece las estructuras de datos y enumeraciones esenciales que
forman la base del subsistema de seguridad de RayRabbit OSS.
"""


from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class EncryptionAlgorithm(Enum):
    """Algoritmos de cifrado soportados por la infraestructura."""

    AES_256_GCM = "AES-256-GCM"
    FERNET = "Fernet"
    RSA_4096 = "RSA-4096"
    BCRYPT = "BCRYPT"


class KeyType(Enum):
    """Tipos de claves criptográficas."""

    SYMMETRIC = "symmetric"
    PRIVATE = "private"
    PUBLIC = "public"
    IDENTITY_SECRET = "identity_secret"


@dataclass(frozen=True)
class EncryptionKey:
    """Modela una clave criptográfica junto con sus metadatos asociados."""

    key_id: str
    key_type: KeyType
    algorithm: EncryptionAlgorithm
    key_data: bytes
    created_at: datetime = datetime.now()
    expires_at: Optional[datetime] = None
    owner_id: Optional[str] = None
    pair_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la clave y sus metadatos a un diccionario."""
        data = asdict(self)
        data["key_type"] = self.key_type.value
        data["algorithm"] = self.algorithm.value
        data["created_at"] = self.created_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        del data["key_data"]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], key_data: bytes) -> EncryptionKey:
        """Crea una instancia de EncryptionKey a partir de un diccionario y sus bytes."""
        expires_at_str = data.get("expires_at")
        return cls(
            key_id=data["key_id"],
            key_type=KeyType(data["key_type"]),
            algorithm=EncryptionAlgorithm(data["algorithm"]),
            key_data=key_data,
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(expires_at_str) if expires_at_str else None,
            owner_id=data.get("owner_id"),
            pair_id=data.get("pair_id"),
            metadata=data.get("metadata"),
        )
