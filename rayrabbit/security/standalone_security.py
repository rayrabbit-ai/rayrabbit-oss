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
import json
import base64
import yaml
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from datetime import datetime

class StandaloneKeyStore:
    """Gestor de llaves de grado empresarial para servicios autónomos (AES-256-GCM)."""
    def __init__(self, store_path: str, master_secret: str, salt: str):
        self.store_path = store_path
        self.master_key = self._derive_master_key(master_secret, salt.encode() if isinstance(salt, str) else salt)
        os.makedirs(self.store_path, exist_ok=True)

    def _derive_master_key(self, secret: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
            backend=default_backend()
        )
        return kdf.derive(secret.encode())

    def _encrypt_data(self, data: bytes) -> bytes:
        nonce = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.master_key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        return nonce + encryptor.tag + encrypted_data

    def _decrypt_data(self, encrypted_content: bytes) -> bytes:
        nonce = encrypted_content[:12]
        tag = encrypted_content[12:28]
        encrypted_data = encrypted_content[28:]
        cipher = Cipher(algorithms.AES(self.master_key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_data) + decryptor.finalize()

    def save_key(self, key_id: str, key_data: bytes, metadata: Dict[str, Any]):
        """Guarda una llave cifrada (.key) y sus metadatos (.json)."""
        encrypted_key = self._encrypt_data(key_data)
        with open(os.path.join(self.store_path, f"{key_id}.key"), 'wb') as f:
            f.write(encrypted_key)
        
        metadata.update({"key_id": key_id, "encrypted": True, "algorithm": "AES-256-GCM"})
        with open(os.path.join(self.store_path, f"{key_id}.json"), 'w') as f:
            json.dump(metadata, f, indent=2)

    def load_key(self, key_id: str) -> Optional[bytes]:
        """Carga y descifra una llave desde el almacén."""
        key_file = os.path.join(self.store_path, f"{key_id}.key")
        if not os.path.exists(key_file):
            return None
        with open(key_file, 'rb') as f:
            return self._decrypt_data(f.read())

class StandaloneJWS:
    """Generador de firmas JWS (RFC 7515) autónomo con llaves cifradas."""
    def __init__(self, agent_id: str, keystore: StandaloneKeyStore):
        self.agent_id = agent_id
        self.keystore = keystore

    def _b64url(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    def sign_message(self, message: Dict[str, Any]) -> str:
        """Firma un mensaje usando la llave privada RSA (cifrada en disco)."""
        private_key_bytes = self.keystore.load_key(f"{self.agent_id}_private")
        if not private_key_bytes:
            raise RuntimeError(f"Clave privada cifrada no encontrada para {self.agent_id}")

        private_key = serialization.load_pem_private_key(private_key_bytes, password=None, backend=default_backend())
        
        header = {"alg": "RS256", "typ": "JWS"}
        header_b64 = self._b64url(json.dumps(header, separators=(',', ':')).encode('utf-8'))
        payload_b64 = self._b64url(json.dumps(message, sort_keys=True, separators=(',', ':')).encode('utf-8'))
        
        signing_input = f"{header_b64}.{payload_b64}"
        signature = private_key.sign(
            signing_input.encode('utf-8'),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        
        return f"{signing_input}.{self._b64url(signature)}"

    def get_jws_headers(self, message: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, str]:
        """
        Genera el conjunto completo de cabeceras de seguridad JWS para un mensaje.
        Sigue el patrón de diseño orientado a objetos: la seguridad fabrica sus propios headers.
        """
        headers = {
            'X-RayRabbit-JWS': self.sign_message(message),
            'X-RayRabbit-Agent-ID': self.agent_id
        }
        
        if correlation_id:
            headers['X-RayRabbit-Correlation-ID'] = correlation_id
        
        pub_key_header = self.get_public_key_header()
        if pub_key_header:
            headers['X-RayRabbit-Bridge-Public-Key-PEM'] = pub_key_header
            
        return headers

    def get_public_key_header(self) -> str:
        """Retorna la clave pública en formato PEM limpio para headers HTTP."""
        pub_key_bytes = self.keystore.load_key(f"{self.agent_id}_public")
        if not pub_key_bytes:
            return ""
        pub_key_pem = pub_key_bytes.decode('utf-8')
        return pub_key_pem.replace('\n', '').replace('-----BEGIN PUBLIC KEY-----', '').replace('-----END PUBLIC KEY-----', '').strip()

class StandaloneAuditor:
    """Auditor autónomo que escribe en la ruta centralizada y en consola para depuración."""
    def __init__(self, agent_id: str, logs_dir: str):
        self.agent_id = agent_id
        self.logs_dir = logs_dir
        os.makedirs(self.logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.logs_dir, f"{agent_id}_internal.log")

    def log(self, level: str, message: str, **kwargs):
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "level": level,
            "agent_id": self.agent_id,
            "message": message,
            "extra": kwargs
        }
        # Escribir en archivo (JSON Lines)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Imprimir en consola para visibilidad inmediata del usuario (RayRabbit Style)
        color = "\033[32m" if level == "INFO" else "\033[31m" if level == "ERROR" else "\033[33m"
        reset = "\033[0m"
        print(f"{timestamp} | {color}{level:8}{reset} | {self.agent_id:20} | {message}")

def ensure_identity(agent_id: str, keystore: StandaloneKeyStore):
    """Genera llaves RSA-4096 y las guarda cifradas si no existen."""
    if not keystore.load_key(f"{agent_id}_private"):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096, backend=default_backend())
        
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        now = datetime.now().isoformat()
        keystore.save_key(f"{agent_id}_private", private_bytes, {"type": "private", "created": now})
        keystore.save_key(f"{agent_id}_public", public_bytes, {"type": "public", "created": now})


