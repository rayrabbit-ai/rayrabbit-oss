import pytest
import json
import os
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch
from rayrabbit.protocols.a2ui.agent import SovereignA2UIAgent
from rayrabbit.protocols.a2ui.generator import A2UIGenerator
from rayrabbit.protocols.a2ui.validator import A2UIValidator

# --- Tests para A2UIGenerator (T1-T4) ---

def test_generator_begin_rendering():
    payload = A2UIGenerator.begin_rendering("test_surface", "test_catalog")
    assert payload["version"] == "v0.9.1"
    assert payload["beginRendering"]["surfaceId"] == "test_surface"
    assert payload["beginRendering"]["catalogId"] == "test_catalog"

def test_generator_surface_update():
    components = [{"id": "c1", "component": {"Text": {"text": "Hello"}}}]
    payload = A2UIGenerator.surface_update("test_surface", components)
    assert payload["version"] == "v0.9.1"
    assert payload["surfaceUpdate"]["surfaceId"] == "test_surface"
    assert len(payload["surfaceUpdate"]["components"]) == 1

def test_generator_update_data_model():
    payload = A2UIGenerator.update_data_model("test_surface", "Narrative text", "/narrative")
    assert payload["version"] == "v0.9.1"
    assert payload["updateDataModel"]["surfaceId"] == "test_surface"
    assert payload["updateDataModel"]["path"] == "/narrative"
    assert payload["updateDataModel"]["value"] == "Narrative text"

def test_generator_delete_surface():
    payload = A2UIGenerator.delete_surface("test_surface")
    assert payload["version"] == "v0.9.1"
    assert payload["deleteSurface"]["surfaceId"] == "test_surface"

# --- Tests para A2UIValidator (T5-T7) ---

def test_validator_valid_message():
    validator = A2UIValidator()
    msg = {
        "version": "v0.9.1",
        "beginRendering": {
            "surfaceId": "test",
            "catalogId": "test_catalog"
        }
    }
    assert validator.validate_message(msg) is True

def test_validator_invalid_message():
    validator = A2UIValidator()
    msg = {"no_version": "invalid"}
    assert validator.validate_message(msg) is False

def test_validator_list_of_messages():
    validator = A2UIValidator()
    msgs = [
        {"version": "v0.9.1", "beginRendering": {"surfaceId": "s1", "catalogId": "c1"}},
        {"version": "v0.9.1", "surfaceUpdate": {"surfaceId": "s1", "components": []}}
    ]
    assert validator.validate_message(msgs) is True

# --- Tests para SovereignA2UIAgent (T8-T14) ---

@patch.dict(os.environ, {}, clear=True)
def test_agent_init_no_api_key():
    agent = SovereignA2UIAgent("test_agent_no_key", "Test Agent")
    assert agent.api_key is None
    assert len(agent.api_keys) == 0

def test_agent_memory_l2_persistence():
    agent = SovereignA2UIAgent("test_agent_p", "Test Agent")
    agent._update_conversation_history("user_123", "hello", "hi there")
    
    history = agent.conversation_history["user_123"]
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "hi there"
    
    prompt_msgs = agent._prepare_prompt("how are you?", "user_123")
    assert len(prompt_msgs) == 4
    assert prompt_msgs[1]["content"] == "hello"
    assert prompt_msgs[2]["content"] == "hi there"
    assert prompt_msgs[3]["content"] == "how are you?"

def test_agent_memory_l2_sliding_window():
    agent = SovereignA2UIAgent("test_agent_w", "Test Agent")
    agent.max_history_length = 3
    # 5 pares user/assistant
    for i in range(5):
        agent._update_conversation_history("user_test", f"msg {i}", f"resp {i}")
    
    history = agent.conversation_history["user_test"]
    # max_history_length * 2 = 6
    assert len(history) == 6
    assert history[0]["content"] == "msg 2"


def test_agent_skill_loads_specs():
    agent = SovereignA2UIAgent("test_agent_s", "Test Agent")
    skill = agent._load_a2ui_skill()
    assert "A2UI" in skill
    assert "beginRendering" in skill or "surfaceUpdate" in skill

@pytest.mark.asyncio
async def test_agent_active_surfaces():
    agent = SovereignA2UIAgent("test_agent_as", "Test Agent")
    # Mockear send_a2ui_message
    agent.send_a2ui_message = MagicMock(return_value=asyncio.Future())
    agent.send_a2ui_message.return_value.set_result(None)
    
    # Signatura: recipient_id, surface_id, root_id, catalog_id...
    await agent.send_begin_rendering("client_1", "surface_1", "root_1", "catalog_1")
    assert agent.active_surfaces["surface_1"] == "catalog_1"
    agent.send_a2ui_message.assert_called_once()

@pytest.mark.asyncio
async def test_agent_broadcast_target():
    agent = SovereignA2UIAgent("test_agent_bt", "Test Agent")
    agent.send_a2ui_message = MagicMock(return_value=asyncio.Future())
    agent.send_a2ui_message.return_value.set_result(None)
    
    payload = {"info": "test"}
    await agent.broadcast_a2ui(payload)
    
    args, kwargs = agent.send_a2ui_message.call_args
    assert args[0] == "a2ui_client"

@pytest.mark.asyncio
async def test_agent_sse_stream():
    agent = SovereignA2UIAgent("test_agent_sse", "Test Agent")
    # Simular una suscripción SSE
    gen = agent.stream_ui_events()
    
    # Al llamar a stream_ui_events, se añade una queue a _ui_subscribers
    # Pero hay que avanzar el generador para que se ejecute el setup
    it = aiter(gen)
    
    # Avanzar hasta el primer await queue.get()
    task = asyncio.create_task(anext(it))
    await asyncio.sleep(0.1)
    
    # Ahora debería haber un suscriptor
    assert len(agent._ui_subscribers) == 1
    queue = list(agent._ui_subscribers)[0]
    
    # Meter un mensaje
    payload = {"test": "data"}
    await queue.put(payload)
    
    # Leer el evento
    event = await asyncio.wait_for(task, timeout=1.0)
    assert "data: {" in event
    assert "\"test\": \"data\"" in event

