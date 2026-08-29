"""
Ejemplos de Uso del ResearcherAgent Enterprise

Este módulo contiene ejemplos prácticos de cómo utilizar el ResearcherAgent
para diferentes tipos de investigación y análisis.

Autor: RayRabbit Enterprise
Versión: 1.0.0
"""

import asyncio
import json
from typing import Dict, Any
from researcher_agent import ResearcherAgent


class ResearcherAgentExamples:
    """Clase con ejemplos de uso del ResearcherAgent."""
    
    @staticmethod
    async def example_1_basic_web_search():
        """Ejemplo 1: Búsqueda web básica."""
        print("=== EJEMPLO 1: BÚSQUEDA WEB BÁSICA ===")
        
        # Crear instancia del agente
        agent = ResearcherAgent("researcher_01", "Basic Research Agent")
        
        # Realizar búsqueda web
        query = "artificial intelligence trends 2024"
        results = await agent._web_search(query, max_results=5)
        
        print(f"Búsqueda realizada: {query}")
        print(f"Resultados encontrados: {len(results['results'])}")
        print("\nPrimer resultado:")
        if results['results']:
            first_result = results['results'][0]
            print(f"Título: {first_result.get('title')}")
            print(f"URL: {first_result.get('url')}")
            print(f"Fragmento: {first_result.get('snippet', '')[:100]}...")
            print(f"Score de confianza: {first_result.get('trust_score', 0):.2f}")
        
        return results
    
    @staticmethod
    async def example_2_document_analysis():
        """Ejemplo 2: Análisis de documento."""
        print("\n=== EJEMPLO 2: ANÁLISIS DE DOCUMENTO ===")
        
        agent = ResearcherAgent("researcher_02", "Document Analyst")
        
        # Simular análisis de documento (en un caso real, usarías un archivo real)
        sample_content = """
        Artificial Intelligence in Healthcare: A Comprehensive Review
        
        This paper examines the current state of artificial intelligence in healthcare applications.
        The study analyzes 150 research papers published between 2020-2024.
        
        Key findings include:
        - AI accuracy in diagnostic tasks reaches 95% in radiology
        - Machine learning models reduce diagnosis time by 60%
        - Investment in healthcare AI reached $6.6 billion in 2023
        
        Methodology:
        We conducted a systematic review of peer-reviewed publications.
        Data was extracted using standardized protocols.
        
        Limitations include limited long-term outcome data.
        Future research should focus on ethical considerations.
        """
        
        # Analizar el contenido simulado
        analysis = agent._basic_document_analysis(sample_content)
        
        print("Análisis del documento:")
        print(f"Número de palabras: {analysis['word_count']}")
        print(f"Número de oraciones: {analysis['sentence_count']}")
        print(f"Score de legibilidad: {analysis['readability_score']:.2f}")
        print(f"Palabras clave principales: {analysis['top_keywords'][:5]}")
        
        # Análisis de sentimiento
        sentiment = analysis['sentiment']
        print(f"\nAnálisis de sentimiento:")
        print(f"Compuesto: {sentiment['compound']:.3f}")
        print(f"Positivo: {sentiment['pos']:.3f}")
        print(f"Neutral: {sentiment['neu']:.3f}")
        print(f"Negativo: {sentiment['neg']:.3f}")
        
        return analysis
    
    @staticmethod
    async def example_3_fact_checking():
        """Ejemplo 3: Verificación de hechos."""
        print("\n=== EJEMPLO 3: VERIFICACIÓN DE HECHOS ===")
        
        agent = ResearcherAgent("researcher_03", "Fact Checker Agent")
        
        # Afirmación a verificar
        claim = "Artificial intelligence will replace 85 million jobs by 2025 according to World Economic Forum"
        
        # Realizar verificación
        fact_check = await agent._fact_check(claim)
        
        print(f"Afirmación verificada: {claim}")
        print(f"Status: {fact_check['status']}")
        print(f"Confianza: {fact_check['confidence']:.2f}")
        
        print(f"\nEvidencia a favor ({len(fact_check['supporting_evidence'])} fuentes):")
        for evidence in fact_check['supporting_evidence']:
            print(f"- {evidence['source'][:50]}... (confianza: {evidence['trust_score']:.2f})")
        
        print(f"\nEvidencia en contra ({len(fact_check['contradicting_evidence'])} fuentes):")
        for evidence in fact_check['contradicting_evidence']:
            print(f"- {evidence['source'][:50]}... (confianza: {evidence['trust_score']:.2f})")
        
        return fact_check
    
    @staticmethod
    async def example_4_academic_search():
        """Ejemplo 4: Búsqueda académica."""
        print("\n=== EJEMPLO 4: BÚSQUEDA ACADÉMICA ===")
        
        agent = ResearcherAgent("researcher_04", "Academic Research Agent")
        
        # Consulta académica
        query = "machine learning healthcare applications"
        databases = ["arxiv", "pubmed"]
        
        # Realizar búsqueda académica
        results = await agent._academic_search(query, databases)
        
        print(f"Búsqueda académica: {query}")
        print(f"Bases de datos consultadas: {databases}")
        
        # Mostrar resultados de arXiv
        if "arxiv" in results:
            arxiv_results = results["arxiv"]
            print(f"\nResultados de arXiv ({len(arxiv_results)} papers):")
            for i, paper in enumerate(arxiv_results[:3], 1):
                print(f"{i}. {paper.get('title', 'Sin título')}")
                print(f"   Autores: {', '.join(paper.get('authors', [])[:3])}...")
                print(f"   Publicado: {paper.get('published', 'N/A')}")
        
        # Mostrar resultados de PubMed
        if "pubmed" in results:
            pubmed_results = results["pubmed"]
            print(f"\nResultados de PubMed ({len(pubmed_results)} papers):")
            for i, paper in enumerate(pubmed_results[:2], 1):
                print(f"{i}. {paper.get('title', 'Sin título')}")
                print(f"   Journal: {paper.get('journal', 'N/A')}")
                print(f"   Año: {paper.get('year', 'N/A')}")
        
        return results
    
    @staticmethod
    async def example_5_data_extraction():
        """Ejemplo 5: Extracción de datos."""
        print("\n=== EJEMPLO 5: EXTRACCIÓN DE DATOS ===")
        
        agent = ResearcherAgent("researcher_05", "Data Extraction Agent")
        
        # Texto de ejemplo con datos para extraer
        sample_text = """
        Contact Information:
        Email: juan.perez@empresa.com
        Phone: (555) 123-4567
        Website: https://www.empresa.com
        
        Address:
        123 Main Street
        Austin, Texas 78701
        
        Company Details:
        Founded in 2015, TechCorp Inc. generated $2.5 million in revenue last year.
        The company has grown by 25% annually and employs 150 people.
        CEO John Smith announced plans for 30% growth this year.
        
        Key Statistics:
        - Customer satisfaction: 94%
        - Market share: 12.5%
        - Profit margin: 18.3%
        
        Founded: January 15, 2015
        """
        
        # Patrones de extracción
        patterns = ["emails", "phones", "urls", "addresses", "monetary_values", "percentages", "companies", "dates"]
        
        # Extraer datos
        extracted_data = await agent._extract_data(sample_text, patterns)
        
        print("Datos extraídos:")
        for pattern, values in extracted_data.items():
            if values:
                print(f"\n{pattern.upper()}:")
                for value in values:
                    print(f"  - {value}")
        
        print(f"\nConfianza general de extracción: {extracted_data.get('confidence_score', 0):.2f}")
        
        return extracted_data
    
    @staticmethod
    async def example_6_trend_analysis():
        """Ejemplo 6: Análisis de tendencias."""
        print("\n=== EJEMPLO 6: ANÁLISIS DE TENDENCIAS ===")
        
        agent = ResearcherAgent("researcher_06", "Trend Analysis Agent")
        
        # Análisis de tendencias
        topic = "artificial intelligence adoption"
        timeframe = "12 months"
        
        trends = await agent._trend_analysis(topic, timeframe)
        
        print(f"Análisis de tendencias: {topic}")
        print(f"Período analizado: {timeframe}")
        
        # Mostrar datos de tendencias
        trend_data = trends.get("trend_data", {})
        print(f"\nDirección de tendencia: {trend_data.get('trend_direction', 'N/A')}")
        print(f"Volatilidad: {trend_data.get('volatility', 0):.2f}")
        
        # Análisis de sentimiento
        sentiment = trends.get("sentiment_analysis", {})
        print(f"\nSentimiento promedio: {sentiment.get('average_sentiment', 0):.3f}")
        print(f"Tendencia de sentimiento: {sentiment.get('sentiment_trend', 'N/A')}")
        
        # Predicciones
        predictions = trends.get("predictions", {})
        if predictions:
            print(f"\nPredicción próxima semana: {predictions.get('next_week', {}).get('expected_volume', 'N/A')}")
            print(f"Confianza predicción: {predictions.get('next_week', {}).get('confidence', 0):.2f}")
        
        # Insights clave
        insights = trends.get("key_insights", [])
        print(f"\nInsights clave:")
        for insight in insights:
            print(f"  - {insight}")
        
        return trends
    
    @staticmethod
    async def example_7_competitive_intelligence():
        """Ejemplo 7: Inteligencia competitiva."""
        print("\n=== EJEMPLO 7: INTELIGENCIA COMPETITIVA ===")
        
        agent = ResearcherAgent("researcher_07", "Competitive Intelligence Agent")
        
        # Análisis competitivo
        company = "OpenAI"
        analysis_type = "overview"
        
        intel = await agent._competitive_intelligence(company, analysis_type)
        
        print(f"Análisis competitivo: {company}")
        print(f"Tipo de análisis: {analysis_type}")
        
        # Datos de inteligencia
        intel_data = intel.get("intelligence_data", {})
        print(f"\nDescripción del negocio: {intel_data.get('business_description', 'N/A')[:100]}...")
        
        # Análisis FODA
        swot = intel.get("swot_analysis", {})
        print(f"\nFortalezas identificadas ({len(swot.get('strengths', []))}):")
        for strength in swot.get('strengths', [])[:3]:
            print(f"  - {strength[:80]}...")
        
        print(f"\nOportunidades identificadas ({len(swot.get('opportunities', []))}):")
        for opportunity in swot.get('opportunities', [])[:3]:
            print(f"  - {opportunity[:80]}...")
        
        # Recomendaciones
        recommendations = intel.get("recommendations", [])
        print(f"\nRecomendaciones ({len(recommendations)}):")
        for rec in recommendations[:3]:
            print(f"  - {rec}")
        
        return intel
    
    @staticmethod
    async def example_8_report_generation():
        """Ejemplo 8: Generación de reportes."""
        print("\n=== EJEMPLO 8: GENERACIÓN DE REPORTES ===")
        
        agent = ResearcherAgent("researcher_08", "Report Generation Agent")
        
        # Datos para el reporte
        report_data = {
            "analysis_date": "2024-11-04",
            "findings": [
                "La adopción de IA creció 40% en 2024",
                "Las startups de IA recaudaron $25 mil millones",
                "Los modelos de lenguaje muestran mejoras significativas"
            ],
            "conclusions": [
                "La IA está en fase de madurez temprana",
                "Se requiere mayor regulación",
                "La inversión continuará creciendo"
            ],
            "recommendations": [
                "Invertir en infraestructura de IA",
                "Desarrollar marcos regulatorios",
                "Fomentar la investigación académica"
            ],
            "metrics": {
                "growth_rate": "40%",
                "investment_volume": "$25B",
                "market_size": "$150B"
            }
        }
        
        # Generar reporte
        report = await agent._generate_report("executive_summary", report_data)
        
        print("Reporte generado:")
        print(f"Tipo: {report['report_type']}")
        print(f"Generado: {report['generated_at']}")
        
        # Mostrar una parte del contenido
        content = report['content']
        lines = content.split('\n')[:20]  # Primeras 20 líneas
        print(f"\nContenido del reporte (primeras 20 líneas):")
        for line in lines:
            print(line)
        
        return report
    
    @staticmethod
    async def example_9_citation_management():
        """Ejemplo 9: Gestión de citas."""
        print("\n=== EJEMPLO 9: GESTIÓN DE CITAS ===")
        
        agent = ResearcherAgent("researcher_09", "Citation Manager Agent")
        
        # Datos de cita de ejemplo
        citation_data = {
            "author": "Smith, John A.",
            "title": "Artificial Intelligence in Modern Healthcare",
            "journal": "Journal of Medical AI",
            "year": 2024,
            "volume": "15",
            "issue": "3",
            "pages": "45-67",
            "doi": "10.1234/jmai.2024.001"
        }
        
        # Formatear cita en diferentes estilos
        styles = ["apa", "mla", "chicago", "ieee"]
        
        print("Formateo de citas en diferentes estilos:")
        for style in styles:
            citation_data["style"] = style
            try:
                formatted = await agent._manage_citations("format", citation_data)
                print(f"\n{style.upper()}:")
                print(f"  {formatted['formatted']}")
            except Exception as e:
                print(f"Error en {style}: {e}")
        
        # Validar cita
        validation = await agent._manage_citations("validate", citation_data)
        print(f"\nValidación de cita:")
        print(f"Válida: {validation['is_valid']}")
        print(f"Advertencias: {validation.get('warnings', [])}")
        print(f"Sugerencias: {validation.get('suggestions', [])}")
        
        return citation_data
    
    @staticmethod
    async def example_10_comprehensive_research():
        """Ejemplo 10: Investigación comprehensiva completa."""
        print("\n=== EJEMPLO 10: INVESTIGACIÓN COMPREHENSIVA ===")
        
        agent = ResearcherAgent("researcher_10", "Comprehensive Research Agent")
        
        # Tema de investigación
        research_topic = "machine learning ethics in healthcare"
        
        print(f"Investigación comprehensiva sobre: {research_topic}")
        print("=" * 60)
        
        # 1. Búsqueda web
        print("1. Realizando búsqueda web...")
        web_results = await agent._web_search(f"{research_topic} ethics guidelines", max_results=10)
        print(f"   Encontrados {len(web_results['results'])} resultados web")
        
        # 2. Búsqueda académica
        print("2. Realizando búsqueda académica...")
        academic_results = await agent._academic_search(research_topic)
        total_papers = sum(len(results) for results in academic_results.values())
        print(f"   Encontrados {total_papers} papers académicos")
        
        # 3. Análisis de tendencias
        print("3. Analizando tendencias...")
        trend_analysis = await agent._trend_analysis("AI ethics healthcare", "6 months")
        print(f"   Tendencia detectada: {trend_analysis['trend_data']['trend_direction']}")
        
        # 4. Fact checking de afirmaciones clave
        print("4. Verificando hechos clave...")
        claims_to_check = [
            "AI in healthcare improves patient outcomes by 25%",
            "85% of healthcare AI projects fail to deploy"
        ]
        
        fact_checks = []
        for claim in claims_to_check:
            fact_check = await agent._fact_check(claim)
            fact_checks.append({
                "claim": claim,
                "status": fact_check['status'],
                "confidence": fact_check['confidence']
            })
            print(f"   - '{claim}': {fact_check['status']} ({fact_check['confidence']:.2f})")
        
        # 5. Generación de reporte final
        print("5. Generando reporte comprehensivo...")
        comprehensive_data = {
            "research_topic": research_topic,
            "web_sources_count": len(web_results['results']),
            "academic_papers_count": total_papers,
            "trend_direction": trend_analysis['trend_data']['trend_direction'],
            "fact_checks": fact_checks,
            "key_findings": [
                f"Identificadas {len(web_results['results'])} fuentes web relevantes",
                f"Encontrados {total_papers} papers académicos sobre el tema",
                f"Tendencia general: {trend_analysis['trend_data']['trend_direction']}",
                f"Verificadas {len(fact_checks)} afirmaciones clave"
            ],
            "recommendations": [
                "Continuar monitoreo de desarrollos en IA ética",
                "Revisar regularmente las guías de implementación",
                "Establecer comités de ética para proyectos de IA"
            ]
        }
        
        final_report = await agent._generate_report("research_report", comprehensive_data)
        
        print("\nINVESTIGACIÓN COMPLETADA")
        print(f"Reporte final generado: {len(final_report['content'])} caracteres")
        print("=" * 60)
        
        return final_report


async def run_all_examples():
    """Ejecuta todos los ejemplos de uso."""
    print("EJEMPLOS DE USO DEL RESEARCHERAGENT ENTERPRISE")
    print("=" * 60)
    
    examples = [
        ResearcherAgentExamples.example_1_basic_web_search,
        ResearcherAgentExamples.example_2_document_analysis,
        ResearcherAgentExamples.example_3_fact_checking,
        ResearcherAgentExamples.example_4_academic_search,
        ResearcherAgentExamples.example_5_data_extraction,
        ResearcherAgentExamples.example_6_trend_analysis,
        ResearcherAgentExamples.example_7_competitive_intelligence,
        ResearcherAgentExamples.example_8_report_generation,
        ResearcherAgentExamples.example_9_citation_management,
        ResearcherAgentExamples.example_10_comprehensive_research
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            await example()
            print("\n" + "=" * 60)
            if i < len(examples):
                input("Presiona Enter para continuar al siguiente ejemplo...")
        except Exception as e:
            print(f"Error en ejemplo {i}: {e}")
    
    print("\n¡Todos los ejemplos completados!")


async def run_specific_example(example_number: int):
    """Ejecuta un ejemplo específico."""
    examples = {
        1: ResearcherAgentExamples.example_1_basic_web_search,
        2: ResearcherAgentExamples.example_2_document_analysis,
        3: ResearcherAgentExamples.example_3_fact_checking,
        4: ResearcherAgentExamples.example_4_academic_search,
        5: ResearcherAgentExamples.example_5_data_extraction,
        6: ResearcherAgentExamples.example_6_trend_analysis,
        7: ResearcherAgentExamples.example_7_competitive_intelligence,
        8: ResearcherAgentExamples.example_8_report_generation,
        9: ResearcherAgentExamples.example_9_citation_management,
        10: ResearcherAgentExamples.example_10_comprehensive_research
    }
    
    if example_number in examples:
        await examples[example_number]()
    else:
        print(f"Ejemplo {example_number} no encontrado. Ejemplos disponibles: 1-10")


# ========================================================================
# EJEMPLO DE INTEGRACIÓN CON EL FRAMEWORK RAYRABBIT
# ========================================================================

async def example_integration_with_rayrabbit():
    """Ejemplo de integración con el framework RayRabbit."""
    print("EJEMPLO DE INTEGRACIÓN CON RAYRABBIT")
    print("=" * 50)
    
    # Crear instancia del agente
    researcher_agent = ResearcherAgent("enterprise_researcher", "Enterprise Research Specialist")
    
    # Simular recepción de mensaje de investigación
    from rayrabbit.communication.message import Message, MessageType
    
    # Mensaje de ejemplo
    message_content = {
        "text": "investigar tendencias en inteligencia artificial para 2024"
    }
    
    message = Message(
        sender_id="user_001",
        sender_name="User Request",
        recipient_id=researcher_agent.id,
        recipient_name=researcher_agent.name,
        message_type=MessageType.REQUEST,
        content=message_content
    )
    
    # Procesar mensaje
    response = await researcher_agent.process_message(message)
    
    if response:
        print("Mensaje procesado exitosamente:")
        print(f"Respuesta para: {response.recipient_id}")
        print(f"Tipo de respuesta: {response.message_type}")
        
        # Mostrar resultados de investigación
        if isinstance(response.content, dict):
            print(f"Query investigada: {response.content.get('query', 'N/A')}")
            print(f"Tipo de investigación: {response.content.get('research_type', 'N/A')}")
            
            results = response.content.get('results', {})
            if 'results' in results:
                print(f"Resultados encontrados: {len(results['results'])}")
    else:
        print("No se recibió respuesta")
    
    return researcher_agent


# ========================================================================
# EJEMPLO DE CONFIGURACIÓN AVANZADA
# ========================================================================

def example_advanced_configuration():
    """Ejemplo de configuración avanzada del agente."""
    print("CONFIGURACIÓN AVANZADA DEL RESEARCHERAGENT")
    print("=" * 50)
    
    # Configuración personalizada
    custom_config = {
        "research_mode": "deep",
        "max_concurrent_searches": 10,
        "cache_enabled": True,
        "cache_duration_hours": 48,
        "fact_check_enabled": True,
        "academic_mode": True,
        "rate_limit_delay": 0.5,
        "max_sources_per_query": 15
    }
    
    # Crear agente con configuración personalizada
    agent = ResearcherAgent(
        "advanced_researcher", 
        "Advanced Research Agent",
        config=custom_config
    )
    
    # Mostrar capacidades
    capabilities = agent.get_research_capabilities()
    print("Capacidades del agente:")
    print(f"- Búsqueda web: {'Habilitada' if capabilities['web_search']['enabled'] else 'Deshabilitada'}")
    print(f"- APIs configuradas: {len(capabilities['web_search']['supported_apis'])}")
    print(f"- Análisis de documentos: {len(capabilities['document_analysis']['supported_formats'])} formatos")
    print(f"- Verificación de hechos: {'Habilitada' if capabilities['fact_checking']['enabled'] else 'Deshabilitada'}")
    print(f"- Búsqueda académica: {'Habilitada' if capabilities['academic_search']['enabled'] else 'Deshabilitada'}")
    
    # Estadísticas
    stats = agent.get_research_statistics()
    print(f"\nEstadísticas del agente:")
    print(f"- Entradas en cache: {stats['cache_entries']}")
    print(f"- APIs configuradas: {stats['sources_configured']}")
    print(f"- Capacidades totales: {stats['total_capabilities']}")
    
    return agent


if __name__ == "__main__":
    # Ejecutar ejemplos
    import sys
    
    if len(sys.argv) > 1:
        try:
            example_num = int(sys.argv[1])
            asyncio.run(run_specific_example(example_num))
        except ValueError:
            print("Uso: python examples.py [1-10]")
    else:
        asyncio.run(run_all_examples())
