"""
Configuración del ResearcherAgent Enterprise

Este archivo contiene todas las configuraciones específicas para el ResearcherAgent,
incluyendo APIs, patrones de búsqueda, templates de reportes y configuraciones
de análisis.

Autor: RayRabbit Enterprise
Versión: 1.0.0
"""

import os
from typing import Dict, Any, List

# ========================================================================
# CONFIGURACIÓN DE APIs DE BÚSQUEDA
# ========================================================================

SEARCH_APIS_CONFIG = {
    "google": {
        "enabled": bool(os.getenv("GOOGLE_SEARCH_API_KEY")),
        "api_key": os.getenv("GOOGLE_SEARCH_API_KEY"),
        "cx": os.getenv("GOOGLE_SEARCH_CX"),
        "rate_limit": 10,  # requests per minute
        "max_results": 10,
        "priority": 1  # 1 = highest, 3 = lowest
    },
    "bing": {
        "enabled": bool(os.getenv("BING_SEARCH_API_KEY")),
        "api_key": os.getenv("BING_SEARCH_API_KEY"),
        "rate_limit": 15,
        "max_results": 10,
        "priority": 2
    },
    "duckduckgo": {
        "enabled": True,
        "rate_limit": 10,
        "max_results": 8,
        "priority": 3
    }
}

# ========================================================================
# CONFIGURACIÓN DE BASE DE DATOS ACADÉMICAS
# ========================================================================

ACADEMIC_DATABASES = {
    "arxiv": {
        "enabled": True,
        "base_url": "http://export.arxiv.org/api/query",
        "max_results": 20,
        "rate_limit": 5,
        "categories": ["cs.AI", "cs.LG", "cs.IR", "stat.ML"]
    },
    "pubmed": {
        "enabled": True,
        "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
        "max_results": 20,
        "rate_limit": 3,
        "email": os.getenv("PUBMED_EMAIL", ""),  # Requerido para PubMed API
        "api_key": os.getenv("PUBMED_API_KEY", "")
    },
    "google_scholar": {
        "enabled": bool(os.getenv("GOOGLE_SCHOLAR_API_KEY")),
        "api_key": os.getenv("GOOGLE_SCHOLAR_API_KEY"),
        "rate_limit": 10,
        "max_results": 15
    }
}

# ========================================================================
# PATRONES DE EXTRACCIÓN DE DATOS
# ========================================================================

EXTRACTION_PATTERNS = {
    "emails": {
        "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "confidence": 0.95,
        "description": "Direcciones de correo electrónico"
    },
    "phones": {
        "pattern": r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
        "confidence": 0.85,
        "description": "Números telefónicos"
    },
    "urls": {
        "pattern": r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        "confidence": 0.90,
        "description": "URLs y enlaces web"
    },
    "dates": {
        "pattern": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        "confidence": 0.80,
        "description": "Fechas en varios formatos"
    },
    "addresses": {
        "pattern": r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl)',
        "confidence": 0.70,
        "description": "Direcciones físicas"
    },
    "names": {
        "pattern": r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
        "confidence": 0.60,
        "description": "Nombres propios"
    },
    "monetary_values": {
        "pattern": r'\$[\d,]+\.?\d*',
        "confidence": 0.85,
        "description": "Valores monetarios"
    },
    "percentages": {
        "pattern": r'\d+\.?\d*%',
        "confidence": 0.85,
        "description": "Porcentajes"
    },
    "companies": {
        "pattern": r'\b[A-Z][A-Za-z\s]*(?:Inc|Corp|Corporation|LLC|Ltd|Company|Co\.?)\b',
        "confidence": 0.75,
        "description": "Nombres de empresas"
    },
    "social_security": {
        "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
        "confidence": 0.95,
        "description": "Números de seguro social (solo para análisis)",
        "sensitive": True
    },
    "credit_cards": {
        "pattern": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "confidence": 0.90,
        "description": "Números de tarjeta de crédito (solo para análisis)",
        "sensitive": True
    },
    "ip_addresses": {
        "pattern": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        "confidence": 0.80,
        "description": "Direcciones IP"
    },
    "isbn": {
        "pattern": r'\bISBN(?:-1[03])?:?\s*(?:[0-9Xx][- ]?){13}\b',
        "confidence": 0.90,
        "description": "Números ISBN de libros"
    }
}

# ========================================================================
# TEMPLATES DE REPORTES
# ========================================================================

REPORT_TEMPLATES = {
    "executive_summary": {
        "name": "Resumen Ejecutivo",
        "sections": ["hallazgos", "conclusiones", "recomendaciones", "métricas"],
        "format": "markdown",
        "max_length": 2000,
        "target_audience": "ejecutivos"
    },
    "research_report": {
        "name": "Reporte de Investigación",
        "sections": ["metodología", "resultados", "análisis", "limitaciones", "referencias"],
        "format": "markdown",
        "max_length": 5000,
        "target_audience": "investigadores"
    },
    "competitive_analysis": {
        "name": "Análisis Competitivo",
        "sections": ["empresas_analizadas", "fortalezas_debilidades", "posicionamiento", "estrategias"],
        "format": "markdown",
        "max_length": 3000,
        "target_audience": "estrategas_de_negocio"
    },
    "trend_analysis": {
        "name": "Análisis de Tendencias",
        "sections": ["tendencias_identificadas", "implicaciones", "predicciones", "recomendaciones"],
        "format": "markdown",
        "max_length": 2500,
        "target_audience": "analistas"
    },
    "academic_paper": {
        "name": "Paper Académico",
        "sections": ["abstract", "introducción", "metodología", "resultados", "discusión", "conclusiones", "referencias"],
        "format": "markdown",
        "max_length": 8000,
        "target_audience": "comunidad_académica"
    },
    "fact_check_report": {
        "name": "Reporte de Verificación",
        "sections": ["afirmación", "evidencia_a_favor", "evidencia_en_contra", "conclusión", "fuentes"],
        "format": "markdown",
        "max_length": 1500,
        "target_audience": "periodistas_investigadores"
    }
}

# ========================================================================
# CONFIGURACIÓN DE ANÁLISIS DE SENTIMIENTO
# ========================================================================

SENTIMENT_CONFIG = {
    "analyzer": "vader",  # vader, textblob
    "thresholds": {
        "positive": 0.05,
        "negative": -0.05,
        "strong_positive": 0.5,
        "strong_negative": -0.5
    },
    "languages": ["en", "es"],  # Soporte para inglés y español
    "context_window": 1000  # Número de caracteres para análisis contextual
}

# ========================================================================
# CONFIGURACIÓN DE CACHE Y ALMACENAMIENTO
# ========================================================================

CACHE_CONFIG = {
    "enabled": True,
    "duration_hours": 24,
    "max_size_mb": 100,
    "cleanup_interval_hours": 6,
    "persistent_storage": True,
    "storage_path": "./research_cache",
    "compression": True
}

# ========================================================================
# DOMINIOS DE CONFIANZA
# ========================================================================

TRUSTED_DOMAINS = {
    "high_trust": {
        "domains": [
            "wikipedia.org",
            "gov",
            "edu",
            "reuters.com",
            "bbc.com",
            "cnn.com",
            "nature.com",
            "science.org",
            "jstor.org",
            "pubmed.ncbi.nlm.nih.gov",
            "arxiv.org",
            "acm.org",
            "ieee.org"
        ],
        "trust_score": 0.9
    },
    "medium_trust": {
        "domains": [
            "medium.com",
            "github.com",
            "stackoverflow.com",
            "reddit.com",
            "wordpress.com",
            "blogspot.com"
        ],
        "trust_score": 0.7
    },
    "low_trust": {
        "domains": [
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "tiktok.com"
        ],
        "trust_score": 0.4
    }
}

# ========================================================================
# PATRONES DE PALABRAS CLAVE POR TEMA
# ========================================================================

TOPIC_KEYWORDS = {
    "tecnología": [
        "technology", "digital", "software", "ai", "artificial intelligence",
        "machine learning", "data", "algorithm", "system", "innovation",
        "tech", "programming", "development", "computer", "cyber"
    ],
    "medicina_salud": [
        "medical", "health", "disease", "treatment", "diagnosis", "patient",
        "clinical", "hospital", "doctor", "medicine", "pharmaceutical",
        "therapy", "surgery", "epidemic", "vaccine", "cure"
    ],
    "finanzas_economía": [
        "finance", "economy", "market", "stock", "investment", "banking",
        "currency", "debt", "profit", "revenue", "financial", "economic",
        "trading", "investment", "portfolio", "inflation"
    ],
    "educación": [
        "education", "school", "university", "student", "teacher", "learning",
        "academic", "curriculum", "degree", "research", "study", "knowledge",
        "training", "course", "class", "lesson"
    ],
    "medio_ambiente": [
        "environment", "climate", "pollution", "green", "sustainability",
        "renewable", "carbon", "emission", "ecosystem", "biodiversity",
        "conservation", "energy", "solar", "wind", "recycling"
    ],
    "política_gobierno": [
        "politics", "government", "policy", "law", "election", "vote",
        "democracy", "parliament", "senate", "congress", "ministry",
        "political", "governance", "public", "citizen"
    ]
}

# ========================================================================
# CONFIGURACIÓN DE TELEMETRÍA
# ========================================================================

TELEMETRY_CONFIG = {
    "enabled": True,
    "metrics": [
        "search_queries",
        "documents_analyzed",
        "facts_checked",
        "reports_generated",
        "cache_hits",
        "api_calls",
        "processing_time"
    ],
    "aggregation_interval": 300,  # segundos
    "export_formats": ["json", "csv", "prometheus"]
}

# ========================================================================
# CONFIGURACIÓN DE SEGURIDAD Y PRIVACIDAD
# ========================================================================

SECURITY_CONFIG = {
    "max_file_size_mb": 50,
    "allowed_file_types": [".pdf", ".docx", ".doc", ".txt", ".md"],
    "blocked_domains": [
        "malware.com",
        "phishing.com",
        "spam-site.com"
    ],
    "sanitize_input": True,
    "audit_logging": True,
    "gdpr_compliance": True,
    "data_retention_days": 90
}

# ========================================================================
# CONFIGURACIÓN DE RATE LIMITING
# ========================================================================

RATE_LIMITS = {
    "web_search": {
        "requests_per_minute": 30,
        "burst_limit": 10,
        "cooldown_seconds": 60
    },
    "document_analysis": {
        "requests_per_minute": 20,
        "burst_limit": 5,
        "cooldown_seconds": 30
    },
    "fact_checking": {
        "requests_per_minute": 25,
        "burst_limit": 8,
        "cooldown_seconds": 45
    },
    "academic_search": {
        "requests_per_minute": 15,
        "burst_limit": 3,
        "cooldown_seconds": 120
    }
}

# ========================================================================
# CONFIGURACIÓN DE LOGGING
# ========================================================================

LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_path": "./logs/researcher_agent.log",
    "max_file_size_mb": 100,
    "backup_count": 5,
    "sensitive_data_filter": True
}

# ========================================================================
# FUNCIONES DE UTILIDAD
# ========================================================================

def get_search_api_config() -> Dict[str, Any]:
    """Retorna la configuración de APIs de búsqueda."""
    return SEARCH_APIS_CONFIG

def get_extraction_patterns() -> Dict[str, Any]:
    """Retorna los patrones de extracción de datos."""
    return EXTRACTION_PATTERNS

def get_report_templates() -> Dict[str, Any]:
    """Retorna los templates de reportes."""
    return REPORT_TEMPLATES

def get_trusted_domains() -> Dict[str, Any]:
    """Retorna los dominios de confianza."""
    return TRUSTED_DOMAINS

def get_topic_keywords() -> Dict[str, Any]:
    """Retorna las palabras clave por tema."""
    return TOPIC_KEYWORDS

def is_trusted_domain(url: str) -> tuple[bool, float]:
    """
    Verifica si un dominio es de confianza.
    
    Returns:
        tuple: (is_trusted, trust_score)
    """
    from urllib.parse import urlparse
    
    try:
        domain = urlparse(url).netloc.lower()
        
        for trust_level, config in TRUSTED_DOMAINS.items():
            for trusted_domain in config["domains"]:
                if trusted_domain in domain:
                    return True, config["trust_score"]
        
        return False, 0.3  # Default low trust
    except Exception:
        return False, 0.0

def get_rate_limit(operation: str) -> Dict[str, Any]:
    """Retorna los límites de velocidad para una operación específica."""
    return RATE_LIMITS.get(operation, {
        "requests_per_minute": 20,
        "burst_limit": 5,
        "cooldown_seconds": 30
    })

def get_config_summary() -> Dict[str, Any]:
    """Retorna un resumen de toda la configuración."""
    return {
        "search_apis": len(SEARCH_APIS_CONFIG),
        "academic_databases": len(ACADEMIC_DATABASES),
        "extraction_patterns": len(EXTRACTION_PATTERNS),
        "report_templates": len(REPORT_TEMPLATES),
        "trusted_domains": sum(len(config["domains"]) for config in TRUSTED_DOMAINS.values()),
        "topic_categories": len(TOPIC_KEYWORDS),
        "rate_limits_configured": len(RATE_LIMITS),
        "cache_enabled": CACHE_CONFIG["enabled"],
        "telemetry_enabled": TELEMETRY_CONFIG["enabled"],
        "security_level": "high" if SECURITY_CONFIG["gdpr_compliance"] else "medium"
    }
