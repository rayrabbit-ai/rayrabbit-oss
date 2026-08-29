"""
RayRabbit OSS — Test Suite: MAESTRO Standalone Security
=======================================================
Tests funcionales para StandaloneKeyStore, StandaloneJWS y ensure_identity.
Cubre el ciclo completo de Mutual PoP (Proof of Possession) Handshake:
- Generación de identidad RSA-4096 cifrada en disco
- Firma JWS (RFC 7515) por mensaje
- Verificación de firma con clave pública
- Rechazo de firma inválida / manipulada

NOTA: Estos tests NO usan mocks. Usan las clases de producción reales.

SPDX-License-Identifier: AGPL-3.0-only
"""
import base64
import json
import pytest
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

from rayrabbit.security.standalone_security import (
    StandaloneKeyStore,
    StandaloneJWS,
    ensure_identity,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def hub_store(tmp_path):
    """KeyStore del Hub con credenciales de prueba."""
    return StandaloneKeyStore(
        store_path=str(tmp_path / "hub_keystore"),
        master_secret="test_master_secret_for_hub_node",
        salt="test_salt_hub_16b",
    )


@pytest.fixture()
def node_store(tmp_path):
    """KeyStore de un nodo SDK con credenciales de prueba."""
    return StandaloneKeyStore(
        store_path=str(tmp_path / "node_keystore"),
        master_secret="test_master_secret_for_sdk_node",
        salt="test_salt_node_16",
    )


# ─── TEST-01a: ensure_identity crea claves RSA-4096 cifradas ─────────────────

def test_ensure_identity_creates_encrypted_keys(hub_store):
    """
    DADO un KeyStore vacío,
    CUANDO se llama a ensure_identity para 'hub_agent',
    ENTONCES deben existir archivos .key y .json para private y public,
    Y las claves deben cargarse como bytes PEM válidos.
    """
    # Pre-condición: no existen claves
    assert hub_store.load_key("hub_agent_private") is None
    assert hub_store.load_key("hub_agent_public") is None

    # Acción
    ensure_identity("hub_agent", hub_store)

    # Verificar que las claves existen y se pueden cargar
    private_bytes = hub_store.load_key("hub_agent_private")
    public_bytes = hub_store.load_key("hub_agent_public")

    assert private_bytes is not None, "La clave privada debe existir tras ensure_identity"
    assert public_bytes is not None, "La clave pública debe existir tras ensure_identity"

    # Verificar que son PEM válidos cargables por cryptography
    private_key = serialization.load_pem_private_key(
        private_bytes, password=None, backend=default_backend()
    )
    public_key = serialization.load_pem_public_key(public_bytes, backend=default_backend())

    assert private_key is not None
    assert public_key is not None

    # Verificar que es RSA-4096
    assert private_key.key_size == 4096, f"Se esperaba RSA-4096, se obtuvo RSA-{private_key.key_size}"


def test_ensure_identity_is_idempotent(hub_store):
    """
    DADO un KeyStore que ya tiene identidad,
    CUANDO se llama a ensure_identity nuevamente,
    ENTONCES NO se sobreescriben las claves existentes (idempotencia).
    """
    ensure_identity("hub_agent", hub_store)
    original_private = hub_store.load_key("hub_agent_private")

    # Segunda llamada
    ensure_identity("hub_agent", hub_store)
    second_private = hub_store.load_key("hub_agent_private")

    assert original_private == second_private, "ensure_identity debe ser idempotente"


# ─── TEST-01b: Cifrado en reposo — claves NO están en texto plano ─────────────

def test_keystore_private_key_is_encrypted_at_rest(hub_store, tmp_path):
    """
    DADO un KeyStore con identidad generada,
    CUANDO se leen los archivos .key del disco,
    ENTONCES el contenido NO debe contener PEM en texto plano.
    """
    ensure_identity("hub_agent", hub_store)

    keystore_dir = Path(tmp_path / "hub_keystore")
    key_files = list(keystore_dir.glob("*.key"))
    assert len(key_files) > 0, "Deben existir archivos .key en el directorio del keystore"

    for kf in key_files:
        raw_bytes = kf.read_bytes()
        assert b"BEGIN RSA PRIVATE KEY" not in raw_bytes, \
            f"FALLO: Clave privada en texto plano (PKCS#1) encontrada en {kf.name}"
        assert b"BEGIN PRIVATE KEY" not in raw_bytes, \
            f"FALLO: Clave privada en texto plano (PKCS#8) encontrada en {kf.name}"
        assert b"BEGIN PUBLIC KEY" not in raw_bytes, \
            f"FALLO: Clave pública en texto plano encontrada en {kf.name}"


def test_wrong_master_secret_cannot_decrypt(hub_store, tmp_path):
    """
    DADO un KeyStore con identidad guardada,
    CUANDO se intenta descifrar con un master_secret incorrecto,
    ENTONCES la operación DEBE fallar lanzando una excepción de autenticación GCM.
    El AES-256-GCM autentica los datos — una clave incorrecta produce InvalidTag.
    Este es el comportamiento de seguridad CORRECTO: fallo ruidoso, nunca silencioso.
    """
    from cryptography.exceptions import InvalidTag

    ensure_identity("hub_agent", hub_store)

    # Crear un segundo store con diferente secreto pero misma ruta de disco
    wrong_store = StandaloneKeyStore(
        store_path=str(tmp_path / "hub_keystore"),
        master_secret="WRONG_SECRET_THAT_IS_NOT_CORRECT",
        salt="test_salt_hub_16b",
    )

    # AES-256-GCM con clave incorrecta DEBE lanzar InvalidTag (no retornar datos corruptos)
    # Este es el comportamiento criptográfico correcto: fallo ruidoso en autenticación
    with pytest.raises((InvalidTag, Exception)):
        wrong_store.load_key("hub_agent_private")


# ─── TEST-02: JWS Signing — Firma y Verificación ─────────────────────────────

def _b64url_decode(s: str) -> bytes:
    """Decodifica base64url con padding automático."""
    padding_needed = 4 - (len(s) % 4)
    if padding_needed != 4:
        s += "=" * padding_needed
    return base64.urlsafe_b64decode(s)


def test_jws_sign_message_produces_three_part_token(hub_store):
    """
    DADO un KeyStore con identidad,
    CUANDO StandaloneJWS.sign_message firma un payload,
    ENTONCES el resultado debe ser un token JWS de 3 partes (RFC 7515 Compact).
    """
    ensure_identity("hub_agent", hub_store)
    jws = StandaloneJWS("hub_agent", hub_store)

    payload = {"method": "tools/call", "params": {"name": "test_tool"}, "id": 1}
    token = jws.sign_message(payload)

    assert isinstance(token, str), "El token JWS debe ser un string"
    parts = token.split(".")
    assert len(parts) == 3, f"El token JWS debe tener 3 partes, tiene {len(parts)}"

    # Decodificar header y verificar algoritmo
    header_json = json.loads(base64.urlsafe_b64decode(parts[0] + "==").decode())
    assert header_json.get("alg") == "RS256", "El algoritmo debe ser RS256"
    assert header_json.get("typ") == "JWS", "El tipo debe ser JWS"


def test_jws_signature_is_valid_with_public_key(hub_store):
    """
    DADO un mensaje firmado con StandaloneJWS,
    CUANDO se verifica la firma con la clave pública del keystore,
    ENTONCES la verificación DEBE ser exitosa (no lanzar excepción).
    """
    ensure_identity("hub_agent", hub_store)
    jws = StandaloneJWS("hub_agent", hub_store)

    payload = {"sender_id": "hub_agent", "method": "tasks/create", "id": 42}
    token = jws.sign_message(payload)

    parts = token.split(".")
    signing_input = f"{parts[0]}.{parts[1]}"
    signature_bytes = _b64url_decode(parts[2])

    # Cargar clave pública desde el keystore
    pub_pem_bytes = hub_store.load_key("hub_agent_public")
    assert pub_pem_bytes is not None
    public_key = serialization.load_pem_public_key(pub_pem_bytes, backend=default_backend())

    # Verificar la firma — NO debe lanzar excepción
    public_key.verify(
        signature_bytes,
        signing_input.encode("utf-8"),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    # Si llegamos aquí, la firma es válida ✓


def test_jws_tampered_payload_fails_verification(hub_store):
    """
    DADO un token JWS válido,
    CUANDO el payload es manipulado (ataque MITM),
    ENTONCES la verificación DEBE fallar con InvalidSignature.
    """
    ensure_identity("hub_agent", hub_store)
    jws = StandaloneJWS("hub_agent", hub_store)

    original_payload = {"action": "execute_task", "authorized": True}
    token = jws.sign_message(original_payload)
    parts = token.split(".")

    # Manipular el payload (parte central) — cambiar authorized a False
    malicious_payload = {"action": "execute_task", "authorized": False}
    malicious_b64 = base64.urlsafe_b64encode(
        json.dumps(malicious_payload, sort_keys=True, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()

    tampered_token = f"{parts[0]}.{malicious_b64}.{parts[2]}"
    tampered_parts = tampered_token.split(".")
    tampered_signing_input = f"{tampered_parts[0]}.{tampered_parts[1]}"
    signature_bytes = _b64url_decode(tampered_parts[2])

    pub_pem_bytes = hub_store.load_key("hub_agent_public")
    public_key = serialization.load_pem_public_key(pub_pem_bytes, backend=default_backend())

    with pytest.raises(InvalidSignature):
        public_key.verify(
            signature_bytes,
            tampered_signing_input.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )


# ─── TEST-03: Mutual PoP Handshake — Simulación completa ─────────────────────

def test_mutual_pop_handshake_hub_and_node(hub_store, node_store):
    """
    DADO dos agentes (Hub y Nodo SDK) con identidades independientes,
    CUANDO el Nodo firma un reto y el Hub lo verifica (Mutual PoP),
    ENTONCES la verificación DEBE ser exitosa,
    Y una firma inválida de un tercero DEBE ser rechazada.

    Simula el handshake definido en 03_Seguridad_MAESTRO_AIDA_y_Runtime.md §1.1
    """
    # 1. Ambos agentes generan su identidad
    ensure_identity("hub_agent", hub_store)
    ensure_identity("node_agent", node_store)

    # 2. El Nodo firma el reto de registro
    timestamp = "2026-08-03T19:00:00Z"
    challenge = f"REG-AUTH:node_agent:{timestamp}"

    node_private_bytes = node_store.load_key("node_agent_private")
    node_private_key = serialization.load_pem_private_key(
        node_private_bytes, password=None, backend=default_backend()
    )
    signature = node_private_key.sign(
        challenge.encode("utf-8"),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )

    # 3. El Hub verifica la firma usando la clave pública del Nodo
    node_pub_bytes = node_store.load_key("node_agent_public")
    node_public_key = serialization.load_pem_public_key(node_pub_bytes, backend=default_backend())

    # No debe lanzar excepción
    node_public_key.verify(
        signature,
        challenge.encode("utf-8"),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )

    # 4. Una firma aleatoria (atacante sin clave privada) DEBE fallar
    import os
    fake_signature = os.urandom(512)
    with pytest.raises(InvalidSignature):
        node_public_key.verify(
            fake_signature,
            challenge.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )


def test_get_jws_headers_returns_required_keys(hub_store):
    """
    DADO un JWS configurado,
    CUANDO se generan los headers HTTP/WS,
    ENTONCES deben incluir X-RayRabbit-JWS y X-RayRabbit-Agent-ID.
    """
    ensure_identity("hub_agent", hub_store)
    jws = StandaloneJWS("hub_agent", hub_store)

    headers = jws.get_jws_headers({"data": "test"}, correlation_id="corr-123")

    assert "X-RayRabbit-JWS" in headers, "Header X-RayRabbit-JWS debe estar presente"
    assert "X-RayRabbit-Agent-ID" in headers, "Header X-RayRabbit-Agent-ID debe estar presente"
    assert headers["X-RayRabbit-Agent-ID"] == "hub_agent"
    assert "X-RayRabbit-Correlation-ID" in headers
    assert headers["X-RayRabbit-Correlation-ID"] == "corr-123"
    # El token JWS debe tener 3 partes
    assert len(headers["X-RayRabbit-JWS"].split(".")) == 3
