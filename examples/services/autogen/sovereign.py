"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import os
import platform
import httpx
import logging
import time
import base64
from typing import Optional
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

logger = logging.getLogger("sovereign_identity")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class RuntimeContext:
    """Gestión de rutas agnóstica para agentes soberanos."""
    @staticmethod
    def get_rayrabbit_home() -> Path:
        """
        Calcula la ruta base de forma estrictamente local y agnóstica al SO.
        Prioridad: 
        1. Variable de entorno RAYRABBIT_HOME
        2. Carpeta local ./.rayrabbit_data
        """
        env_home = os.getenv("RAYRABBIT_HOME")
        if env_home:
            return Path(env_home).resolve()
        
        # OSS: Siempre local al directorio del servicio para Atomic Sovereignty
        return Path.cwd() / ".rayrabbit_data"

    @classmethod
    def get_identity_dir(cls) -> Path:
        path = cls.get_rayrabbit_home() / "identity"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_agent_data_path(cls, agent_id: str, subfolder: str = "") -> Path:
        path = cls.get_rayrabbit_home() / "agents" / agent_id / subfolder
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def resolve_env_path(cls, filename: str = ".env") -> Path:
        # Prioridad 1: Carpeta local del servicio (CWD)
        local_env = Path.cwd() / filename
        if local_env.exists(): return local_env
        # Prioridad 2: Home de RayRabbit
        return cls.get_rayrabbit_home() / filename

class SovereignIdentity:
    """Implementación de Identidad Soberana con Handshake (PoP)."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        ctx = RuntimeContext()
        self.identity_dir = ctx.get_identity_dir()
        self.private_key_path = self.identity_dir / f"{agent_id}_private.pem"
        self.public_key_path = self.identity_dir / f"{agent_id}_public.pem"

    def ensure_identity(self) -> str:
        if not self.private_key_path.exists():
            logger.info(f"Generando nueva identidad soberana para: {self.agent_id}")
            private_key = rsa.generate_private_key(65537, 2048)
            with open(self.private_key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open(self.public_key_path, "wb") as f:
                f.write(private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
        with open(self.public_key_path, "r") as f:
            return f.read()

    def _create_handshake_signature(self, timestamp: str) -> str:
        """Crea una firma RSA del reto de registro (Proof of Possession)."""
        if not self.private_key_path.exists():
            raise FileNotFoundError("No se encontró la llave privada para firmar el handshake.")
            
        with open(self.private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None)
            
        challenge = f"REG-AUTH:{self.agent_id}:{timestamp}"
        signature = private_key.sign(
            challenge.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    async def _do_register(self, hub_url: str, p2p_endpoint: Optional[str] = None, openapi_url: Optional[str] = None) -> bool:
        """Intenta registrar la identidad en el Hub (una vez)."""
        public_key_pem = self.ensure_identity()
        timestamp = str(int(time.time()))
        signature = self._create_handshake_signature(timestamp)
        
        payload = {
            "agent_id": self.agent_id,
            "public_key_pem": public_key_pem,
            "timestamp": timestamp,
            "signature": signature,
            "p2p_endpoint": p2p_endpoint,
            "openapi_url": openapi_url
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                logger.info(f"🛰️ Enviando Handshake PoP a {hub_url} (ID: {self.agent_id})...")
                response = await client.post(
                    f"{hub_url}/api/security/register",
                    json=payload
                )
                if response.status_code == 200:
                    data = response.json()
                    hub_pk = data.get("hub_public_key")
                    hub_sig_b64 = data.get("hub_signature")
                    hub_timestamp = data.get("hub_timestamp")

                    if hub_pk and hub_sig_b64 and hub_timestamp:
                        # Verificar la firma del Hub (Mutual PoP)
                        try:
                            hub_public_key = serialization.load_pem_public_key(hub_pk.encode('utf-8'))
                            challenge = f"HUB-AUTH:{self.agent_id}:{hub_timestamp}"
                            signature_bytes = base64.b64decode(hub_sig_b64)
                            hub_public_key.verify(
                                signature_bytes,
                                challenge.encode('utf-8'),
                                padding.PSS(
                                    mgf=padding.MGF1(hashes.SHA256()),
                                    salt_length=padding.PSS.MAX_LENGTH
                                ),
                                hashes.SHA256()
                            )
                            # Firma válida
                            hub_pk_path = self.identity_dir / "hub_public.pem"
                            with open(hub_pk_path, "w") as f:
                                f.write(hub_pk)
                            logger.info(f"🤝 Handshake Bidireccional exitoso con {hub_url}")
                            logger.info(f"🛡️ Trust Established: Hub PK validada y guardada en {hub_pk_path}")
                            return True
                        except Exception as e:
                            logger.error(f"❌ Handshake fallido: La firma del Hub no es válida. Posible suplantación. Error: {e}")
                            return False
                    else:
                        logger.warning(f"❌ Hub no retornó credenciales completas para Handshake Bidireccional.")
                        return False
                else:
                    logger.warning(f"❌ Hub rechazó registro (Status {response.status_code}): {response.text}")
                    return False
            except Exception as e:
                logger.warning(f"Fallo de conexión con el Hub en {hub_url} (se reintentará): {e}")
                return False

    async def register_with_backoff(self, hub_url: str, p2p_endpoint: Optional[str] = None, openapi_url: Optional[str] = None, max_retries: int = 5):
        """
        Registro resiliente con Exponential Backoff + Jitter.
        Industry Standard: Kubernetes, Consul, HashiCorp patterns.
        """
        import asyncio
        import random
        
        base_delay = 5.0  # 5 segundos inicial
        
        for attempt in range(max_retries):
            try:
                success = await self._do_register(hub_url, p2p_endpoint=p2p_endpoint, openapi_url=openapi_url)
                if success:
                    logger.info(f"✅ Identidad registrada en {hub_url} con éxito.")
                    return True
            except Exception as e:
                # ... backoff ...
                pass
            
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"↻ Reintento registro {attempt+1}/{max_retries} en {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        logger.warning(f"⚠️ Hub no disponible tras {max_retries} intentos. Operando en modo aislado.")
        return False

    async def register_online(self, hub_url: str):
        """Alias legacy para compatibilidad. Usa register_with_backoff."""
        await self.register_with_backoff(hub_url)
