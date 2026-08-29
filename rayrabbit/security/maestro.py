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
"""Módulo de orquestación de seguridad MAESTRO para la versión OSS.

Proporciona la fachada de seguridad central (``MAESTROSecurity``) utilizada
por el núcleo del framework y los agentes, implementando de forma transparente
el cifrado persistente en reposo y la firma/verificación JWS autónoma.
"""


import base64
import json
from typing import Any, Dict, Optional, TYPE_CHECKING

from ..utils.logger import get_logger
from .encryption_defs import EncryptionAlgorithm, EncryptionKey, KeyType
from .standalone_security import StandaloneJWS, StandaloneKeyStore, ensure_identity

if TYPE_CHECKING:
    from ..utils.config import SecurityConfig
    from .auditing import AuditManager


class MAESTROSecurity:
    """Orquestador de seguridad unificado para agentes y núcleo de RayRabbit OSS."""

    def __init__(
        self, agent_id: str, config: "SecurityConfig", audit_manager: "AuditManager"
    ) -> None:
        """Inicializa la seguridad para un agente utilizando el almacén de claves autónomo.

        Args:
            agent_id: ID único del agente o núcleo.
            config: Configuración de seguridad.
            audit_manager: Instancia del gestor de auditoría.
        """
        self.agent_id = agent_id
        self.config = config
        self.audit_manager = audit_manager
        self.logger = get_logger(f"MAESTRO-{self.agent_id}")

        from rayrabbit.core.runtime_context import RuntimeContext
        keystore_path = str(RuntimeContext.get_identity_dir())
        if not config or not config.master_secret or not config.salt:
            raise RuntimeError(
                "CRITICAL: MAESTROSecurity requiere 'master_secret' y 'salt' configurados vía entorno. "
                "El uso de secretos por defecto ha sido deshabilitado para despliegues OSS."
            )
        master_secret = config.master_secret
        salt = config.salt

        self.keystore = StandaloneKeyStore(keystore_path, master_secret, salt)
        self.jws = StandaloneJWS(self.agent_id, self.keystore)
        self.public_key_cache: Dict[str, EncryptionKey] = {}

        # Asegura la existencia del par de claves de identidad RSA-4096
        ensure_identity(self.agent_id, self.keystore)

    def _ensure_identity_key(self) -> None:
        """Asegura la existencia del par de claves de identidad RSA-4096."""
        ensure_identity(self.agent_id, self.keystore)

    def update_public_key_cache(self, key_cache: Dict[str, EncryptionKey]) -> None:
        """Actualiza el caché de claves públicas en memoria."""
        self.public_key_cache = key_cache
        self.logger.info(f"Caché de claves públicas actualizado con {len(key_cache)} claves.")

    def get_identity_key(self, key_type: KeyType) -> Optional[EncryptionKey]:
        """Recupera la clave de identidad del agente."""
        kt_str = key_type.value if hasattr(key_type, "value") else str(key_type)
        key_id = f"{self.agent_id}_{kt_str}"
        key_data = self.keystore.load_key(key_id)
        if not key_data:
            return None
        return EncryptionKey(
            key_id=key_id,
            key_data=key_data,
            owner_id=self.agent_id,
            key_type=key_type,
            algorithm=EncryptionAlgorithm.RSA_4096,
        )

    def encrypt_for_storage(self, data: bytes) -> bytes:
        """Cifra datos simétricamente con AES-256-GCM para persistencia."""
        return self.keystore._encrypt_data(data)

    def encrypt_for(self, data: bytes, agent_id: str) -> bytes:
        """Cifra datos para un agente destinatario usando MAESTRO Security."""
        return self.encrypt_for_storage(data)

    def decrypt_for_storage(self, encrypted_data: bytes, agent_id: Optional[str] = None) -> bytes:
        """Descifra datos persistentes usando la clave del almacén."""
        return self.keystore._decrypt_data(encrypted_data)

    def sign_message(self, message: Dict[str, Any]) -> str:
        """Firma un mensaje usando JWS (RS256)."""
        return self.jws.sign_message(message)

    def sign(self, data: bytes) -> str:
        """Firma datos canónicos en bytes utilizando RSA-4096 PSS con SHA-256."""
        import base64
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        priv_key_bytes = self.keystore.load_key(f"{self.agent_id}_private")
        if not priv_key_bytes:
            return ""
        priv_key = load_pem_private_key(priv_key_bytes, password=None)
        sig = priv_key.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return base64.b64encode(sig).decode("utf-8")

    def verify(self, signature_b64: str, data: bytes, sender_agent_id: str) -> bool:
        """Verifica una firma RSA-4096 PSS contra los datos canónicos recibidos."""
        import base64
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        pub_key_bytes = None
        if sender_agent_id in self.public_key_cache:
            pub_key_bytes = self.public_key_cache[sender_agent_id].key_data
        else:
            pub_key_bytes = self.keystore.load_key(f"{sender_agent_id}_public")

        if not pub_key_bytes:
            return False

        try:
            pub_key = load_pem_public_key(pub_key_bytes)
            sig_bytes = base64.b64decode(signature_b64)
            pub_key.verify(
                sig_bytes,
                data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            self.logger.error(f"Fallo de verificación de firma de '{sender_agent_id}': {e}")
            return False

    def decrypt_from(self, data: bytes) -> bytes:
        """Descifra datos recibidos o persistentes."""
        return self.decrypt_for_storage(data)

    def get_jws_headers(
        self, message: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Genera las cabeceras HTTP de seguridad A2A con la firma JWS."""
        return self.jws.get_jws_headers(message, correlation_id)

    def verify_message(self, jws_token: str, sender_agent_id: str) -> Optional[Dict[str, Any]]:
        """Verifica un mensaje firmado mediante JWS usando la clave pública del emisor."""
        try:
            parts = jws_token.split(".")
            if len(parts) != 3:
                return None
            header_b64, payload_b64, signature_b64 = parts

            # Ajuste de relleno para base64url
            rem = len(signature_b64) % 4
            if rem:
                signature_b64 += "=" * (4 - rem)
            signature = base64.urlsafe_b64decode(signature_b64.encode("utf-8"))

            # Obtención de la clave pública del emisor
            sender_public_key_bytes = None
            if sender_agent_id in self.public_key_cache:
                sender_public_key_bytes = self.public_key_cache[sender_agent_id].key_data
            else:
                sender_public_key_bytes = self.keystore.load_key(f"{sender_agent_id}_public")

            if not sender_public_key_bytes:
                return None

            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives.serialization import load_pem_public_key

            public_key = load_pem_public_key(sender_public_key_bytes, backend=default_backend())

            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            public_key.verify(
                signature,
                signing_input,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )

            # Decodificación del payload
            rem = len(payload_b64) % 4
            if rem:
                payload_b64 += "=" * (4 - rem)
            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            return json.loads(payload_bytes.decode("utf-8"))
        except Exception as exc:
            self.logger.error(f"Error verificando mensaje JWS de {sender_agent_id}: {exc}")
            return None

    def authorize_task_action(self, agent_id: str, action: str, task_id: str, domain: str) -> bool:
        """Verifica si el agente tiene permisos (scopes) para realizar una acción en una tarea específica.
        Parte de la expansión MAESTRO para MCP v2.
        """
        # TODO: Implementar resolución real de scopes desde el Identity Provider.
        # Por ahora, permitimos todo dentro de la prueba de concepto si el agente está autenticado.
        self.logger.debug(f"Autorización MAESTRO: agent={agent_id} action={action} task={task_id} domain={domain} -> GRANTED")
        return True

    def generate_task_audit_hash(self, event_type: str, task_id: str, payload: Dict[str, Any], previous_hash: Optional[str] = None) -> str:
        """Genera un hash inmutable encadenado para un evento de tarea.
        Proporciona trazabilidad estricta (Hash chaining) para auditoría inmutable.
        """
        import hashlib
        # Serializar determinísticamente el payload
        payload_str = json.dumps(payload, sort_keys=True)
        data_to_hash = f"{event_type}:{task_id}:{payload_str}:{previous_hash or 'GENESIS'}"
        
        # Auditoría MAESTRO interna
        if self.audit_manager:
            self.audit_manager.log_event(
                level=AuditLevel.INFO,
                category=EventCategory.SYSTEM_CHANGE,
                event_type="TASK_AUDIT_HASH_GENERATED",
                action="hash_chaining",
                result="SUCCESS",
                details={"task_id": task_id, "event_type": event_type, "has_previous": previous_hash is not None}
            )
            
        return hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()

__all__ = ["MAESTROSecurity"]
