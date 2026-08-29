"""
ResearcherAgent Enterprise - Agente de Investigación y Análisis Avanzado

Agente especializado en investigación automatizada que proporciona capacidades
avanzadas de búsqueda web, análisis de documentos, minería de datos, gestión
de citas, generación de reportes y verificación de facts.

Autor: RayRabbit Enterprise
Versión: 1.0.0
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env de forma dinámica (acumulativa de abajo hacia arriba)
def _load_env_file():
    current = Path(__file__).resolve().parent
    for _ in range(10):
        dotenv_path = current / ".env"
        if dotenv_path.exists():
            load_dotenv(dotenv_path)
        if (current / "pyproject.toml").exists():
            break
        current = current.parent
    else:
        load_dotenv()

_load_env_file()

import re
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from urllib.parse import urljoin, urlparse
import logging

# Imports para investigación web
import aiohttp
import requests
from bs4 import BeautifulSoup
import aiofiles

# Imports para análisis de documentos
from pypdf import PdfReader
import docx
from docx import Document

# Imports para NLP y análisis de texto
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Imports para bases de datos académicas
import arxiv
import pubmedpy

# Imports del framework RayRabbit SDK
from rayrabbit_client.node import RayRabbitNode
from rayrabbit_client.message import Message, MessageType

# Descargar recursos NLTK si no están disponibles
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')


class ResearcherAgent(RayRabbitNode):
    """
    Agente de Investigación Enterprise con capacidades avanzadas de análisis.
    """
    
    def __init__(self, agent_id: str, name: str = "ResearcherAgent", hub_url: str = "ws://localhost:8005/ws", **kwargs):
        """
        Inicializa el Researcher Agent con capacidades de investigación.
        """
        super().__init__(name=name, hub_url=hub_url)
        self.agent_id = agent_id
        
        # Configuración específica del Researcher Agent
        self.config = {
            "research_mode": "comprehensive",  # basic, comprehensive, deep
            "max_concurrent_searches": 5,
            "cache_enabled": True,
            "cache_duration_hours": 24,
            "fact_check_enabled": True,
            "academic_mode": True,
            "rate_limit_delay": 1.0,  # segundos entre búsquedas
            "max_sources_per_query": 10,
            "report_template": "default"
        }
        self.config.update(kwargs)
        
        # Inicializar componentes
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Cache interno para resultados
        self._research_cache = {}
        self._source_trust_scores = {}
        
        # APIs de búsqueda configurables
        self.search_apis = {
            "google": {
                "enabled": False,  # Requiere API key
                "api_key": os.getenv("GOOGLE_SEARCH_API_KEY"),
                "cx": os.getenv("GOOGLE_SEARCH_CX")
            },
            "bing": {
                "enabled": os.getenv("BING_SEARCH_API_KEY") is not None,
                "api_key": os.getenv("BING_SEARCH_API_KEY")
            },
            "duckduckgo": {
                "enabled": True,
                "rate_limit": 10  # requests per minute
            }
        }
        
        # Registrar comandos especializados vía decorador dinámico
        self._register_research_commands()
        
        self.logger.info(f"ResearcherAgent inicializado con ID: {agent_id}")
    
    def _register_research_commands(self):
        """Registra comandos especializados de investigación."""
        self.register_tool(self._command_web_search, "web_search", "Búsqueda web avanzada")
        self.register_tool(self._command_analyze_document, "analyze_document", "Análisis de documentos NLP")
        self.register_tool(self._command_fact_check, "fact_check", "Verificación de hechos automática")
        self.register_tool(self._command_generate_report, "generate_report", "Generación de reportes académicos")
        self.register_tool(self._command_extract_data, "extract_data", "Extracción de datos estructurada")
        self.register_tool(self._command_trend_analysis, "trend_analysis", "Análisis de tendencias VADER")
        self.register_tool(self._command_academic_search, "academic_search", "Búsqueda en bases de datos académicas (arXiv)")
        self.register_tool(self._command_manage_citations, "manage_citations", "Gestión de citas APA/MLA")
        self.register_tool(self._command_competitive_intelligence, "competitive_intel", "Inteligencia competitiva automatizada")
        self.register_tool(self._command_clear_cache, "clear_cache", "Limpiar cache interno")
        self.register_tool(self._command_get_cache_stats, "get_cache_stats", "Estadísticas de caché")
    
    async def _command_web_search(self, query: str, max_results: int = 10, sources: List[str] = None) -> Dict[str, Any]:
        """Comando para búsqueda web avanzada."""
        try:
            results = await self._web_search(query, max_results, sources)
            
            # --- Integración Real con LLM ---
            self.logger.info("Enviando resultados al LLM para síntesis...")
            synthesis = await self._synthesize_with_llm(query, json.dumps(results.get("results", [])[:3]))
            
            return {
                "status": "success",
                "query": query,
                "synthesis": synthesis,
                "results_count": len(results.get("results", [])),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error en búsqueda web: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _command_analyze_document(self, file_path: str = None, content: str = None, analysis_type: str = "comprehensive", document_type: str = "file") -> Dict[str, Any]:
        """Comando para análisis de documentos. Acepta file_path o content directo."""
        try:
            if content and not file_path:
                # Análisis directo de texto plano sin archivo
                analysis = self._basic_document_analysis(content)
            elif file_path:
                analysis = await self._analyze_document(file_path, analysis_type)
            else:
                return {"status": "error", "message": "Se requiere file_path o content"}
            return {
                "status": "success",
                "file_path": file_path,
                "analysis_type": analysis_type,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error en análisis de documento: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _command_fact_check(self, claim: str, sources: List[str] = None) -> Dict[str, Any]:
        """Comando para verificación de hechos."""
        try:
            fact_check = await self._fact_check(claim, sources)
            return {
                "status": "success",
                "claim": claim,
                "fact_check": fact_check,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error en verificación de hechos: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _command_generate_report(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comando para generación de reportes."""
        try:
            report = await self._generate_report(report_type, data)
            return {
                "status": "success",
                "report_type": report_type,
                "report": report,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error en generación de reporte: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _command_extract_data(self, source: str = None, content: str = None, extraction_patterns: List[str] = None, patterns: List[str] = None) -> Dict[str, Any]:
        """Comando para extracción de datos. Acepta source (URL/path) o content (texto directo)."""
        try:
            # Normalizar alias: patterns -> extraction_patterns
            active_patterns = patterns or extraction_patterns or []
            active_source = content or source or ""
            extracted_data = await self._extract_data(active_source, active_patterns)
            return {
                "status": "success",
                "source": source,
                "patterns": active_patterns,
                "extracted_data": extracted_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error en extracción de datos: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _command_trend_analysis(self, topic: str, timeframe: str = "30d") -> Dict[str, Any]:
        """Comando para análisis de tendencias."""
        try:
            trends = await self._trend_analysis(topic, timeframe)
            return {
                "status": "success",
                "topic": topic,
                "timeframe": timeframe,
                "trends": trends,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error en análisis de tendencias: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _command_academic_search(self, query: str, databases: List[str] = None) -> Dict[str, Any]:
        """Comando para búsqueda académica."""
        try:
            results = await self._academic_search(query, databases)
            return {
                "status": "success",
                "query": query,
                "databases": databases or ["arxiv", "pubmed"],
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error en búsqueda académica: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _command_manage_citations(self, action: str = "format", citation_data: Dict[str, Any] = None, sources: List[Dict] = None, citation_style: str = "apa") -> Dict[str, Any]:
        """Comando para gestión de citas. Acepta formato ergonómico (sources + citation_style) o el legado (action + citation_data)."""
        try:
            if sources is not None:
                # Interfaz moderna: formatear lista de fuentes directamente
                citations = []
                for src in sources:
                    formatted = await self._format_citation({"source": src, "style": citation_style})
                    citations.append(formatted)
                return {
                    "status": "success",
                    "citation_style": citation_style,
                    "citations": citations,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Interfaz legado
                result = await self._manage_citations(action, citation_data or {})
                return {
                    "status": "success",
                    "action": action,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error en gestión de citas: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _command_competitive_intelligence(self, company: str = None, companies: List[str] = None, analysis_type: str = "overview") -> Dict[str, Any]:
        """Comando para inteligencia competitiva. Acepta una empresa o lista."""
        try:
            # Normalizar: companies list -> iterar por cada empresa
            targets = companies if companies else ([company] if company else [])
            if not targets:
                return {"status": "error", "message": "Se requiere company o companies"}
            
            all_intel = {}
            for target in targets:
                intel = await self._competitive_intelligence(target, analysis_type)
                all_intel[target] = intel
            
            return {
                "status": "success",
                "companies_analyzed": targets,
                "analysis_type": analysis_type,
                "analysis": all_intel,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error en inteligencia competitiva: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _command_clear_cache(self) -> Dict[str, Any]:
        """Comando para limpiar cache."""
        self._research_cache.clear()
        self.logger.info("Cache de investigación limpiado")
        return {"status": "success", "message": "Cache limpiado correctamente"}
    
    async def _command_get_cache_stats(self) -> Dict[str, Any]:
        """Comando para obtener estadísticas del cache."""
        total_entries = len(self._research_cache)
        cache_size_mb = len(json.dumps(self._research_cache).encode('utf-8')) / (1024 * 1024)
        
        return {
            "status": "success",
            "stats": {
                "total_entries": total_entries,
                "cache_size_mb": round(cache_size_mb, 2),
                "enabled": self.config.get("cache_enabled", True)
            }
        }
    
    # ========================================================================
    # MÉTODOS PRINCIPALES DE INVESTIGACIÓN
    # ========================================================================
    
    async def _web_search(self, query: str, max_results: int = 10, sources: List[str] = None) -> Dict[str, Any]:
        """
        Realiza búsqueda web utilizando múltiples fuentes.
        """
        cache_key = f"web_search_{hashlib.md5(query.encode()).hexdigest()}_{max_results}"
        
        # Verificar cache
        if self.config.get("cache_enabled") and cache_key in self._research_cache:
            cache_entry = self._research_cache[cache_key]
            if datetime.now() - cache_entry["timestamp"] < timedelta(hours=self.config.get("cache_duration_hours", 24)):
                self.logger.info(f"Retornando resultado desde cache para: {query}")
                return cache_entry["data"]
        
        sources = sources or list(self.search_apis.keys())
        all_results = []
        
        for source in sources:
            if self.search_apis.get(source, {}).get("enabled", False):
                try:
                    if source == "duckduckgo":
                        results = await self._search_duckduckgo(query, max_results)
                    elif source == "bing":
                        results = await self._search_bing(query, max_results)
                    elif source == "google":
                        results = await self._search_google(query, max_results)
                    
                    all_results.extend(results)
                    
                    # Rate limiting
                    await asyncio.sleep(self.config.get("rate_limit_delay", 1.0))
                    
                except Exception as e:
                    self.logger.warning(f"Error en búsqueda {source}: {e}")
                    continue
        
        # Eliminar duplicados y limitar resultados
        unique_results = self._deduplicate_results(all_results)
        final_results = unique_results[:max_results]
        
        # Enriquecer resultados con análisis de contenido
        enriched_results = []
        for result in final_results:
            try:
                enriched = await self._enrich_search_result(result)
                enriched_results.append(enriched)
            except Exception as e:
                self.logger.warning(f"Error enriqueciendo resultado: {e}")
                enriched_results.append(result)
        
        result_data = {
            "query": query,
            "results": enriched_results,
            "results_count": len(enriched_results),
            "total_sources": len(sources),
            "sources_searched": [s for s in sources if self.search_apis.get(s, {}).get("enabled", False)]
        }
        
        # Guardar en cache
        if self.config.get("cache_enabled"):
            self._research_cache[cache_key] = {
                "data": result_data,
                "timestamp": datetime.now()
            }
        
        self.logger.info(f"Búsqueda completada: {query} - {len(final_results)} resultados")
        return result_data
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Búsqueda real usando DuckDuckGo (sin API key, igual que un navegador)."""
        try:
            from ddgs import DDGS
            
            results = []
            def _run_ddg():
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=max_results))
            
            raw_results = await asyncio.to_thread(_run_ddg)
            
            for item in raw_results:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                    "source": "duckduckgo",
                    "relevance_score": 1.0
                })
            
            self.logger.info(f"DuckDuckGo devolvió {len(results)} resultados reales para: '{query}'")
            return results
        except Exception as e:
            self.logger.error(f"Error en búsqueda DuckDuckGo: {e}")
            return []
    
    async def _search_bing(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Búsqueda usando Bing."""
        try:
            api_key = self.search_apis["bing"]["api_key"]
            headers = {"Ocp-Apim-Subscription-Key": api_key}
            params = {
                "q": query,
                "count": max_results,
                "mkt": "en-US",
                "safeSearch": "Moderate"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.bing.microsoft.com/v7.0/search", 
                                     headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get("webPages", {}).get("value", []):
                            results.append({
                                "title": item.get("name", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("snippet", ""),
                                "source": "bing",
                                "relevance_score": 0.8
                            })
                        return results
        except Exception as e:
            self.logger.error(f"Error en búsqueda Bing: {e}")
        return []
    
    async def _search_google(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Búsqueda usando Google Custom Search."""
        try:
            api_key = self.search_apis["google"]["api_key"]
            cx = self.search_apis["google"]["cx"]
            
            params = {
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": min(max_results, 10)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get("https://www.googleapis.com/customsearch/v1", 
                                     params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get("items", []):
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                                "source": "google",
                                "relevance_score": 0.9
                            })
                        return results
        except Exception as e:
            self.logger.error(f"Error en búsqueda Google: {e}")
        return []
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Elimina resultados duplicados basándose en URL y título similar."""
        seen_urls = set()
        seen_titles = set()
        unique_results = []
        
        for result in results:
            url = result.get("url", "")
            title = result.get("title", "").lower().strip()
            
            # Filtrar duplicados por URL
            if url and url in seen_urls:
                continue
            
            # Filtrar títulos muy similares
            if any(self._similarity(title, seen_title) > 0.8 for seen_title in seen_titles):
                continue
            
            seen_urls.add(url)
            if title:
                seen_titles.add(title)
            unique_results.append(result)
        
        return unique_results
    
    def _similarity(self, str1: str, str2: str) -> float:
        """Calcula similitud entre dos strings."""
        if not str1 or not str2:
            return 0.0
        
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _enrich_search_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquece un resultado de búsqueda con análisis adicional."""
        try:
            url = result.get("url", "")
            if not url:
                return result
            
            # Análisis básico del contenido
            content_analysis = await self._analyze_url_content(url)
            
            # Combinar análisis con resultado original
            enriched = result.copy()
            enriched.update({
                "content_analysis": content_analysis,
                "trust_score": self._calculate_trust_score(result),
                "sentiment": self._analyze_text_sentiment(result.get("snippet", "")),
                "keywords": self._extract_keywords(result.get("snippet", "")),
                "processed_at": datetime.now().isoformat()
            })
            
            return enriched
            
        except Exception as e:
            self.logger.warning(f"Error enriqueciendo resultado: {e}")
            return result
    
    async def _analyze_url_content(self, url: str) -> Dict[str, Any]:
        """Analiza el contenido de una URL."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Extraer texto del body
                        body_text = soup.get_text()
                        
                        # Análisis básico
                        word_count = len(body_text.split())
                        char_count = len(body_text)
                        
                        return {
                            "word_count": word_count,
                            "char_count": char_count,
                            "has_images": len(soup.find_all('img')) > 0,
                            "has_videos": len(soup.find_all(['video', 'iframe'])) > 0,
                            "external_links": len(soup.find_all('a', href=True)),
                            "language": self._detect_language(body_text[:500])  # Primeras 500 chars
                        }
        except Exception as e:
            self.logger.warning(f"Error analizando URL {url}: {e}")
        
        return {"error": "No se pudo analizar el contenido"}
    
    def _calculate_trust_score(self, result: Dict[str, Any]) -> float:
        """Calcula un score de confianza para el resultado."""
        score = 0.5  # Base score
        
        url = result.get("url", "").lower()
        domain = urlparse(url).netloc
        
        # Factores de confianza
        trusted_domains = ["wikipedia.org", "gov", "edu", "org", "reuters", "bbc", "cnn"]
        if any(trusted in domain for trusted in trusted_domains):
            score += 0.3
        
        # Puntuación por fuente
        source = result.get("source", "").lower()
        if source == "google":
            score += 0.2
        elif source == "bing":
            score += 0.15
        
        # Penalizar URLs sospechosas
        suspicious_patterns = ["spam", "fake", "scam", "malware"]
        if any(pattern in url for pattern in suspicious_patterns):
            score -= 0.4
        
        return max(0.0, min(1.0, score))
    
    def _analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """Analiza el sentimiento del texto."""
        if not text:
            return {"compound": 0.0, "pos": 0.0, "neu": 0.0, "neg": 0.0}
        
        return self.sentiment_analyzer.polarity_scores(text)
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extrae palabras clave del texto."""
        if not text:
            return []
        
        # Tokenización y limpieza
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
        
        # Lematización
        lemmatized = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        # Frecuencia de palabras
        word_freq = {}
        for word in lemmatized:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Obtener top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def _detect_language(self, text: str) -> str:
        """Detecta el idioma del texto (implementación simple)."""
        # Implementación básica - en producción usarían una librería como langdetect
        english_words = ["the", "and", "is", "in", "to", "of", "a", "that", "it", "with"]
        words = text.lower().split()
        
        english_count = sum(1 for word in words if word in english_words)
        english_ratio = english_count / len(words) if words else 0
        
        return "en" if english_ratio > 0.1 else "unknown"
    
    # ========================================================================
    # ANÁLISIS DE DOCUMENTOS
    # ========================================================================
    
    async def _analyze_document(self, file_path: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analiza un documento (PDF, DOCX, TXT) y extrae información relevante.
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                content = await self._extract_pdf_content(file_path)
            elif file_ext in ['.docx', '.doc']:
                content = await self._extract_docx_content(file_path)
            elif file_ext == '.txt':
                content = await self._extract_text_content(file_path)
            else:
                raise ValueError(f"Formato de archivo no soportado: {file_ext}")
            
            # Análisis según tipo
            if analysis_type == "basic":
                analysis = self._basic_document_analysis(content)
            elif analysis_type == "comprehensive":
                analysis = await self._comprehensive_document_analysis(content, file_path)
            else:
                analysis = self._basic_document_analysis(content)
            
            return {
                "file_path": file_path,
                "file_type": file_ext,
                "analysis_type": analysis_type,
                "content_length": len(content),
                "analysis": analysis,
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando documento {file_path}: {e}")
            raise
    
    async def _extract_pdf_content(self, file_path: str) -> str:
        """Extrae texto de un archivo PDF."""
        content = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    content.append(f"--- Página {page_num + 1} ---\n{text}")
        except Exception as e:
            self.logger.error(f"Error extrayendo PDF: {e}")
            raise
        
        return "\n\n".join(content)
    
    async def _extract_docx_content(self, file_path: str) -> str:
        """Extrae texto de un archivo DOCX."""
        try:
            doc = Document(file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
            
            return "\n".join(content)
            
        except Exception as e:
            self.logger.error(f"Error extrayendo DOCX: {e}")
            raise
    
    async def _extract_text_content(self, file_path: str) -> str:
        """Extrae contenido de archivo de texto."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
            return content
        except Exception as e:
            self.logger.error(f"Error extrayendo texto: {e}")
            raise
    
    def _basic_document_analysis(self, content: str) -> Dict[str, Any]:
        """Análisis básico del documento."""
        sentences = sent_tokenize(content)
        words = word_tokenize(content)
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_words_per_sentence": len(words) / len(sentences) if sentences else 0,
            "char_count": len(content),
            "readability_score": self._calculate_readability(content),
            "top_keywords": self._extract_keywords(content, 10),
            "sentiment": self._analyze_text_sentiment(content)
        }
    
    async def _comprehensive_document_analysis(self, content: str, file_path: str) -> Dict[str, Any]:
        """Análisis comprehensivo del documento."""
        basic_analysis = self._basic_document_analysis(content)
        
        # Análisis adicional
        entities = await self._extract_entities(content)
        topics = await self._extract_topics(content)
        citations = await self._extract_citations(content)
        structure = await self._analyze_document_structure(content)
        
        return {
            **basic_analysis,
            "entities": entities,
            "topics": topics,
            "citations": citations,
            "structure": structure,
            "summary": await self._generate_document_summary(content),
            "quality_score": self._assess_document_quality(content)
        }
    
    async def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extrae entidades nombradas del texto."""
        # Implementación básica - en producción usarían spaCy o NER
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "concepts": []
        }
        
        # Regex patterns básicos para entidades
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        dates = re.findall(date_pattern, content, re.IGNORECASE)
        entities["dates"] = list(set(dates))
        
        # Acronyms (letras mayúsculas de 2+ caracteres)
        acronyms = re.findall(r'\b[A-Z]{2,}\b', content)
        entities["concepts"] = list(set(acronyms))
        
        return entities
    
    async def _extract_topics(self, content: str) -> List[str]:
        """Extrae temas principales del documento."""
        # Implementación simple basada en frecuencia de palabras clave
        keywords = self._extract_keywords(content, 20)
        
        # Categorizar palabras clave por tema (simplificado)
        topics = {
            "tecnología": ["technology", "digital", "software", "ai", "data", "system"],
            "negocios": ["business", "market", "company", "revenue", "profit", "strategy"],
            "investigación": ["study", "research", "analysis", "results", "conclusion"],
            "académico": ["university", "research", "publication", "journal", "paper"]
        }
        
        detected_topics = []
        content_lower = content.lower()
        
        for topic, keywords_topic in topics.items():
            if any(keyword in content_lower for keyword in keywords_topic):
                detected_topics.append(topic)
        
        return detected_topics
    
    async def _extract_citations(self, content: str) -> List[Dict[str, str]]:
        """Extrae citas y referencias del documento."""
        citations = []
        
        # Patrones para diferentes tipos de citas
        citation_patterns = [
            r'\(([^)]*\d{4}[^)]*)\)',  # (Author, 2023)
            r'\[(\d+(?:,\s*\d+)*)\]',  # [1], [1, 2, 3]
            r'(?:et al\.,?\s*\d{4})',   # Smith et al., 2023
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                citations.append({
                    "raw": match,
                    "type": "reference",
                    "confidence": 0.8
                })
        
        return citations

    async def _synthesize_with_llm(self, query: str, context: str) -> str:
        """Sintetiza la información recopilada utilizando LiteLLM para ser 100% agnóstico del proveedor."""
        import os
        from litellm import acompletion
        
        prompt = f"El usuario está investigando: '{query}'.\n\nBasándote ÚNICAMENTE en este contexto extraído de la web, redacta un resumen analítico y concluyente:\n\nCONTEXTO:\n{context}\n\nSÍNTESIS:"
        
        # Obtenemos el modelo priorizando la variable LLM_MODEL_FULL_NAME
        model_name = (
            os.getenv("LLM_MODEL_FULL_NAME")
            or self.config.get("llm_model")
            or os.getenv("RAYRABBIT_LLM_MODEL")
            or "gpt-4o-mini"
        )
        
        self.logger.info(f"Usando LiteLLM con el modelo: {model_name} para la síntesis de investigación.")
        
        # Obtener variables de conexión del LLM desde el entorno
        llm_api_key = os.getenv("LLM_API_KEY")
        llm_base_url = os.getenv("LLM_BASE_URL")
        llm_timeout_raw = os.getenv("LLM_TIMEOUT")
        
        llm_timeout = None
        if llm_timeout_raw:
            try:
                llm_timeout = float(llm_timeout_raw)
            except ValueError:
                pass
        
        completion_kwargs = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        
        # Inyectar credenciales dinámicas en la llamada de LiteLLM
        if llm_api_key:
            completion_kwargs["api_key"] = llm_api_key
            # OpenRouter / LiteLLM a veces requiere la variable de entorno explícita para ciertos proveedores
            if "openrouter" in model_name.lower():
                os.environ["OPENROUTER_API_KEY"] = llm_api_key
        if llm_base_url:
            completion_kwargs["api_base"] = llm_base_url
        if llm_timeout is not None:
            completion_kwargs["timeout"] = llm_timeout
            
        try:
            response = await acompletion(**completion_kwargs)
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error de LiteLLM al sintetizar contexto: {e}")
            return f"⚠️ Advertencia: Fallo en el proveedor LLM ({model_name}). Revisa tus API keys y configuración de modelo. Detalles: {e}"
    
    async def _analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analiza la estructura del documento."""
        lines = content.split('\n')
        
        # Detectar títulos y subtítulos
        titles = []
        for line in lines:
            line = line.strip()
            if line and (line.isupper() or line.endswith(':') or len(line.split()) <= 8):
                titles.append(line)
        
        # Detectar listas
        list_items = []
        for line in lines:
            line = line.strip()
            if re.match(r'^[\d\-*•]\s+', line):
                list_items.append(line)
        
        return {
            "total_lines": len(lines),
            "titles": titles[:10],  # Top 10 títulos
            "list_items": list_items[:20],  # Top 20 items de lista
            "has_table_of_contents": "table of contents" in content.lower(),
            "has_references": "references" in content.lower() or "bibliography" in content.lower()
        }
    
    async def _generate_document_summary(self, content: str) -> str:
        """Genera un resumen del documento."""
        # Implementación simple - en producción usarían summarization models
        sentences = sent_tokenize(content)
        
        if len(sentences) <= 3:
            return " ".join(sentences)
        
        # Seleccionar las primeras 3 oraciones como resumen básico
        return " ".join(sentences[:3])
    
    def _calculate_readability(self, content: str) -> float:
        """Calcula un score de legibilidad básico."""
        sentences = sent_tokenize(content)
        words = word_tokenize(content)
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        
        # Score simple: menor longitud de oraciones = mayor legibilidad
        # Normalizar a 0-1 scale
        readability = max(0, min(1, (20 - avg_sentence_length) / 20))
        
        return readability
    
    def _assess_document_quality(self, content: str) -> Dict[str, float]:
        """Evalúa la calidad del documento."""
        quality_factors = {
            "completeness": 0.0,  # ¿Tiene introducción y conclusión?
            "structure": 0.0,     # ¿Está bien estructurado?
            "clarity": 0.0,       # ¿Es claro y comprensible?
            "depth": 0.0          # ¿Tiene profundidad de análisis?
        }
        
        content_lower = content.lower()
        
        # Completeness
        intro_indicators = ["introduction", "overview", "abstract", "summary"]
        conclusion_indicators = ["conclusion", "summary", "final", "end"]
        
        if any(indicator in content_lower for indicator in intro_indicators):
            quality_factors["completeness"] += 0.5
        if any(indicator in content_lower for indicator in conclusion_indicators):
            quality_factors["completeness"] += 0.5
        
        # Structure (detección básica de títulos y subtítulos)
        structure_indicators = len(re.findall(r'\n\s*[A-Z][^a-z]*\n', content))
        quality_factors["structure"] = min(1.0, structure_indicators / 10)
        
        # Clarity (basado en longitud de oraciones)
        sentences = sent_tokenize(content)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        quality_factors["clarity"] = max(0, min(1, (15 - avg_sentence_length) / 15))
        
        # Depth (basado en diversidad de vocabulario)
        words = word_tokenize(content.lower())
        unique_words = set(words)
        lexical_diversity = len(unique_words) / len(words) if words else 0
        quality_factors["depth"] = min(1.0, lexical_diversity * 2)
        
        return quality_factors
    
    # ========================================================================
    # FACT CHECKING
    # ========================================================================
    
    async def _fact_check(self, claim: str, sources: List[str] = None) -> Dict[str, Any]:
        """
        Verifica la veracidad de una afirmación utilizando múltiples fuentes.
        """
        sources = sources or ["fact_check_websites", "news_sources"]
        
        # Buscar información relacionada
        search_results = await self._web_search(claim, max_results=5, sources=sources)
        
        # Analizar resultados
        verification_data = {
            "claim": claim,
            "status": "unknown",
            "confidence": 0.0,
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "sources_checked": [],
            "analysis": {}
        }
        
        for result in search_results.get("results", []):
            source_url = result.get("url", "")
            content = result.get("snippet", "")
            trust_score = result.get("trust_score", 0.5)
            
            verification_data["sources_checked"].append({
                "url": source_url,
                "trust_score": trust_score,
                "content": content
            })
            
            # Análisis de polaridad de la información
            sentiment = self._analyze_text_sentiment(content)
            
            # Determinar si apoya o contradice la afirmación
            similarity = self._calculate_claim_similarity(claim, content)
            
            if similarity > 0.6 and trust_score > 0.6:
                verification_data["supporting_evidence"].append({
                    "source": source_url,
                    "content": content,
                    "similarity": similarity,
                    "trust_score": trust_score
                })
            elif similarity < 0.3 and trust_score > 0.6:
                verification_data["contradicting_evidence"].append({
                    "source": source_url,
                    "content": content,
                    "similarity": 1 - similarity,
                    "trust_score": trust_score
                })
        
        # Determinar status final
        if len(verification_data["supporting_evidence"]) >= 2:
            verification_data["status"] = "likely_true"
            verification_data["confidence"] = 0.8
        elif len(verification_data["contradicting_evidence"]) >= 2:
            verification_data["status"] = "likely_false"
            verification_data["confidence"] = 0.8
        elif len(verification_data["supporting_evidence"]) >= 1 or len(verification_data["contradicting_evidence"]) >= 1:
            verification_data["status"] = "inconclusive"
            verification_data["confidence"] = 0.5
        else:
            verification_data["status"] = "insufficient_data"
            verification_data["confidence"] = 0.2
        
        return verification_data
    
    def _calculate_claim_similarity(self, claim: str, content: str) -> float:
        """Calcula la similitud entre una afirmación y el contenido."""
        claim_words = set(claim.lower().split())
        content_words = set(content.lower().split())
        
        if not claim_words or not content_words:
            return 0.0
        
        # Remover palabras comunes
        claim_words = claim_words - self.stop_words
        content_words = content_words - self.stop_words
        
        intersection = len(claim_words.intersection(content_words))
        union = len(claim_words.union(content_words))
        
        return intersection / union if union > 0 else 0.0
    
    # ========================================================================
    # GENERACIÓN DE REPORTES
    # ========================================================================
    
    async def _generate_report(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un reporte basado en los datos proporcionados.
        """
        templates = {
            "executive_summary": self._generate_executive_summary,
            "research_report": self._generate_research_report,
            "competitive_analysis": self._generate_competitive_report,
            "trend_analysis": self._generate_trend_report,
            "academic_paper": self._generate_academic_report
        }
        
        if report_type not in templates:
            raise ValueError(f"Tipo de reporte no soportado: {report_type}")
        
        generator_func = templates[report_type]
        report_content = await generator_func(data)
        
        return {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "content": report_content,
            "metadata": {
                "data_sources": data.get("sources", []),
                "analysis_date": datetime.now().isoformat(),
                "confidence": data.get("confidence", 0.0)
            }
        }
    
    async def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """Genera un resumen ejecutivo."""
        summary = f"""
# RESUMEN EJECUTIVO
**Fecha de análisis:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## HALLAZGOS PRINCIPALES
{self._format_findings(data.get('findings', []))}

## CONCLUSIONES CLAVE
{self._format_conclusions(data.get('conclusions', []))}

## RECOMENDACIONES
{self._format_recommendations(data.get('recommendations', []))}

## MÉTRICAS CLAVE
{self._format_metrics(data.get('metrics', {}))}
"""
        return summary
    
    async def _generate_research_report(self, data: Dict[str, Any]) -> str:
        """Genera un reporte de investigación completo."""
        report = f"""
# REPORTE DE INVESTIGACIÓN
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Tipo:** {data.get('research_type', 'General')}

## METODOLOGÍA
{data.get('methodology', 'Metodología no especificada')}

## RESULTADOS
{self._format_results(data.get('results', []))}

## ANÁLISIS
{self._format_analysis(data.get('analysis', {}))}

## LIMITACIONES
{self._format_limitations(data.get('limitations', []))}

## REFERENCIAS
{self._format_references(data.get('references', []))}
"""
        return report
    
    async def _generate_competitive_report(self, data: Dict[str, Any]) -> str:
        """Genera un reporte de análisis competitivo."""
        companies = data.get('companies', [])
        report = f"""
# ANÁLISIS COMPETITIVO
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Mercado:** {data.get('market', 'No especificado')}

## EMPRESAS ANALIZADAS
"""
        
        for company in companies:
            report += f"### {company.get('name', 'Desconocida')}\n"
            report += f"- **Fortalezas:** {', '.join(company.get('strengths', []))}\n"
            report += f"- **Debilidades:** {', '.join(company.get('weaknesses', []))}\n"
            report += f"- **Cuota de mercado:** {company.get('market_share', 'N/A')}\n\n"
        
        report += self._format_competitive_recommendations(data.get('recommendations', []))
        return report
    
    async def _generate_trend_report(self, data: Dict[str, Any]) -> str:
        """Genera un reporte de análisis de tendencias."""
        trends = data.get('trends', [])
        report = f"""
# ANÁLISIS DE TENDENCIAS
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Período analizado:** {data.get('timeframe', 'N/A')}

## TENDENCIAS IDENTIFICADAS
"""
        
        for trend in trends:
            report += f"### {trend.get('name', 'Tendencia sin nombre')}\n"
            report += f"- **Dirección:** {trend.get('direction', 'No especificada')}\n"
            report += f"- **Magnitud:** {trend.get('magnitude', 'N/A')}\n"
            report += f"- **Impacto esperado:** {trend.get('impact', 'No especificado')}\n"
            report += f"- **Horizonte temporal:** {trend.get('timeframe', 'N/A')}\n\n"
        
        report += self._format_trend_recommendations(data.get('recommendations', []))
        return report
    
    async def _generate_academic_report(self, data: Dict[str, Any]) -> str:
        """Genera un reporte académico."""
        report = f"""
# PAPER ACADÉMICO
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Título:** {data.get('title', 'Título no especificado')}

## ABSTRACT
{data.get('abstract', 'Abstract no disponible')}

## 1. INTRODUCCIÓN
{data.get('introduction', 'Introducción no disponible')}

## 2. METODOLOGÍA
{data.get('methodology', 'Metodología no especificada')}

## 3. RESULTADOS
{self._format_results(data.get('results', []))}

## 4. DISCUSIÓN
{data.get('discussion', 'Discusión no disponible')}

## 5. CONCLUSIONES
{self._format_conclusions(data.get('conclusions', []))}

## REFERENCIAS
{self._format_references(data.get('references', []))}
"""
        return report
    
    def _format_findings(self, findings: List[str]) -> str:
        if not findings:
            return "No se encontraron hallazgos principales."
        return "\n".join(f"- {finding}" for finding in findings)
    
    def _format_conclusions(self, conclusions: List[str]) -> str:
        if not conclusions:
            return "No se derivaron conclusiones específicas."
        return "\n".join(f"- {conclusion}" for conclusion in conclusions)
    
    def _format_recommendations(self, recommendations: List[str]) -> str:
        if not recommendations:
            return "No se generaron recomendaciones específicas."
        return "\n".join(f"- {rec}" for rec in recommendations)
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        if not metrics:
            return "No hay métricas disponibles."
        return "\n".join(f"- **{k}:** {v}" for k, v in metrics.items())
    
    def _format_results(self, results: List[Any]) -> str:
        if not results:
            return "No se obtuvieron resultados específicos."
        return "\n".join(f"- {result}" if isinstance(result, str) else f"- {json.dumps(result)}" for result in results)
    
    def _format_analysis(self, analysis: Dict[str, Any]) -> str:
        if not analysis:
            return "No se realizó análisis específico."
        return "\n".join(f"**{k}:** {v}" for k, v in analysis.items())
    
    def _format_limitations(self, limitations: List[str]) -> str:
        if not limitations:
            return "No se identificaron limitaciones específicas."
        return "\n".join(f"- {limitation}" for limitation in limitations)
    
    def _format_references(self, references: List[Dict[str, str]]) -> str:
        if not references:
            return "No hay referencias disponibles."
        return "\n".join(f"- {ref.get('author', 'Autor desconocido')} ({ref.get('year', 'N/A')}): {ref.get('title', 'Título desconocido')}" for ref in references)
    
    def _format_competitive_recommendations(self, recommendations: List[str]) -> str:
        return f"""
## RECOMENDACIONES ESTRATÉGICAS
{self._format_recommendations(recommendations)}
"""
    
    def _format_trend_recommendations(self, recommendations: List[str]) -> str:
        return f"""
## IMPLICACIONES ESTRATÉGICAS
{self._format_recommendations(recommendations)}
"""
    
    # ========================================================================
    # BÚSQUEDA ACADÉMICA
    # ========================================================================
    
    async def _academic_search(self, query: str, databases: List[str] = None) -> Dict[str, Any]:
        """
        Busca en bases de datos académicas como arXiv y PubMed.
        """
        databases = databases or ["arxiv", "pubmed"]
        results = {}
        
        for db in databases:
            try:
                if db == "arxiv":
                    db_results = await self._search_arxiv(query)
                elif db == "pubmed":
                    db_results = await self._search_pubmed(query)
                else:
                    db_results = []
                
                results[db] = db_results
                
            except Exception as e:
                self.logger.warning(f"Error buscando en {db}: {e}")
                results[db] = []
        
        return results
    
    async def _search_arxiv(self, query: str) -> List[Dict[str, Any]]:
        """Busca en arXiv usando la API oficial v4 (arxiv.Client)."""
        try:
            def _run_arxiv():
                client = arxiv.Client()
                search = arxiv.Search(
                    query=query,
                    max_results=10,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                return list(client.results(search))
            
            papers = await asyncio.to_thread(_run_arxiv)
            
            results = []
            for paper in papers:
                results.append({
                    "title": paper.title,
                    "authors": [str(author) for author in paper.authors],
                    "summary": paper.summary[:500],
                    "published": paper.published.strftime('%Y-%m-%d') if paper.published else "N/A",
                    "url": paper.entry_id,
                    "pdf_url": paper.pdf_url,
                    "categories": paper.categories,
                    "source": "arxiv"
                })
            
            self.logger.info(f"arXiv devolvió {len(results)} papers reales para: '{query}'")
            return results
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda arXiv: {e}")
            return []
    
    async def _search_pubmed(self, query: str) -> List[Dict[str, Any]]:
        """Busca en PubMed via NCBI E-utilities REST API (pública, sin key para búsquedas básicas)."""
        try:
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
            email = self.search_apis.get("pubmed", {}).get("email", "rayrabbit@example.com")
            
            # Paso 1: esearch - obtener IDs de artículos
            async with aiohttp.ClientSession() as session:
                search_params = {
                    "db": "pubmed",
                    "term": query,
                    "retmax": 5,
                    "retmode": "json",
                    "email": email
                }
                async with session.get(f"{base_url}/esearch.fcgi", params=search_params) as resp:
                    search_data = await resp.json()
                
                ids = search_data.get("esearchresult", {}).get("idlist", [])
                if not ids:
                    return []
                
                # Paso 2: efetch - obtener detalles de los artículos
                fetch_params = {
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "json",
                    "rettype": "abstract",
                    "email": email
                }
                async with session.get(f"{base_url}/esummary.fcgi", params=fetch_params) as resp:
                    fetch_data = await resp.json()
                
                results = []
                articles = fetch_data.get("result", {})
                for pmid in ids:
                    article = articles.get(pmid, {})
                    if article:
                        results.append({
                            "title": article.get("title", ""),
                            "authors": [a.get("name", "") for a in article.get("authors", [])],
                            "abstract": article.get("sortpubdate", ""),
                            "journal": article.get("source", ""),
                            "year": article.get("pubdate", "")[:4],
                            "pmid": pmid,
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            "source": "pubmed"
                        })
                
                self.logger.info(f"PubMed devolvió {len(results)} artículos reales para: '{query}'")
                return results
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda PubMed: {e}")
            return []
    
    # ========================================================================
    # GESTIÓN DE CITAS
    # ========================================================================
    
    async def _manage_citations(self, action: str, citation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gestiona citas y referencias académicas.
        """
        if action == "add":
            return await self._add_citation(citation_data)
        elif action == "format":
            return await self._format_citation(citation_data)
        elif action == "validate":
            return await self._validate_citation(citation_data)
        elif action == "export":
            return await self._export_citations(citation_data)
        else:
            raise ValueError(f"Acción no soportada: {action}")
    
    async def _add_citation(self, citation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Añade una nueva cita al repositorio."""
        # En una implementación real, esto se guardaría en una base de datos
        citation_id = hashlib.md5(f"{citation_data}{time.time()}".encode()).hexdigest()[:8]
        
        return {
            "action": "add",
            "citation_id": citation_id,
            "citation": citation_data,
            "status": "added",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _format_citation(self, citation_data: Dict[str, Any]) -> Dict[str, str]:
        """Formatea una cita según diferentes estilos."""
        styles = {
            "apa": self._format_apa,
            "mla": self._format_mla,
            "chicago": self._format_chicago,
            "ieee": self._format_ieee
        }
        
        style = citation_data.get("style", "apa")
        if style not in styles:
            raise ValueError(f"Estilo no soportado: {style}")
        
        formatted = styles[style](citation_data)
        
        return {
            "original": citation_data,
            "formatted": formatted,
            "style": style
        }
    
    async def _validate_citation(self, citation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida una cita académica."""
        required_fields = ["title", "author", "year"]
        missing_fields = [field for field in required_fields if not citation_data.get(field)]
        
        validation_result = {
            "is_valid": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "warnings": [],
            "suggestions": []
        }
        
        # Validaciones específicas
        year = citation_data.get("year")
        if year and (year < 1800 or year > datetime.now().year):
            validation_result["warnings"].append("El año parece fuera del rango típico")
        
        # Sugerencias de mejora
        if not citation_data.get("doi") and not citation_data.get("url"):
            validation_result["suggestions"].append("Considera añadir DOI o URL para mejor accesibilidad")
        
        return validation_result
    
    async def _export_citations(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Exporta citas en diferentes formatos."""
        citations = export_data.get("citations", [])
        format_type = export_data.get("format", "bibtex")
        
        if format_type == "bibtex":
            exported = self._export_bibtex(citations)
        elif format_type == "ris":
            exported = self._export_ris(citations)
        elif format_type == "json":
            exported = json.dumps(citations, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Formato de exportación no soportado: {format_type}")
        
        return {
            "format": format_type,
            "exported_data": exported,
            "citation_count": len(citations)
        }
    
    def _extract_citation_fields(self, citation: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae de manera robusta los campos de una cita, soportando formatos ergonómicos y legados."""
        src = citation.get("source") if isinstance(citation.get("source"), dict) else citation
        
        # Extraer autor/autores
        authors_val = src.get("authors") or src.get("author")
        if isinstance(authors_val, list):
            # Formatear la lista de autores
            authors_str = ", ".join(str(a) for a in authors_val)
        elif authors_val:
            authors_str = str(authors_val)
        else:
            authors_str = "Autor desconocido"
            
        return {
            "author": authors_str,
            "year": src.get("year", "s.f.") if src.get("year") else "s.f.",
            "title": src.get("title", "Título desconocido"),
            "journal": src.get("journal", ""),
            "doi": src.get("doi", ""),
            "url": src.get("url", "")
        }

    def _format_apa(self, citation: Dict[str, Any]) -> str:
        """Formatea cita en estilo APA."""
        fields = self._extract_citation_fields(citation)
        author = fields["author"]
        year = fields["year"]
        title = fields["title"]
        journal = fields["journal"]
        doi = fields["doi"]
        
        citation_str = f"{author} ({year}). {title}."
        if journal:
            citation_str += f" {journal}."
        if doi:
            citation_str += f" https://doi.org/{doi}"
        
        return citation_str
    
    def _format_mla(self, citation: Dict[str, Any]) -> str:
        """Formatea cita en estilo MLA."""
        fields = self._extract_citation_fields(citation)
        author = fields["author"]
        title = fields["title"]
        year = fields["year"]
        journal = fields["journal"]
        
        citation_str = f'{author}. "{title}."'
        if journal:
            citation_str += f" {journal},"
        if year and year != "s.f.":
            citation_str += f" {year},"
        
        return citation_str.rstrip(",") + "."
    
    def _format_chicago(self, citation: Dict[str, Any]) -> str:
        """Formatea cita en estilo Chicago."""
        fields = self._extract_citation_fields(citation)
        author = fields["author"]
        title = fields["title"]
        year = fields["year"]
        journal = fields["journal"]
        
        citation_str = f'{author}. "{title}."'
        if journal:
            citation_str += f" {journal}"
        if year and year != "s.f.":
            citation_str += f" ({year})"
        
        return citation_str
    
    def _format_ieee(self, citation: Dict[str, Any]) -> str:
        """Formatea cita en estilo IEEE."""
        fields = self._extract_citation_fields(citation)
        author = fields["author"]
        title = fields["title"]
        year = fields["year"]
        journal = fields["journal"]
        
        citation_str = f"{author}, \"{title},\""
        if journal:
            citation_str += f" {journal},"
        if year and year != "s.f.":
            citation_str += f" {year}."
        
        return citation_str.rstrip(",") + "."
    
    def _export_bibtex(self, citations: List[Dict[str, Any]]) -> str:
        """Exporta citas en formato BibTeX."""
        bibtex_entries = []
        
        for i, citation in enumerate(citations):
            entry_type = citation.get("type", "article")
            key = citation.get("key", f"ref{i+1}")
            
            entry = f"@{entry_type}{{{key},\n"
            for field, value in citation.items():
                if field not in ["type", "key"] and value:
                    entry += f"  {field} = {{{value}}},\n"
            entry = entry.rstrip(",\n") + "\n}\n"
            bibtex_entries.append(entry)
        
        return "\n".join(bibtex_entries)
    
    def _export_ris(self, citations: List[Dict[str, Any]]) -> str:
        """Exporta citas en formato RIS."""
        ris_entries = []
        
        for citation in citations:
            entry_type = citation.get("type", "JOUR")
            ris_entries.append(f"TY  - {entry_type}")
            
            for field, value in citation.items():
                if field not in ["type"] and value:
                    ris_field = {
                        "author": "AU",
                        "title": "TI",
                        "journal": "JO",
                        "year": "PY",
                        "doi": "DO",
                        "url": "UR"
                    }.get(field, field.upper())
                    ris_entries.append(f"{ris_field}  - {value}")
            
            ris_entries.append("ER  - \n")
        
        return "\n".join(ris_entries)
    
    # ========================================================================
    # ANÁLISIS DE TENDENCIAS
    # ========================================================================
    
    async def _trend_analysis(self, topic: str, timeframe: str = "30d") -> Dict[str, Any]:
        """
        Analiza tendencias relacionadas con un tema específico.
        """
        try:
            # Búsqueda inicial para obtener datos base
            search_results = await self._web_search(topic, max_results=20)
            
            # Análisis temporal (simplificado)
            trend_data = await self._analyze_temporal_trends(search_results, timeframe)
            
            # Análisis de sentimiento de tendencias
            sentiment_trends = await self._analyze_sentiment_trends(search_results)
            
            # Predicción de tendencias (implementación básica)
            predictions = await self._predict_future_trends(trend_data, topic)
            
            return {
                "topic": topic,
                "timeframe": timeframe,
                "analysis_date": datetime.now().isoformat(),
                "trend_data": trend_data,
                "sentiment_analysis": sentiment_trends,
                "predictions": predictions,
                "key_insights": await self._extract_key_insights(trend_data),
                "recommendations": await self._generate_trend_recommendations(trend_data, topic)
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis de tendencias: {e}")
            raise
    
    async def _analyze_temporal_trends(self, search_results: Dict[str, Any], timeframe: str) -> Dict[str, Any]:
        """Analiza tendencias temporales reales usando las fechas de publicación extraídas de los resultados."""
        results = search_results.get("results", [])
        
        trend_points = []
        for result in results[:10]:
            # Extraer fecha real del resultado si existe (scraping de metadatos)
            raw_date = result.get("published_date") or result.get("date") or result.get("timestamp")
            
            if raw_date:
                try:
                    from dateutil import parser as date_parser
                    parsed_date = date_parser.parse(str(raw_date), fuzzy=True)
                except (ValueError, TypeError):
                    parsed_date = datetime.now()
            else:
                # Si no hay fecha explícita, usamos la fecha actual como conservador
                parsed_date = datetime.now()
            
            # Calcular relevancia usando el sentiment score real del resultado
            sentiment_score = result.get("sentiment", {}).get("compound", 0.0)
            relevance = result.get("relevance_score", 0.5)
            
            trend_points.append({
                "date": parsed_date.isoformat(),
                "relevance": relevance,
                "sentiment": sentiment_score,
                "source_url": result.get("url", ""),
                "title": result.get("title", "")
            })
        
        # Ordenar por fecha real
        trend_points.sort(key=lambda x: x["date"])
        
        # Calcular dirección real de tendencia por sentimiento
        if len(trend_points) >= 2:
            first_half_sentiment = sum(p["sentiment"] for p in trend_points[:len(trend_points)//2]) / (len(trend_points)//2)
            second_half_sentiment = sum(p["sentiment"] for p in trend_points[len(trend_points)//2:]) / (len(trend_points) - len(trend_points)//2)
            trend_direction = "increasing" if second_half_sentiment > first_half_sentiment else "decreasing"
        else:
            trend_direction = "neutral"
        
        return {
            "data_points": trend_points,
            "trend_direction": trend_direction,
            "total_sources": len(trend_points),
            "peak_activity": max(trend_points, key=lambda x: x["relevance"]) if trend_points else None
        }
    
    async def _analyze_sentiment_trends(self, search_results: Dict[str, Any]) -> Dict[str, float]:
        """Analiza tendencias de sentimiento."""
        results = search_results.get("results", [])
        
        sentiments = []
        for result in results:
            sentiment = result.get("sentiment", {})
            if sentiment:
                sentiments.append(sentiment.get("compound", 0.0))
        
        if not sentiments:
            return {"average_sentiment": 0.0, "sentiment_trend": "neutral"}
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        return {
            "average_sentiment": avg_sentiment,
            "sentiment_distribution": {
                "positive": len([s for s in sentiments if s > 0.1]) / len(sentiments),
                "neutral": len([s for s in sentiments if -0.1 <= s <= 0.1]) / len(sentiments),
                "negative": len([s for s in sentiments if s < -0.1]) / len(sentiments)
            },
            "sentiment_trend": "improving" if sentiments[-1] > sentiments[0] else "declining"
        }
    
    async def _predict_future_trends(self, trend_data: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """Predice tendencias futuras (implementación básica)."""
        data_points = trend_data.get("data_points", [])
        
        if len(data_points) < 2:
            return {"prediction": "insufficient_data", "confidence": 0.0}
        
        # Predicción lineal simple
        recent_volume = data_points[-1]["volume"]
        trend_direction = trend_data.get("trend_direction", "stable")
        
        predictions = {
            "next_week": {
                "expected_volume": recent_volume * (1.1 if trend_direction == "increasing" else 0.9),
                "confidence": 0.6
            },
            "next_month": {
                "expected_volume": recent_volume * (1.2 if trend_direction == "increasing" else 0.8),
                "confidence": 0.4
            }
        }
        
        return predictions
    
    async def _extract_key_insights(self, trend_data: Dict[str, Any]) -> List[str]:
        """Extrae insights clave del análisis de tendencias."""
        insights = []
        
        trend_direction = trend_data.get("trend_direction", "stable")
        volatility = trend_data.get("volatility", 0)
        
        if trend_direction == "increasing":
            insights.append("El tema muestra una tendencia de crecimiento sostenido")
        elif trend_direction == "decreasing":
            insights.append("El tema presenta una tendencia de declive notable")
        
        if volatility > 50:
            insights.append("Alta volatilidad detectada en el tema")
        elif volatility < 20:
            insights.append("Baja volatilidad indica estabilidad en el tema")
        
        peak_activity = trend_data.get("peak_activity")
        if peak_activity:
            insights.append(f"Actividad pico detectada: {peak_activity['volume']} unidades")
        
        return insights
    
    async def _generate_trend_recommendations(self, trend_data: Dict[str, Any], topic: str) -> List[str]:
        """Genera recomendaciones basadas en el análisis de tendencias."""
        recommendations = []
        
        trend_direction = trend_data.get("trend_direction", "stable")
        
        if trend_direction == "increasing":
            recommendations.append(f"Considera aumentar la inversión en investigación sobre {topic}")
            recommendations.append("Aprovecha el momentum creciente del tema")
        elif trend_direction == "decreasing":
            recommendations.append(f"Evalúa si continuar la investigación sobre {topic} es estratégico")
            recommendations.append("Considera diversificar hacia temas más activos")
        
        volatility = trend_data.get("volatility", 0)
        if volatility > 50:
            recommendations.append("Monitorea de cerca debido a alta volatilidad")
        
        return recommendations
    
    # ========================================================================
    # INTELIGENCIA COMPETITIVA
    # ========================================================================
    
    async def _competitive_intelligence(self, company: str, analysis_type: str = "overview") -> Dict[str, Any]:
        """
        Realiza análisis de inteligencia competitiva para una empresa.
        """
        try:
            # Búsqueda de información de la empresa
            company_query = f"{company} company analysis financial performance"
            search_results = await self._web_search(company_query, max_results=15)
            
            # Análisis según tipo solicitado
            if analysis_type == "overview":
                intel_data = await self._company_overview_analysis(company, search_results)
            elif analysis_type == "financial":
                intel_data = await self._financial_analysis(company, search_results)
            elif analysis_type == "competitive_position":
                intel_data = await self._competitive_position_analysis(company, search_results)
            else:
                intel_data = await self._company_overview_analysis(company, search_results)
            
            # Análisis de fortalezas y debilidades
            swot_analysis = await self._swot_analysis(company, search_results)
            
            # Análisis de mercado
            market_analysis = await self._market_analysis(company, search_results)
            
            return {
                "company": company,
                "analysis_type": analysis_type,
                "analysis_date": datetime.now().isoformat(),
                "intelligence_data": intel_data,
                "swot_analysis": swot_analysis,
                "market_analysis": market_analysis,
                "recommendations": await self._generate_competitive_recommendations(company, intel_data, swot_analysis),
                "sources_count": len(search_results.get("results", []))
            }
            
        except Exception as e:
            self.logger.error(f"Error en inteligencia competitiva: {e}")
            raise
    
    async def _company_overview_analysis(self, company: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis general de la empresa."""
        results = search_results.get("results", [])
        
        # Extraer información básica
        overview_data = {
            "company_name": company,
            "business_description": "",
            "key_products": [],
            "market_focus": "",
            "recent_news": [],
            "leadership": [],
            "headquarters": "",
            "founded": ""
        }
        
        for result in results:
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            
            # Clasificar información por relevancia
            if "about" in snippet.lower() or "company" in snippet.lower():
                overview_data["business_description"] = snippet[:200] + "..."
            
            if "product" in snippet.lower() or "service" in snippet.lower():
                overview_data["key_products"].append(snippet[:100] + "...")
            
            if any(word in snippet.lower() for word in ["ceo", "president", "founder", "leader"]):
                overview_data["leadership"].append(snippet[:100] + "...")
        
        return overview_data
    
    async def _financial_analysis(self, company: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis financiero de la empresa."""
        results = search_results.get("results", [])
        
        financial_data = {
            "revenue": "N/A",
            "profit": "N/A",
            "growth_rate": "N/A",
            "market_cap": "N/A",
            "debt_ratio": "N/A",
            "financial_health": "unknown",
            "recent_performance": []
        }
        
        # Buscar indicadores financieros en los resultados
        for result in results:
            snippet = result.get("snippet", "")
            
            # Patrones financieros simples
            revenue_match = re.search(r'revenue.*?\$?([\d,]+\.?\d*)\s*(million|billion)', snippet, re.IGNORECASE)
            if revenue_match:
                financial_data["revenue"] = f"${revenue_match.group(1)} {revenue_match.group(2)}"
            
            profit_match = re.search(r'profit.*?\$?([\d,]+\.?\d*)\s*(million|billion)', snippet, re.IGNORECASE)
            if profit_match:
                financial_data["profit"] = f"${profit_match.group(1)} {profit_match.group(2)}"
            
            growth_match = re.search(r'growth.*?(\d+\.?\d*)%', snippet)
            if growth_match:
                financial_data["growth_rate"] = f"{growth_match.group(1)}%"
        
        # Análisis básico de salud financiera
        if financial_data["revenue"] != "N/A" and financial_data["profit"] != "N/A":
            financial_data["financial_health"] = "good"
        elif financial_data["revenue"] != "N/A":
            financial_data["financial_health"] = "moderate"
        else:
            financial_data["financial_health"] = "unknown"
        
        return financial_data
    
    async def _competitive_position_analysis(self, company: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis de posición competitiva."""
        results = search_results.get("results", [])
        
        position_data = {
            "market_share": "N/A",
            "main_competitors": [],
            "competitive_advantages": [],
            "competitive_disadvantages": [],
            "market_position": "unknown",
            "threat_level": "low"
        }
        
        for result in results:
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            
            # Buscar competidores mencionados
            if any(word in snippet.lower() for word in ["competitor", "competition", "vs", "versus"]):
                position_data["main_competitors"].append(snippet[:100] + "...")
            
            # Buscar ventajas competitivas
            if any(word in snippet.lower() for word in ["advantage", "strength", "leader", "innovation"]):
                position_data["competitive_advantages"].append(snippet[:100] + "...")
            
            # Buscar desventajas
            if any(word in snippet.lower() for word in ["weakness", "challenge", "problem", "issue"]):
                position_data["competitive_disadvantages"].append(snippet[:100] + "...")
        
        return position_data
    
    async def _swot_analysis(self, company: str, search_results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Realiza análisis SWOT (Fortalezas, Oportunidades, Debilidades, Amenazas)."""
        results = search_results.get("results", [])
        
        swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }
        
        for result in results:
            snippet = result.get("snippet", "").lower()
            
            # Clasificación automática básica
            if any(word in snippet for word in ["strong", "leader", "innovation", "advantage"]):
                swot["strengths"].append(result.get("snippet", "")[:150])
            
            if any(word in snippet for word in ["weak", "problem", "challenge", "issue"]):
                swot["weaknesses"].append(result.get("snippet", "")[:150])
            
            if any(word in snippet for word in ["opportunity", "potential", "growth", "expansion"]):
                swot["opportunities"].append(result.get("snippet", "")[:150])
            
            if any(word in snippet for word in ["threat", "risk", "competition", "decline"]):
                swot["threats"].append(result.get("snippet", "")[:150])
        
        return swot
    
    async def _market_analysis(self, company: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el mercado de la empresa."""
        market_data = {
            "market_size": "N/A",
            "growth_trend": "stable",
            "market_segment": "",
            "geographic_presence": "",
            "regulatory_environment": "neutral"
        }
        
        # Análisis simplificado del mercado
        results = search_results.get("results", [])
        market_mentions = [result.get("snippet", "") for result in results if "market" in result.get("snippet", "").lower()]
        
        if market_mentions:
            market_data["market_segment"] = market_mentions[0][:100] + "..."
        
        return market_data
    
    async def _generate_competitive_recommendations(self, company: str, intel_data: Dict[str, Any], swot_analysis: Dict[str, List[str]]) -> List[str]:
        """Genera recomendaciones competitivas."""
        recommendations = []
        
        strengths = swot_analysis.get("strengths", [])
        weaknesses = swot_analysis.get("weaknesses", [])
        opportunities = swot_analysis.get("opportunities", [])
        threats = swot_analysis.get("threats", [])
        
        # Recomendaciones basadas en fortalezas
        if len(strengths) >= 3:
            recommendations.append(f"Capitalizar las fortalezas identificadas de {company} en el mercado")
        
        # Recomendaciones basadas en debilidades
        if len(weaknesses) >= 2:
            recommendations.append(f"Abordar las debilidades críticas identificadas en {company}")
        
        # Recomendaciones basadas en oportunidades
        if len(opportunities) >= 2:
            recommendations.append("Aprovechar las oportunidades de mercado detectadas")
        
        # Recomendaciones basadas en amenazas
        if len(threats) >= 2:
            recommendations.append("Desarrollar estrategias de mitigación de amenazas competitivas")
        
        # Recomendaciones generales
        recommendations.append(f"Monitorear continuamente el desempeño de {company}")
        recommendations.append("Actualizar el análisis competitivo regularmente")
        
        return recommendations
    
    # ========================================================================
    # EXTRACCIÓN DE DATOS
    # ========================================================================
    
    async def _extract_data(self, source: str, extraction_patterns: List[str]) -> Dict[str, Any]:
        """
        Extrae datos estructurados de fuentes no estructuradas.
        """
        try:
            if source.startswith("http"):
                # Extraer de URL
                content = await self._extract_web_content(source)
            elif os.path.exists(source):
                # Extraer de archivo
                content = await self._extract_file_content(source)
            else:
                # Tratar como texto directo
                content = source
            
            extracted_data = await self._apply_extraction_patterns(content, extraction_patterns)
            
            return {
                "source": source,
                "extraction_patterns": extraction_patterns,
                "extraction_date": datetime.now().isoformat(),
                "confidence_score": self._calculate_extraction_confidence(extracted_data),
                "extracted_data": extracted_data,
                **extracted_data
            }
            
        except Exception as e:
            self.logger.error(f"Error en extracción de datos: {e}")
            raise
    
    async def _extract_web_content(self, url: str) -> str:
        """Extrae contenido de una página web."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Extraer texto del body
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        return soup.get_text()
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error extrayendo contenido web: {e}")
            raise
    
    async def _extract_file_content(self, file_path: str) -> str:
        """Extrae contenido de un archivo."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return await self._extract_pdf_content(file_path)
        elif file_ext in ['.docx', '.doc']:
            return await self._extract_docx_content(file_path)
        elif file_ext in ['.txt', '.md']:
            return await self._extract_text_content(file_path)
        else:
            raise ValueError(f"Formato de archivo no soportado para extracción: {file_ext}")
    
    async def _apply_extraction_patterns(self, content: str, patterns: List[str]) -> Dict[str, Any]:
        """Aplica patrones de extracción al contenido."""
        extracted = {}
        
        for pattern in patterns:
            try:
                # Patrones específicos
                if pattern == "emails":
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
                    extracted["emails"] = [{"value": email, "confidence": 1.0} for email in sorted(list(set(emails)))]
                
                elif pattern == "phones":
                    phones = re.findall(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b', content)
                    extracted["phones"] = [{"value": f"({match[0]}) {match[1]}-{match[2]}", "confidence": 0.8} for match in phones]
                
                elif pattern == "urls":
                    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
                    extracted["urls"] = [{"value": url, "confidence": 1.0} for url in sorted(list(set(urls)))]
                
                elif pattern == "dates":
                    dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', content, re.IGNORECASE)
                    extracted["dates"] = [{"value": d, "confidence": 0.7} for d in sorted(list(set(dates)))]
                
                elif pattern == "addresses":
                    # Patrón básico para direcciones
                    addresses = re.findall(r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)', content, re.IGNORECASE)
                    extracted["addresses"] = [{"value": addr, "confidence": 0.6} for addr in sorted(list(set(addresses)))]
                
                elif pattern == "names":
                    # Patrón básico para nombres propios
                    names = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', content)
                    extracted["names"] = [{"value": name, "confidence": 0.5} for name in sorted(list(set(names)))]
                
                elif pattern == "monetary_values":
                    monetary = re.findall(r'\$[\d,]+\.?\d*', content)
                    extracted["monetary_values"] = [{"value": val, "confidence": 0.8} for val in sorted(list(set(monetary)))]
                
                elif pattern == "percentages":
                    percentages = re.findall(r'\d+\.?\d*%', content)
                    extracted["percentages"] = [{"value": val, "confidence": 0.8} for val in sorted(list(set(percentages)))]
                
                elif pattern == "companies":
                    # Búsqueda de empresas (texto en mayúsculas o con "Inc", "Corp", etc.)
                    companies = re.findall(r'\b[A-Z][A-Za-z\s]*(?:Inc|Corp|Corporation|LLC|Ltd|Company|Co\.?)\b', content)
                    extracted["companies"] = [{"value": comp, "confidence": 0.6} for comp in sorted(list(set(companies)))]
                
                elif pattern == "social_security":
                    ss_numbers = re.findall(r'\b\d{3}-\d{2}-\d{4}\b', content)
                    extracted["social_security"] = [{"value": ss, "confidence": 1.0} for ss in ss_numbers]
                
                elif pattern == "credit_cards":
                    # Detectar números de tarjeta de crédito (formato básico)
                    cc_numbers = re.findall(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', content)
                    extracted["credit_cards"] = [{"value": cc, "confidence": 1.0} for cc in cc_numbers]
                
                else:
                    # Patrón personalizado usando regex
                    try:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        extracted[f"custom_{pattern}"] = [{"value": m, "confidence": 0.5} for m in sorted(list(set(matches)))]
                    except Exception as e:
                        self.logger.warning(f"Error con patrón personalizado '{pattern}': {e}")
                        
            except Exception as e:
                self.logger.warning(f"Error aplicando patrón '{pattern}': {e}")
                extracted[pattern] = []
        
        return extracted
    
    def _calculate_extraction_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Calcula un score de confianza para la extracción."""
        total_items = sum(len(values) if isinstance(values, list) else 1 for values in extracted_data.values())
        
        if total_items == 0:
            return 0.0
        
        # Factores de confianza
        confidence_factors = {
            "email": 0.9,
            "phone": 0.8,
            "url": 0.9,
            "date": 0.7,
            "address": 0.6,
            "name": 0.5,
            "monetary_value": 0.8,
            "percentage": 0.8,
            "company": 0.6
        }
        
        total_confidence = 0
        pattern_count = 0
        
        for pattern, values in extracted_data.items():
            if isinstance(values, list) and len(values) > 0:
                # Extraer tipo de patrón
                pattern_type = pattern.split('_')[0] if '_' in pattern else pattern
                base_confidence = confidence_factors.get(pattern_type, 0.5)
                
                # Ajustar confianza basada en número de matches
                match_bonus = min(0.2, len(values) * 0.05)
                adjusted_confidence = min(1.0, base_confidence + match_bonus)
                
                total_confidence += adjusted_confidence
                pattern_count += 1
        
        return total_confidence / pattern_count if pattern_count > 0 else 0.0
    
    # ========================================================================
    # MANEJO DE MENSAJES PERSONALIZADO
    # ========================================================================
    
    async def _handle_request(self, message: Message) -> Optional[Message]:
        """
        Maneja solicitudes de investigación de forma especializada.
        """
        text = message.content.get("text", "") if isinstance(message.content, dict) else ""
        
        # Detectar tipo de investigación solicitada
        if "investigar" in text.lower() or "research" in text.lower():
            return await self._handle_research_request(message, text)
        
        # Buscar comandos específicos de investigación
        research_keywords = [
            "buscar", "search", "web", "análisis", "analyze", 
            "verificar", "fact check", "reporte", "report"
        ]
        
        if any(keyword in text.lower() for keyword in research_keywords):
            return await self._handle_research_request(message, text)
        
        # Delegar al manejador base
        return await super()._handle_request(message)
    
    async def _handle_research_request(self, message: Message, text: str) -> Optional[Message]:
        """Maneja solicitudes específicas de investigación."""
        try:
            # Extraer parámetros de la solicitud
            query = self._extract_research_query(text)
            research_type = self._determine_research_type(text)
            
            if not query:
                return message.create_response(
                    content={"error": "No se pudo extraer una consulta de investigación válida"},
                    message_type=MessageType.ERROR
                )
            
            # Ejecutar investigación según el tipo
            if research_type == "web_search":
                results = await self._web_search(query)
            elif research_type == "fact_check":
                results = await self._fact_check(query)
            elif research_type == "academic_search":
                results = await self._academic_search(query)
            else:
                results = await self._web_search(query)
            
            return message.create_response(
                content={
                    "query": query,
                    "research_type": research_type,
                    "results": results,
                    "agent": self.name
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error manejando solicitud de investigación: {e}")
            return message.create_response(
                content={"error": f"Error en investigación: {str(e)}"},
                message_type=MessageType.ERROR
            )
    
    def _extract_research_query(self, text: str) -> Optional[str]:
        """Extrae la consulta de investigación del texto."""
        # Limpiar texto y extraer consulta principal
        text = text.lower().strip()
        
        # Remover palabras comunes de comandos
        command_words = ["investigar", "research", "buscar", "search", "analizar", "analyze"]
        for word in command_words:
            text = text.replace(word, "")
        
        # Limpiar puntuación excesiva
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())  # Normalizar espacios
        
        return text.strip() if text.strip() else None
    
    def _determine_research_type(self, text: str) -> str:
        """Determina el tipo de investigación solicitado."""
        text_lower = text.lower()
        
        if "fact check" in text_lower or "verificar" in text_lower:
            return "fact_check"
        elif "academic" in text_lower or "paper" in text_lower or "journal" in text_lower:
            return "academic_search"
        elif "web" in text_lower or "internet" in text_lower:
            return "web_search"
        else:
            return "web_search"  # Default
    
    # ========================================================================
    # MÉTODOS DE UTILIDAD
    # ========================================================================
    
    def get_research_capabilities(self) -> Dict[str, Any]:
        """Retorna las capacidades de investigación del agente."""
        return {
            "web_search": {
                "enabled": True,
                "supported_apis": list(self.search_apis.keys()),
                "max_results": self.config.get("max_sources_per_query", 10)
            },
            "document_analysis": {
                "supported_formats": [".pdf", ".docx", ".doc", ".txt"],
                "analysis_types": ["basic", "comprehensive"]
            },
            "fact_checking": {
                "enabled": self.config.get("fact_check_enabled", True),
                "confidence_threshold": 0.6
            },
            "academic_search": {
                "enabled": self.config.get("academic_mode", True),
                "databases": ["arxiv", "pubmed"]
            },
            "data_extraction": {
                "patterns": ["emails", "phones", "urls", "dates", "addresses", "names"],
                "confidence_scoring": True
            },
            "report_generation": {
                "templates": ["executive_summary", "research_report", "competitive_analysis"],
                "formats": ["markdown", "json"]
            },
            "cache": {
                "enabled": self.config.get("cache_enabled", True),
                "duration_hours": self.config.get("cache_duration_hours", 24)
            }
        }
    
    def get_research_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas de investigación."""
        return {
            "cache_entries": len(self._research_cache),
            "sources_configured": len([api for api in self.search_apis.values() if api.get("enabled", False)]),
            "total_capabilities": len(self.capabilities),
            "uptime": datetime.now().isoformat()
        }
    
    async def export_research_data(self, format_type: str = "json") -> Dict[str, Any]:
        """Exporta datos de investigación."""
        data = {
            "agent_info": {
                "id": self.id,
                "name": self.name,
                "type": "ResearcherAgent",
                "version": "1.0.0"
            },
            "capabilities": self.get_research_capabilities(),
            "statistics": self.get_research_statistics(),
            "cache_summary": {
                "entries": len(self._research_cache),
                "enabled": self.config.get("cache_enabled", True)
            },
            "export_date": datetime.now().isoformat()
        }
        
        if format_type == "json":
            return data
        else:
            return {"error": f"Formato de exportación no soportado: {format_type}"}
