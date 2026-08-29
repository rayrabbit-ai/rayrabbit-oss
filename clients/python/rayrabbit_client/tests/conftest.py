"""
conftest.py - Fixtures globales para la suite de pruebas del ResearcherAgent SDK.

Uso:
    pytest tests/ -v -s

Requiere que el Hub de RayRabbit esté corriendo en el puerto 8005 para los tests E2E.
"""

import pytest
import asyncio
import subprocess
import time
import sys
import os
from pathlib import Path

# Asegurar que el SDK está en el path
SDK_SRC = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SDK_SRC))

from rayrabbit_client.agents.researcher_agent.researcher_agent import ResearcherAgent


@pytest.fixture(scope="session")
def event_loop():
    """Event loop compartido para toda la sesión de pruebas (requerido por pytest-asyncio)."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def agent():
    """
    Fixture que provee una instancia real del ResearcherAgent.
    No conecta al Hub (eso es para tests E2E). Solo inicializa el agente localmente.
    """
    a = ResearcherAgent(agent_id="test_researcher", name="TestResearcher")
    yield a


@pytest.fixture(scope="session")
def hub_url():
    """URL del Hub real de RayRabbit. Los tests E2E requieren que esté corriendo."""
    return "ws://localhost:8005/ws"


@pytest.fixture(scope="session")
def sample_pdf_path(tmp_path_factory):
    """Genera un PDF mínimo real para las pruebas de análisis de documentos."""
    try:
        from reportlab.pdfgen import canvas
        path = tmp_path_factory.mktemp("docs") / "test_doc.pdf"
        c = canvas.Canvas(str(path))
        c.drawString(100, 750, "RayRabbit ResearcherAgent Test Document")
        c.drawString(100, 700, "Artificial intelligence is transforming the world in 2026.")
        c.save()
        return str(path)
    except ImportError:
        # Fallback: crear un PDF mínimo manualmente si reportlab no está disponible
        path = tmp_path_factory.mktemp("docs") / "test_doc.pdf"
        # PDF mínimo válido
        path.write_bytes(
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj "
            b"xref\n0 4\n0000000000 65535 f\n"
            b"0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        )
        return str(path)


@pytest.fixture(scope="session")
def sample_text_content():
    """Texto real (no simulado) para pruebas de NLP."""
    return (
        "Artificial intelligence and machine learning have achieved remarkable progress in 2026. "
        "The World Economic Forum reports that AI tools are reshaping industries globally. "
        "Companies like OpenAI, Anthropic, and Google have released powerful language models. "
        "Investment in AI reached $200 billion in 2025 according to industry analysts. "
        "Researchers at MIT and Stanford published groundbreaking papers on quantum computing."
    )
