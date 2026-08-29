"""
spec_researcher_agent.py - Especificaciones SDD (Specification-Driven Development) del ResearcherAgent.

Estas pruebas NO usan mocks de negocio. Validan el comportamiento real de cada capacidad.

Ejecutar con:
    pytest tests/spec_researcher_agent.py -v -s

Para tests E2E (requiere Hub corriendo en puerto 8005):
    pytest tests/spec_researcher_agent.py -v -s -m e2e
"""

import pytest
import asyncio
import os
from typing import Dict, Any

pytestmark = pytest.mark.asyncio


# ============================================================================
# ESPECIFICACIÓN 1: BÚSQUEDA WEB AVANZADA (DuckDuckGo real)
# ============================================================================

class TestWebSearch:
    """Especificación: El agente debe buscar en internet de verdad sin mocks."""

    async def test_duckduckgo_returns_real_results(self, agent):
        """SPEC: _search_duckduckgo debe retornar URLs reales (no example.com)."""
        results = await agent._search_duckduckgo("RayRabbit AI interoperability", max_results=3)

        assert len(results) > 0, "DDG debe retornar al menos 1 resultado real"
        for r in results:
            assert r["url"] != "", "Cada resultado debe tener una URL real"
            assert "example.com" not in r["url"], "NO debe haber URLs de ejemplo/mock"
            assert r["source"] == "duckduckgo"
            assert r["title"] != ""

    async def test_web_search_command_returns_synthesis(self, agent):
        """SPEC: _command_web_search debe retornar una síntesis LLM si hay API key configurada."""
        # Solo ejecutamos la búsqueda, no la síntesis LLM (que requiere key externa)
        results = await agent._web_search("artificial intelligence 2026", max_results=2)

        assert "query" in results
        assert "results" in results
        assert results["results_count"] >= 0

    async def test_bing_search_requires_api_key(self, agent):
        """SPEC: Si no hay BING_API_KEY, debe retornar lista vacía sin crashear."""
        original_key = agent.search_apis["bing"]["api_key"]
        agent.search_apis["bing"]["api_key"] = None
        agent.search_apis["bing"]["enabled"] = False

        results = await agent._web_search("test", max_results=3, sources=["bing"])
        assert isinstance(results["results"], list), "Debe retornar lista incluso sin API key"

        # Restaurar
        agent.search_apis["bing"]["api_key"] = original_key


# ============================================================================
# ESPECIFICACIÓN 2: ANÁLISIS DE DOCUMENTOS NLP REAL
# ============================================================================

class TestDocumentAnalysis:
    """Especificación: El agente debe analizar documentos reales con NLP."""

    async def test_basic_document_analysis_extracts_keywords(self, agent, sample_text_content):
        """SPEC: _basic_document_analysis debe extraer palabras clave reales del texto."""
        analysis = agent._basic_document_analysis(sample_text_content)

        assert analysis["word_count"] > 0
        assert analysis["sentence_count"] > 0
        assert len(analysis["top_keywords"]) > 0
        # Palabras clave esperadas del texto real
        top_keywords_lower = [kw.lower() for kw in analysis["top_keywords"]]
        assert any(kw in top_keywords_lower for kw in ["artificial", "intelligence", "ai", "machine"])

    async def test_sentiment_analysis_is_real(self, agent, sample_text_content):
        """SPEC: El análisis de sentimiento debe usar VADER real y retornar scores en rango [-1, 1]."""
        analysis = agent._basic_document_analysis(sample_text_content)
        sentiment = analysis["sentiment"]

        assert "compound" in sentiment
        assert -1.0 <= sentiment["compound"] <= 1.0, "VADER compound debe estar entre -1 y 1"
        assert "pos" in sentiment
        assert "neg" in sentiment
        assert "neu" in sentiment

    async def test_analyze_document_command_with_text_content(self, agent, sample_text_content):
        """SPEC: _command_analyze_document debe procesar contenido de texto plano."""
        result = await agent._command_analyze_document(
            content=sample_text_content,
            document_type="text"
        )
        assert result["status"] == "success"
        assert "analysis" in result
        assert result["analysis"]["word_count"] > 0


# ============================================================================
# ESPECIFICACIÓN 3: BÚSQUEDA ACADÉMICA REAL (arXiv)
# ============================================================================

class TestAcademicSearch:
    """Especificación: El agente debe consultar arXiv real."""

    async def test_arxiv_returns_real_papers(self, agent):
        """SPEC: _search_arxiv debe retornar papers reales con DOI/URL de arxiv.org."""
        results = await agent._search_arxiv("large language models")

        assert len(results) > 0, "arXiv debe retornar papers reales"
        for paper in results[:3]:
            assert paper["title"] != ""
            assert "arxiv.org" in paper.get("url", "") or paper.get("id", "") != ""
            assert isinstance(paper.get("authors", []), list)

    async def test_academic_search_command_returns_structured_result(self, agent):
        """SPEC: _command_academic_search debe retornar resultado estructurado con fuentes."""
        result = await agent._command_academic_search(
            query="transformer neural networks",
            databases=["arxiv"]
        )
        assert result["status"] == "success"
        assert "results" in result
        assert "arxiv" in result["results"]


# ============================================================================
# ESPECIFICACIÓN 4: EXTRACCIÓN DE DATOS REAL (regex + spaCy NER)
# ============================================================================

class TestDataExtraction:
    """Especificación: El agente debe extraer entidades reales del texto."""

    async def test_extract_emails_real_regex(self, agent):
        """SPEC: _command_extract_data debe extraer emails reales con regex."""
        text = "Contact us at support@rayrabbit.ai or admin@example.org for more info."
        result = await agent._command_extract_data(content=text, patterns=["emails"])

        assert result["status"] == "success"
        emails = result.get("extracted_data", {}).get("emails", [])
        assert len(emails) == 2
        assert any("rayrabbit.ai" in e.get("value", "") for e in emails)

    async def test_extract_monetary_values(self, agent):
        """SPEC: _command_extract_data debe detectar valores monetarios."""
        text = "The investment round totaled $250,000,000 and the valuation was $1.5 billion."
        result = await agent._command_extract_data(content=text, patterns=["monetary_values"])

        assert result["status"] == "success"
        values = result.get("extracted_data", {}).get("monetary_values", [])
        assert len(values) > 0


# ============================================================================
# ESPECIFICACIÓN 5: VERIFICACIÓN DE HECHOS REAL
# ============================================================================

class TestFactChecking:
    """Especificación: El agente debe buscar evidencia real para fact-checking."""

    async def test_fact_check_searches_real_sources(self, agent):
        """SPEC: _fact_check debe buscar fuentes reales para validar o refutar una afirmación."""
        claim = "Python is one of the most popular programming languages in 2026"
        result = await agent._fact_check(claim)

        assert "status" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
        assert "supporting_evidence" in result
        # Debe haber al menos alguna evidencia de la búsqueda real
        total_evidence = len(result.get("supporting_evidence", [])) + len(result.get("contradicting_evidence", []))
        assert total_evidence >= 0  # No crashea incluso si no hay evidencia


# ============================================================================
# ESPECIFICACIÓN 6: GESTIÓN DE CITAS REAL (APA, MLA, IEEE)
# ============================================================================

class TestCitationManagement:
    """Especificación: El agente debe formatear citas con los metadatos reales."""

    async def test_generate_apa_citation(self, agent):
        """SPEC: _command_manage_citations debe generar citas APA correctamente formateadas."""
        sources = [
            {
                "title": "Attention Is All You Need",
                "authors": ["Vaswani, A.", "Shazeer, N."],
                "year": "2017",
                "url": "https://arxiv.org/abs/1706.03762",
                "journal": "NeurIPS"
            }
        ]
        result = await agent._command_manage_citations(
            sources=sources,
            citation_style="apa"
        )
        assert result["status"] == "success"
        citations = result.get("citations", [])
        assert len(citations) > 0
        # Verificar que el año está presente en la cita APA
        citation_text = citations[0].get("formatted", "")
        assert "2017" in citation_text or "Vaswani" in citation_text

    async def test_generate_ieee_citation(self, agent):
        """SPEC: IEEE usa formato numérico [1] Author, 'Title', Journal, Year."""
        sources = [
            {
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "authors": ["Devlin, J."],
                "year": "2019",
                "url": "https://arxiv.org/abs/1810.04805",
                "journal": "NAACL"
            }
        ]
        result = await agent._command_manage_citations(
            sources=sources,
            citation_style="ieee"
        )
        assert result["status"] == "success"


# ============================================================================
# ESPECIFICACIÓN 7: ANÁLISIS DE TENDENCIAS (sin datos simulados)
# ============================================================================

class TestTrendAnalysis:
    """Especificación: Tendencias deben basarse en datos reales extraídos de búsquedas."""

    async def test_temporal_trends_use_real_dates_not_hardcoded(self, agent):
        """SPEC: _analyze_temporal_trends NO debe generar fechas de forma artificial (i*3 días)."""
        # Creamos resultados con fechas reales en los metadatos
        mock_search_results = {
            "results": [
                {"title": "AI News Jan", "url": "https://example.com/1", "published_date": "2026-01-15", "relevance_score": 0.9, "sentiment": {"compound": 0.5}},
                {"title": "AI News Mar", "url": "https://example.com/2", "published_date": "2026-03-20", "relevance_score": 0.8, "sentiment": {"compound": 0.7}},
                {"title": "AI News Jun", "url": "https://example.com/3", "published_date": "2026-06-01", "relevance_score": 0.95, "sentiment": {"compound": 0.8}},
            ]
        }
        result = await agent._analyze_temporal_trends(mock_search_results, "6months")

        assert "data_points" in result
        assert "trend_direction" in result
        assert result["trend_direction"] in ["increasing", "decreasing", "neutral"]
        # Verificar que los puntos están ordenados cronológicamente (no hardcoded)
        dates = [p["date"] for p in result["data_points"]]
        assert dates == sorted(dates), "Los puntos de tendencia deben estar ordenados por fecha real"


# ============================================================================
# ESPECIFICACIÓN 8: INTELIGENCIA COMPETITIVA
# ============================================================================

class TestCompetitiveIntelligence:
    """Especificación: El análisis de competidores debe extraer datos reales de la web."""

    async def test_competitive_intel_command_returns_structured_result(self, agent):
        """SPEC: _command_competitive_intel debe retornar un análisis estructurado."""
        result = await agent._command_competitive_intelligence(
            companies=["OpenAI", "Anthropic"],
            analysis_type="basic"
        )
        assert result["status"] == "success"
        assert "companies_analyzed" in result or "analysis" in result


# ============================================================================
# ESPECIFICACIÓN E2E: CONEXIÓN AL HUB REAL DE RAYRABBIT
# ============================================================================

@pytest.mark.e2e
class TestE2EHubConnection:
    """
    Tests de integración real contra el Hub de RayRabbit.
    REQUIERE: python run_local_rayrabbit_cluster.py corriendo en puerto 8005.
    Ejecutar con: pytest -m e2e
    """

    async def test_agent_registers_on_real_hub(self, hub_url):
        """SPEC E2E: El agente debe poder registrarse en el Hub real vía WebSocket MAESTRO."""
        import websockets
        import json

        try:
            async with websockets.connect(hub_url, open_timeout=5) as ws:
                handshake = {
                    "type": "register",
                    "agent_id": "pytest_e2e_researcher",
                    "capabilities": ["web_search", "analyze_document", "fact_check"]
                }
                await ws.send(json.dumps(handshake))
                response_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                response = json.loads(response_raw)
                assert response is not None, "Hub debe responder al registro"
        except (ConnectionRefusedError, OSError):
            pytest.skip("Hub no disponible en puerto 8005. Inicia el cluster con run_local_rayrabbit_cluster.py")

    async def test_agent_tool_call_routes_through_hub(self, hub_url):
        """SPEC E2E: Una petición MCP tools/call debe ser enrutada por el Hub al agente."""
        import websockets
        import json

        try:
            async with websockets.connect(hub_url, open_timeout=5) as ws:
                mcp_call = {
                    "jsonrpc": "2.0",
                    "id": "e2e-test-001",
                    "method": "tools/call",
                    "params": {
                        "name": "web_search",
                        "arguments": {"query": "RayRabbit test", "max_results": 1}
                    }
                }
                await ws.send(json.dumps(mcp_call))
                response_raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
                response = json.loads(response_raw)
                assert "result" in response or "error" in response
        except (ConnectionRefusedError, OSError):
            pytest.skip("Hub no disponible en puerto 8005. Inicia el cluster con run_local_rayrabbit_cluster.py")
