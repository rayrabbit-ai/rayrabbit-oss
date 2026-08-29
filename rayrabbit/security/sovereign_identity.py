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
import os
import httpx
import asyncio
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from ..core.runtime_context import RuntimeContext
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SovereignIdentity:
    """
    Gestiona la identidad auto-soberana del agente.
    Permite el arranque autónomo, generación de claves y registro en el ecosistema.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.identity_dir = RuntimeContext.get_identity_dir()
        self.private_key_path = self.identity_dir / f"{agent_id}_private.pem"
        self.public_key_path = self.identity_dir / f"{agent_id}_public.pem"

    def ensure_identity(self) -> str:
        """
        Asegura que el agente tenga un par de llaves. 
        Si no existen, las genera automáticamente.
        """
        if not self.private_key_path.exists():
            logger.info(f"Generando nueva identidad soberana para: {self.agent_id}")
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Guardar Privada
            with open(self.private_key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Guardar Pública
            with open(self.public_key_path, "wb") as f:
                f.write(private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            logger.info(f"Identidad generada en {self.identity_dir}")
        
        with open(self.public_key_path, "r") as f:
            return f.read()

    async def register_online(self, hub_url: str):
        """
        Registra la clave pública en el Hub de interoperabilidad.
        Esto habilita que otros agentes puedan verificar JWS sin compartir archivos.
        """
        public_key_pem = self.ensure_identity()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{hub_url}/api/security/register",
                    json={
                        "agent_id": self.agent_id,
                        "public_key_pem": public_key_pem
                    }
                )
                if response.status_code == 200:
                    logger.info(f"✅ Identidad registrada exitosamente en el Hub: {hub_url}")
                else:
                    logger.warning(f"⚠️ El Hub respondió con error al registrar identidad: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error conectando con el Hub para registro: {e}")
