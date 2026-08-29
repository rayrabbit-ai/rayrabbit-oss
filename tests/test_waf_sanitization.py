"""
RayRabbit OSS — Test Suite: WAF Data Validation
================================================
Tests funcionales para DataValidator (Hub WAF — MAESTRO Perimeter Shield).
Cubre:
- Detección y bloqueo de SQL Injection
- Detección y bloqueo de XSS
- Detección y bloqueo de Path Traversal
- Paso libre de payloads legítimos
- Sanitización HTML con SanitizationMode.ESCAPE

NOTA: Estos tests NO usan mocks. Usan las clases de producción reales.

SPDX-License-Identifier: AGPL-3.0-only
"""
import pytest
from rayrabbit.security.data_validation import DataValidator, SanitizationMode, ValidationLevel


@pytest.fixture()
def validator():
    """DataValidator sin AuditManager (modo standalone para tests unitarios)."""
    return DataValidator()


# ─── SQL Injection ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("attack,label", [
    ("'; DROP TABLE agents; --", "DROP TABLE con comentario SQL"),
    ("SELECT * FROM users WHERE id = 1", "SELECT clásico"),
    ("INSERT INTO admin VALUES ('pwned')", "INSERT de escalada"),
    ("' UNION SELECT username, password FROM users --", "UNION SELECT dump"),
    ("/* bypass */ DELETE FROM logs", "Bypass con comentario de bloque"),
    ("admin'--", "Comentario de truncación SQL"),
])
def test_waf_blocks_sql_injection(validator, attack, label):
    """
    DADO un payload con vector de SQL Injection,
    CUANDO se llama a sanitize_payload,
    ENTONCES debe retornar False (bloqueado).
    """
    result = validator.sanitize_payload(attack)
    assert result is False, \
        f"WAF FALLÓ al bloquear SQL Injection [{label}]: '{attack}'"


# ─── XSS ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("attack,label", [
    ("<script>alert('xss')</script>", "Script tag clásico"),
    ("<script src='http://evil.com/x.js'></script>", "Script con src externo"),
    ("javascript:alert(1)", "Protocolo javascript:"),
    ("<img onerror=alert(1)>", "Event handler onerror"),
    ("<body onload=alert('pwned')>", "Event handler onload"),
])
def test_waf_blocks_xss(validator, attack, label):
    """
    DADO un payload con vector XSS,
    CUANDO se llama a sanitize_payload,
    ENTONCES debe retornar False (bloqueado).
    """
    result = validator.sanitize_payload(attack)
    assert result is False, \
        f"WAF FALLÓ al bloquear XSS [{label}]: '{attack}'"


# ─── Path Traversal ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("attack,label", [
    ("../../etc/passwd", "Path traversal clásico Unix"),
    ("../../../windows/system32/config/sam", "Path traversal Windows"),
    ("....//....//etc/passwd", "Double dot con forward slash"),
])
def test_waf_blocks_path_traversal(validator, attack, label):
    """
    DADO un payload con vector de Path Traversal,
    CUANDO se llama a sanitize_payload,
    ENTONCES debe retornar False (bloqueado).
    """
    result = validator.sanitize_payload(attack)
    assert result is False, \
        f"WAF FALLÓ al bloquear Path Traversal [{label}]: '{attack}'"


# ─── Payloads Legítimos ───────────────────────────────────────────────────────

@pytest.mark.parametrize("legitimate,label", [
    (
        "Elaborar el procedimiento de chequeo médico general para el paciente Juan Pérez.",
        "Prompt médico en español"
    ),
    (
        "Rastrear el pedido ORD-2025-001 y optimizar su ruta de entrega.",
        "Prompt de logística"
    ),
    (
        "Crear una cuadrilla de agentes CrewAI para analizar el mercado financiero de Argentina.",
        "Prompt de orquestación CrewAI"
    ),
    (
        "¿Cuál es el estado del paquete con número de seguimiento 123456789?",
        "Query de estado de paquete"
    ),
    (
        "La temperatura en el depósito norte es de 22.5°C. El inventario está al 87%.",
        "Dato de IoT con números"
    ),
])
def test_waf_allows_legitimate_payloads(validator, legitimate, label):
    """
    DADO un payload legítimo (sin vectores de ataque),
    CUANDO se llama a sanitize_payload,
    ENTONCES debe retornar True (permitido).
    """
    result = validator.sanitize_payload(legitimate)
    assert result is True, \
        f"WAF BLOQUEÓ un payload legítimo [{label}]: '{legitimate[:80]}'"


# ─── Sanitización de strings ──────────────────────────────────────────────────

def test_sanitize_string_escapes_html(validator):
    """
    DADO un string con caracteres HTML peligrosos,
    CUANDO se usa sanitize_string con modo ESCAPE,
    ENTONCES los caracteres < > & " ' deben ser escapados.
    """
    raw = "<script>alert('hello & goodbye')</script>"
    sanitized = validator.sanitize_string(raw, SanitizationMode.ESCAPE)

    assert "<script>" not in sanitized, "El tag <script> no debe aparecer sin escapar"
    assert "&lt;" in sanitized, "< debe escaparse como &lt;"
    assert "&gt;" in sanitized, "> debe escaparse como &gt;"
    assert "&#x27;" in sanitized or "&amp;" in sanitized, \
        "Los caracteres especiales deben estar escapados"


# ─── Tipo no-string ───────────────────────────────────────────────────────────

def test_sanitize_payload_rejects_non_string(validator):
    """
    DADO un input que no es string (ej. None, dict, int),
    CUANDO se llama a sanitize_payload,
    ENTONCES debe retornar False (input inválido = bloqueado).
    """
    assert validator.sanitize_payload(None) is False  # type: ignore
    assert validator.sanitize_payload({"key": "value"}) is False  # type: ignore
    assert validator.sanitize_payload(12345) is False  # type: ignore
