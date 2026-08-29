# ResearcherAgent Enterprise

Agente especializado en investigación y análisis avanzado para el sistema RayRabbit Enterprise.

## 🚀 Características Principales

### Capacidades de Investigación
- **Búsqueda Web Avanzada**: Integración con múltiples APIs de búsqueda (Google, Bing, DuckDuckGo)
- **Análisis de Documentos**: Soporte para PDF, DOCX, TXT con análisis NLP completo
- **Verificación de Hechos**: Sistema automatizado de fact-checking con múltiples fuentes
- **Búsqueda Académica**: Integración con bases de datos académicas (arXiv, PubMed)
- **Extracción de Datos**: Patrones configurables para extracción de información estructurada
- **Análisis de Tendencias**: Detección y predicción de tendencias del mercado
- **Inteligencia Competitiva**: Análisis automatizado de competidores
- **Gestión de Citas**: Formateo automático en estilos APA, MLA, Chicago, IEEE

### Tecnologías Integradas
- **APIs de Búsqueda**: Google Search, Bing Search, DuckDuckGo
- **Procesamiento NLP**: NLTK, spaCy para análisis de texto
- **Análisis de Sentimiento**: VADER Sentiment Analysis
- **Bases de Datos Académicas**: arXiv, PubMed, Google Scholar
- **Extracción de PDFs**: PyPDF2 para análisis de documentos
- **Web Scraping**: BeautifulSoup para extracción de contenido web
- **Cache Inteligente**: Sistema de caché para optimizar rendimiento

## 📋 Requisitos

### Dependencias Python
```python
# Investigación web
aiohttp>=3.8.0
requests>=2.28.0
beautifulsoup4>=4.11.0

# Análisis de documentos
PyPDF2>=3.0.0
python-docx>=0.8.11

# Procesamiento de texto
nltk>=3.8
spacy>=3.5.0

# Utilidades
aiofiles>=22.0.0
```

### Variables de Entorno Requeridas
```bash
# APIs de Búsqueda (opcional pero recomendado)
GOOGLE_SEARCH_API_KEY=tu_google_api_key
GOOGLE_SEARCH_CX=tu_google_cx_id
BING_SEARCH_API_KEY=tu_bing_api_key

# APIs Académicas
PUBMED_EMAIL=tu_email@dominio.com
PUBMED_API_KEY=tu_pubmed_api_key
GOOGLE_SCHOLAR_API_KEY=tu_scholar_api_key
```

## 🛠️ Instalación

### Instalación Básica
```bash
# Clonar el repositorio
git clone <repository_url>
cd rayrabbit_enterprise/agents/researcher_agent

# Instalar dependencias
pip install -r requirements.txt

# Descargar recursos NLTK
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('vader_lexicon')"
```

### Instalación con spaCy
```bash
# Descargar modelo de spaCy para inglés
python -m spacy download en_core_web_sm

# Descargar modelo para español (opcional)
python -m spacy download es_core_news_sm
```

## 🚀 Uso Rápido

### Inicialización Básica
```python
from researcher_agent import ResearcherAgent

# Crear instancia del agente
agent = ResearcherAgent("my_researcher", "Mi Agente de Investigación")

# Realizar búsqueda web
results = await agent._web_search("inteligencia artificial tendencias 2024")
print(f"Encontrados {len(results['results'])} resultados")
```

### Análisis de Documento
```python
# Analizar documento
analysis = await agent._analyze_document("documento.pdf", "comprehensive")
print(f"Análisis completado: {analysis['analysis']['word_count']} palabras")
```

### Verificación de Hechos
```python
# Verificar afirmación
fact_check = await agent._fact_check("La IA reemplazará 85 millones de empleos para 2025")
print(f"Status: {fact_check['status']}, Confianza: {fact_check['confidence']:.2f}")
```

### Generación de Reportes
```python
# Datos para el reporte
data = {
    "analysis_date": "2024-11-04",
    "findings": ["Hallazgo 1", "Hallazgo 2"],
    "recommendations": ["Recomendación 1", "Recomendación 2"]
}

# Generar reporte
report = await agent._generate_report("executive_summary", data)
print(f"Reporte generado: {len(report['content'])} caracteres")
```

## 📚 Ejemplos Detallados

Ver el archivo `examples.py` para ejemplos completos de uso:

```python
import asyncio
from researcher_agent.examples import ResearcherAgentExamples

# Ejecutar ejemplo específico
asyncio.run(ResearcherAgentExamples.example_1_basic_web_search())

# Ejecutar todos los ejemplos
asyncio.run(ResearcherAgentExamples.run_all_examples())
```

## ⚙️ Configuración Avanzada

### Configuración Personalizada
```python
custom_config = {
    "research_mode": "deep",  # basic, comprehensive, deep
    "max_concurrent_searches": 10,
    "cache_enabled": True,
    "cache_duration_hours": 48,
    "fact_check_enabled": True,
    "academic_mode": True,
    "rate_limit_delay": 0.5,
    "max_sources_per_query": 15
}

agent = ResearcherAgent("advanced_researcher", config=custom_config)
```

### Configuración de APIs
```python
# El agente detecta automáticamente las APIs configuradas
# mediante variables de entorno

# Google Custom Search
export GOOGLE_SEARCH_API_KEY="tu_api_key"
export GOOGLE_SEARCH_CX="tu_cx_id"

# Bing Search
export BING_SEARCH_API_KEY="tu_api_key"

# Configuración manual en el código
agent.search_apis["google"]["enabled"] = True
agent.search_apis["bing"]["enabled"] = True
```

## 🔧 API Reference

### Métodos Principales

#### Búsqueda Web
```python
await agent._web_search(query, max_results=10, sources=None)
```
- `query`: Consulta de búsqueda
- `max_results`: Número máximo de resultados
- `sources`: Lista de fuentes a usar (duckduckgo, bing, google)

#### Análisis de Documentos
```python
await agent._analyze_document(file_path, analysis_type="comprehensive")
```
- `file_path`: Ruta al documento
- `analysis_type`: "basic" o "comprehensive"

#### Verificación de Hechos
```python
await agent._fact_check(claim, sources=None)
```
- `claim`: Afirmación a verificar
- `sources`: Fuentes específicas para verificar

#### Búsqueda Académica
```python
await agent._academic_search(query, databases=["arxiv", "pubmed"])
```
- `query`: Consulta académica
- `databases`: Bases de datos a consultar

#### Extracción de Datos
```python
await agent._extract_data(source, extraction_patterns)
```
- `source`: URL, archivo o texto
- `patterns`: Lista de patrones (emails, phones, urls, etc.)

#### Análisis de Tendencias
```python
await agent._trend_analysis(topic, timeframe="30d")
```
- `topic`: Tema a analizar
- `timeframe`: Período de análisis

#### Inteligencia Competitiva
```python
await agent._competitive_intelligence(company, analysis_type="overview")
```
- `company`: Nombre de la empresa
- `analysis_type`: "overview", "financial", "competitive_position"

#### Generación de Reportes
```python
await agent._generate_report(report_type, data)
```
- `report_type`: Tipo de reporte
- `data`: Datos para el reporte

#### Gestión de Citas
```python
await agent._manage_citations(action, citation_data)
```
- `action`: "add", "format", "validate", "export"
- `citation_data`: Datos de la cita

### Comandos Disponibles

```python
# Registro de comandos automatizado
await agent._command_web_search(query, max_results, sources)
await agent._command_analyze_document(file_path, analysis_type)
await agent._command_fact_check(claim, sources)
await agent._command_generate_report(report_type, data)
await agent._command_extract_data(source, patterns)
await agent._command_trend_analysis(topic, timeframe)
await agent._command_academic_search(query, databases)
await agent._command_manage_citations(action, citation_data)
await agent._command_competitive_intel(company, analysis_type)
await agent._command_clear_cache()
await agent._command_get_cache_stats()
```

## 📊 Capacidades del Agente

### Capacidades de Investigación
```python
capabilities = agent.get_research_capabilities()
print(capabilities)

# Resultado:
{
    "web_search": {
        "enabled": True,
        "supported_apis": ["google", "bing", "duckduckgo"],
        "max_results": 10
    },
    "document_analysis": {
        "supported_formats": [".pdf", ".docx", ".doc", ".txt"],
        "analysis_types": ["basic", "comprehensive"]
    },
    "fact_checking": {
        "enabled": True,
        "confidence_threshold": 0.6
    },
    "academic_search": {
        "enabled": True,
        "databases": ["arxiv", "pubmed"]
    },
    "data_extraction": {
        "patterns": ["emails", "phones", "urls", "dates", ...],
        "confidence_scoring": True
    },
    "report_generation": {
        "templates": ["executive_summary", "research_report", ...],
        "formats": ["markdown", "json"]
    },
    "cache": {
        "enabled": True,
        "duration_hours": 24
    }
}
```

### Estadísticas del Agente
```python
stats = agent.get_research_statistics()
print(stats)

# Resultado:
{
    "cache_entries": 25,
    "sources_configured": 3,
    "total_capabilities": 8,
    "uptime": "2024-11-04T07:04:39"
}
```

## 🔒 Seguridad y Privacidad

### Medidas de Seguridad
- **Sanitización de entrada**: Limpieza automática de datos de entrada
- **Filtrado de contenido sensible**: Detección automática de datos sensibles
- **Audit logging**: Registro completo de actividades
- **Compliance GDPR**: Cumplimiento con regulaciones de privacidad
- **Rate limiting**: Prevención de abuso de APIs

### Configuración de Seguridad
```python
security_config = {
    "max_file_size_mb": 50,
    "allowed_file_types": [".pdf", ".docx", ".doc", ".txt", ".md"],
    "blocked_domains": ["malware.com", "phishing.com"],
    "sanitize_input": True,
    "audit_logging": True,
    "gdpr_compliance": True,
    "data_retention_days": 90
}
```

## 🚨 Solución de Problemas

### Problemas Comunes

#### Error: "No module named 'nltk'"
```bash
pip install nltk
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

#### Error: "No se encontraron resultados de búsqueda"
```python
# Verificar configuración de APIs
print("APIs configuradas:", agent.search_apis)

# Usar DuckDuckGo como fallback (siempre disponible)
results = await agent._web_search("query", sources=["duckduckgo"])
```

#### Error: "Documento no encontrado"
```python
import os
file_path = "documento.pdf"

# Verificar que el archivo existe
if os.path.exists(file_path):
    analysis = await agent._analyze_document(file_path)
else:
    print(f"Error: Archivo {file_path} no encontrado")
```

#### Rendimiento lento
```python
# Ajustar configuración para mejor rendimiento
agent.config.update({
    "max_concurrent_searches": 5,  # Reducir concurrencia
    "rate_limit_delay": 2.0,      # Aumentar delay
    "cache_enabled": True          # Habilitar cache
})

# Limpiar cache si es necesario
await agent._command_clear_cache()
```

### Logs y Debugging
```python
import logging

# Habilitar logging detallado
logging.basicConfig(level=logging.DEBUG)

# El agente registra automáticamente todas las operaciones
# Revisar logs en: ./logs/researcher_agent.log
```

## 📈 Telemetría y Monitoreo

### Métricas Recopiladas
- Número de consultas de búsqueda
- Documentos analizados
- Hechos verificados
- Reportes generados
- Hits de caché
- Llamadas a APIs
- Tiempo de procesamiento

### Exportación de Datos
```python
# Exportar datos de telemetría
telemetry_data = await agent.export_research_data("json")

# Estadísticas del agente
stats = agent.get_research_statistics()
```

## 🤝 Integración con RayRabbit

### Registro Automático
El ResearcherAgent se registra automáticamente en:
- **MessageBus Enterprise**: Para comunicación entre agentes
- **MAESTRO Security**: Para autenticación y autorización
- **Canvas Workflows**: Para integración con interfaces de usuario
- **Discovery Automático**: Para detección de capacidades

### Ejemplo de Integración
```python
from rayrabbit.communication.message import Message, MessageType

# Crear mensaje de investigación
message = Message(
    sender_id="user_001",
    sender_name="User",
    recipient_id=agent.id,
    recipient_name=agent.name,
    message_type=MessageType.REQUEST,
    content={"text": "investigar tendencias en IA"}
)

# Procesar mensaje
response = await agent.process_message(message)
```

## 📝 Licencia

Este proyecto está licenciado bajo los términos especificados en el archivo de licencia del sistema RayRabbit Enterprise.

## 👥 Contribuciones

Para contribuir al ResearcherAgent:

1. Fork del repositorio
2. Crear branch de feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit de cambios (`git commit -am 'Añadir nueva característica'`)
4. Push al branch (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## 📞 Soporte

Para soporte técnico:

- **Documentación**: [docs.researcher-agent.com](https://docs.researcher-agent.com)
- **Issues**: GitHub Issues
- **Email**: support@rayrabbit.com
- **Slack**: #researcher-agent-support

## 🗺️ Roadmap

### Próximas Versiones
- **v1.1**: Soporte para análisis de imágenes
- **v1.2**: Integración con más bases de datos académicas
- **v1.3**: Análisis predictivo avanzado
- **v1.4**: Soporte multiidioma expandido
- **v1.5**: API GraphQL

### Características Planificadas
- Análisis de sentimientos en tiempo real
- Detección de fake news
- Integración con redes sociales
- Análisis de patentes
- Monitor de competidores en tiempo real

---

**Desarrollado por RayRabbit Enterprise v1.0.0**

Para más información, visite [rayrabbit.com](https://rayrabbit.com)
