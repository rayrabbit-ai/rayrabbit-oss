"""
RayRabbit OSS — Test Suite: Offline Tolerance (Outbox Pattern)
==============================================================
Tests funcionales para OutboxStore y OfflineToleranceService.
Cubre:
- Persistencia de mensajes en outbox SQLite cuando el receptor no existe
- Recuperación de mensajes pendientes
- Eliminación tras entrega exitosa
- Límite de intentos máximos (max_attempts=3 → eliminación automática)
- Integración con MessageBus: mensajes a agentes offline van al outbox

NOTA: Estos tests NO usan mocks. Usan las clases de producción reales.

SPDX-License-Identifier: AGPL-3.0-only
"""
import asyncio
import pytest
from pathlib import Path

from rayrabbit.resilience.offline_tolerance import OutboxStore
from rayrabbit.communication.message import Message, MessageType


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def outbox_db(tmp_path) -> str:
    """Ruta de base de datos SQLite en directorio temporal."""
    return str(tmp_path / "test_outbox.db")


@pytest.fixture()
def outbox_store(outbox_db) -> OutboxStore:
    """OutboxStore real con base de datos de prueba."""
    return OutboxStore(db_path=outbox_db)


def make_message(
    sender_id="sender_agent",
    recipient_id="offline_agent",
    content=None,
) -> Message:
    """Fábrica de mensajes de prueba."""
    return Message(
        sender_id=sender_id,
        sender_name="Test Sender",
        recipient_id=recipient_id,
        content=content or {"task": "test_task", "data": "payload"},
        message_type=MessageType.REQUEST,
    )


# ─── TEST-05a: store_message persiste en SQLite ───────────────────────────────

@pytest.mark.asyncio
async def test_outbox_store_persists_message(outbox_store):
    """
    DADO un OutboxStore vacío,
    CUANDO se almacena un mensaje,
    ENTONCES get_pending_messages debe retornar ese mensaje.
    """
    msg = make_message()
    result = await outbox_store.store_message(msg)
    assert result is True, "store_message debe retornar True en caso de éxito"

    pending = await outbox_store.get_pending_messages()
    assert len(pending) >= 1, "Debe haber al menos 1 mensaje pendiente"

    found = [m for m in pending if m.message_id == msg.message_id]
    assert len(found) == 1, f"El mensaje {msg.message_id} debe estar en el outbox"
    assert found[0].sender_id == msg.sender_id
    assert found[0].recipient_id == msg.recipient_id


# ─── TEST-05b: remove_message elimina el mensaje ─────────────────────────────

@pytest.mark.asyncio
async def test_outbox_remove_message(outbox_store):
    """
    DADO un OutboxStore con un mensaje pendiente,
    CUANDO se llama a remove_message,
    ENTONCES el mensaje ya no debe aparecer en get_pending_messages.
    """
    msg = make_message()
    await outbox_store.store_message(msg)

    # Verificar que existe
    pending_before = await outbox_store.get_pending_messages()
    assert any(m.message_id == msg.message_id for m in pending_before)

    # Eliminar
    await outbox_store.remove_message(msg.message_id)

    # Verificar que fue eliminado
    pending_after = await outbox_store.get_pending_messages()
    assert not any(m.message_id == msg.message_id for m in pending_after), \
        "El mensaje debe haber sido eliminado del outbox"


# ─── TEST-05c: store_message es idempotente (INSERT OR IGNORE) ────────────────

@pytest.mark.asyncio
async def test_outbox_store_is_idempotent(outbox_store):
    """
    DADO un mensaje ya almacenado,
    CUANDO se intenta almacenar el mismo mensaje nuevamente (mismo message_id),
    ENTONCES solo debe existir UNA copia (INSERT OR IGNORE).
    """
    msg = make_message()
    await outbox_store.store_message(msg)
    await outbox_store.store_message(msg)  # Segunda llamada con mismo ID

    pending = await outbox_store.get_pending_messages()
    matching = [m for m in pending if m.message_id == msg.message_id]
    assert len(matching) == 1, "INSERT OR IGNORE debe prevenir duplicados"


# ─── TEST-05d: increment_attempt acumula intentos ────────────────────────────

@pytest.mark.asyncio
async def test_outbox_increment_attempt_removes_after_max(outbox_store):
    """
    DADO un mensaje en el outbox,
    CUANDO increment_attempt supera max_attempts (3),
    ENTONCES el mensaje debe ser eliminado automáticamente.
    """
    msg = make_message()
    await outbox_store.store_message(msg)

    # 3 intentos → eliminación automática
    await outbox_store.increment_attempt(msg.message_id, max_attempts=3)
    await outbox_store.increment_attempt(msg.message_id, max_attempts=3)
    await outbox_store.increment_attempt(msg.message_id, max_attempts=3)

    pending = await outbox_store.get_pending_messages()
    assert not any(m.message_id == msg.message_id for m in pending), \
        "El mensaje debe ser eliminado tras superar el límite de intentos"


# ─── TEST-05e: Múltiples mensajes en el outbox ────────────────────────────────

@pytest.mark.asyncio
async def test_outbox_stores_multiple_messages(outbox_store):
    """
    DADO múltiples mensajes de diferentes remitentes,
    CUANDO se almacenan en el outbox,
    ENTONCES todos deben recuperarse correctamente.
    """
    messages = [
        make_message(sender_id=f"agent_{i}", recipient_id="offline_hub")
        for i in range(5)
    ]
    for msg in messages:
        await outbox_store.store_message(msg)

    pending = await outbox_store.get_pending_messages()
    stored_ids = {m.message_id for m in pending}

    for msg in messages:
        assert msg.message_id in stored_ids, \
            f"El mensaje {msg.message_id} debe estar en el outbox"


# ─── TEST-05f: Integración con MessageBus — agente offline → outbox ───────────

@pytest.mark.asyncio
async def test_message_bus_routes_to_outbox_when_agent_offline():
    """
    DADO un MessageBus en ejecución,
    CUANDO se publica un mensaje a un agente que NO está registrado,
    ENTONCES el mensaje debe quedar guardado en el OutboxStore (Offline Tolerance).

    Este test verifica el flujo real de resiliencia definido en
    02_Arquitectura_Core_y_Protocolos.md §2 (OfflineToleranceService).
    """
    from rayrabbit.core.message_bus import MessageBus

    bus = MessageBus()
    await bus.start()

    try:
        msg = Message(
            sender_id="test_sender",
            sender_name="Test Sender",
            recipient_id="nonexistent_offline_agent",
            content={"task": "offline_delivery_test"},
            message_type=MessageType.REQUEST,
        )

        # Publicar a un agente que no existe — debe ir al outbox
        publish_result = await bus.publish(msg)

        # publish() siempre retorna True (el fallback al outbox es transparente)
        assert publish_result is True, "publish() debe retornar True incluso con fallback al outbox"

        # Dar tiempo al asyncio para procesar
        await asyncio.sleep(0.1)

        # Verificar que el mensaje está en el outbox store
        pending = await bus.offline_tolerance.store.get_pending_messages()
        found = [m for m in pending if m.message_id == msg.message_id]
        assert len(found) == 1, \
            "El mensaje a un agente offline debe persistir en el OutboxStore"

    finally:
        await bus.stop()
