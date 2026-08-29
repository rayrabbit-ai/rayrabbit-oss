"""
Ejemplo de configuración para ResearcherAgent Enterprise

Este archivo muestra diferentes configuraciones para el ResearcherAgent
según diferentes casos de uso y entornos.

Autor: RayRabbit Enterprise
Versión: 1.0.0
"""

# ========================================================================
# CONFIGURACIÓN BÁSICA PARA DESARROLLO
# ========================================================================

DEVELOPMENT_CONFIG = {
    # Configuración principal
    "research_mode": "basic",  # basic, comprehensive, deep
    "max_concurrent_searches": 3,
    "cache_enabled": True,
    "cache_duration_hours": 6,  # Cache corto para desarrollo
    "fact_check_enabled": True,
    "academic_mode": True,
    "rate_limit_delay": 2.0,  # Delay mayor para evitar rate limits
    "max_sources_per_query": 5,  # Pocos resultados para desarrollo rápido
    "report_template": "default"
}

# ========================================================================
# CONFIGURACIÓN PARA PRODUCCIÓN
# ========================================================================

PRODUCTION_CONFIG = {
    "research_mode": "comprehensive",
    "max_concurrent_searches": 8,
    "cache_enabled": True,
    "cache_duration_hours": 48,  # Cache largo para producción
    "fact_check_enabled": True,
    "academic_mode": True,
    "rate_limit_delay": 0.5,
    "max_sources_per_query": 15,
    "report_template": "default"
}

# ========================================================================
# CONFIGURACIÓN PARA INVESTIGACIÓN INTENSIVA
# ========================================================================

INTENSIVE_RESEARCH_CONFIG = {
    "research_mode": "deep",
    "max_concurrent_searches": 12,
    "cache_enabled": True,
    "cache_duration_hours": 168,  # 1 semana de cache
    "fact_check_enabled": True,
    "academic_mode": True,
    "rate_limit_delay": 0.3,
    "max_sources_per_query": 25,
    "report_template": "default"
}

# ========================================================================
# CONFIGURACIÓN PARA ANÁLISIS ACADÉMICO
# ========================================================================

ACADEMIC_CONFIG = {
    "research_mode": "comprehensive",
    "max_concurrent_searches": 5,
    "cache_enabled": True,
    "cache_duration_hours": 72,  # 3 días para papers académicos
    "fact_check_enabled": True,
    "academic_mode": True,  # Priorizar bases académicas
    "rate_limit_delay": 1.5,
    "max_sources_per_query": 20,
    "report_template": "academic_paper"
}

# ========================================================================
# CONFIGURACIÓN PARA VERIFICACIÓN DE HECHOS
# ========================================================================

FACT_CHECK_CONFIG = {
    "research_mode": "comprehensive",
    "max_concurrent_searches": 6,
    "cache_enabled": True,
    "cache_duration_hours": 12,  # Cache corto para información actual
    "fact_check_enabled": True,  # Alta prioridad a fact checking
    "academic_mode": True,
    "rate_limit_delay": 1.0,
    "max_sources_per_query": 12,
    "report_template": "fact_check_report"
}

# ========================================================================
# CONFIGURACIÓN PARA ANÁLISIS COMPETITIVO
# ========================================================================

COMPETITIVE_ANALYSIS_CONFIG = {
    "research_mode": "comprehensive",
    "max_concurrent_searches": 7,
    "cache_enabled": True,
    "cache_duration_hours": 24,
    "fact_check_enabled": True,
    "academic_mode": False,  # Menos énfasis en fuentes académicas
    "rate_limit_delay": 0.8,
    "max_sources_per_query": 18,
    "report_template": "competitive_analysis"
}

# ========================================================================
# CONFIGURACIÓN PARA ANÁLISIS DE TENDENCIAS
# ========================================================================

TREND_ANALYSIS_CONFIG = {
    "research_mode": "comprehensive",
    "max_concurrent_searches": 8,
    "cache_enabled": True,
    "cache_duration_hours": 36,  # Cache mediano para tendencias
    "fact_check_enabled": True,
    "academic_mode": True,
    "rate_limit_delay": 0.7,
    "max_sources_per_query": 20,
    "report_template": "trend_analysis"
}

# ========================================================================
# CONFIGURACIÓN MÍNIMA (SIN APIS EXTERNAS)
# ========================================================================

MINIMAL_CONFIG = {
    "research_mode": "basic",
    "max_concurrent_searches": 1,
    "cache_enabled": False,  # Sin cache para evitar almacenamiento
    "cache_duration_hours": 1,
    "fact_check_enabled": False,  # Sin fact checking
    "academic_mode": False,  # Sin búsqueda académica
    "rate_limit_delay": 3.0,
    "max_sources_per_query": 3,
    "report_template": "default"
}

# ========================================================================
# CONFIGURACIÓN PARA ENTORNOS RESTRINGIDOS
# ========================================================================

SECURE_CONFIG = {
    "research_mode": "basic",
    "max_concurrent_searches": 2,
    "cache_enabled": False,  # Sin cache por seguridad
    "cache_duration_hours": 1,
    "fact_check_enabled": True,
    "academic_mode": True,
    "rate_limit_delay": 2.0,
    "max_sources_per_query": 8,
    "report_template": "default",
    "audit_logging": True,
    "sensitive_data_filter": True,
    "gdpr_compliance": True
}

# ========================================================================
# CONFIGURACIÓN CON APIs EXTERNAS CONFIGURADAS
# ========================================================================

API_ENHANCED_CONFIG = {
    "research_mode": "comprehensive",
    "max_concurrent_searches": 10,
    "cache_enabled": True,
    "cache_duration_hours": 72,
    "fact_check_enabled": True,
    "academic_mode": True,
    "rate_limit_delay": 0.4,  # Delay mínimo con APIs pagadas
    "max_sources_per_query": 20,
    "report_template": "default",
    "enable_premium_apis": True,  # Habilitar APIs premium si están disponibles
    "api_timeout": 30,  # Timeout para APIs externas
    "retry_failed_requests": True
}

# ========================================================================
# FUNCIONES DE UTILIDAD PARA CONFIGURACIÓN
# ========================================================================

def get_config_for_use_case(use_case: str) -> dict:
    """
    Retorna configuración optimizada para un caso de uso específico.
    
    Args:
        use_case: Tipo de uso ("development", "production", "academic", etc.)
        
    Returns:
        dict: Configuración optimizada
    """
    configs = {
        "development": DEVELOPMENT_CONFIG,
        "production": PRODUCTION_CONFIG,
        "intensive": INTENSIVE_RESEARCH_CONFIG,
        "academic": ACADEMIC_CONFIG,
        "fact_check": FACT_CHECK_CONFIG,
        "competitive": COMPETITIVE_ANALYSIS_CONFIG,
        "trends": TREND_ANALYSIS_CONFIG,
        "minimal": MINIMAL_CONFIG,
        "secure": SECURE_CONFIG,
        "api_enhanced": API_ENHANCED_CONFIG
    }
    
    return configs.get(use_case, DEVELOPMENT_CONFIG)

def validate_config(config: dict) -> tuple[bool, list]:
    """
    Valida una configuración del ResearcherAgent.
    
    Args:
        config: Configuración a validar
        
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    # Validar research_mode
    valid_modes = ["basic", "comprehensive", "deep"]
    if config.get("research_mode") not in valid_modes:
        errors.append(f"research_mode debe ser uno de: {valid_modes}")
    
    # Validar números enteros
    int_fields = [
        "max_concurrent_searches", "cache_duration_hours", 
        "max_sources_per_query"
    ]
    for field in int_fields:
        if field in config:
            try:
                value = int(config[field])
                if field == "max_concurrent_searches" and (value < 1 or value > 20):
                    errors.append(f"{field} debe estar entre 1 y 20")
                elif field == "cache_duration_hours" and (value < 1 or value > 168):
                    errors.append(f"{field} debe estar entre 1 y 168 horas")
                elif field == "max_sources_per_query" and (value < 1 or value > 50):
                    errors.append(f"{field} debe estar entre 1 y 50")
            except (ValueError, TypeError):
                errors.append(f"{field} debe ser un número entero")
    
    # Validar números decimales
    if "rate_limit_delay" in config:
        try:
            value = float(config["rate_limit_delay"])
            if value < 0.1 or value > 10.0:
                errors.append("rate_limit_delay debe estar entre 0.1 y 10.0")
        except (ValueError, TypeError):
            errors.append("rate_limit_delay debe ser un número decimal")
    
    # Validar booleanos
    bool_fields = ["cache_enabled", "fact_check_enabled", "academic_mode"]
    for field in bool_fields:
        if field in config and not isinstance(config[field], bool):
            errors.append(f"{field} debe ser un valor booleano")
    
    # Validar report_template
    valid_templates = ["default", "executive_summary", "research_report", 
                      "competitive_analysis", "trend_analysis", "academic_paper", 
                      "fact_check_report"]
    if config.get("report_template") not in valid_templates:
        errors.append(f"report_template debe ser uno de: {valid_templates}")
    
    return len(errors) == 0, errors

def merge_configs(base_config: dict, overrides: dict) -> dict:
    """
    Combina una configuración base con overrides.
    
    Args:
        base_config: Configuración base
        overrides: Configuración que sobrescribe la base
        
    Returns:
        dict: Configuración combinada
    """
    merged = base_config.copy()
    merged.update(overrides)
    return merged

def get_environment_config() -> dict:
    """
    Obtiene configuración basada en variables de entorno.
    
    Returns:
        dict: Configuración basada en entorno
    """
    import os
    
    # Configuración base según entorno
    env = os.getenv("RESEARCHER_AGENT_ENV", "development")
    config = get_config_for_use_case(env)
    
    # Aplicar overrides desde variables de entorno
    env_overrides = {}
    
    if os.getenv("RESEARCHER_CACHE_ENABLED"):
        env_overrides["cache_enabled"] = os.getenv("RESEARCHER_CACHE_ENABLED").lower() == "true"
    
    if os.getenv("RESEARCHER_MAX_SEARCHES"):
        try:
            env_overrides["max_concurrent_searches"] = int(os.getenv("RESEARCHER_MAX_SEARCHES"))
        except ValueError:
            pass
    
    if os.getenv("RESEARCHER_RATE_LIMIT"):
        try:
            env_overrides["rate_limit_delay"] = float(os.getenv("RESEARCHER_RATE_LIMIT"))
        except ValueError:
            pass
    
    return merge_configs(config, env_overrides)

def print_config_summary(config: dict):
    """Imprime un resumen de la configuración."""
    print("RESUMEN DE CONFIGURACIÓN - RESEARCHERAGENT")
    print("=" * 50)
    print(f"Modo de investigación: {config.get('research_mode', 'N/A')}")
    print(f"Búsquedas concurrentes: {config.get('max_concurrent_searches', 'N/A')}")
    print(f"Cache habilitado: {'Sí' if config.get('cache_enabled') else 'No'}")
    print(f"Duración del cache: {config.get('cache_duration_hours', 'N/A')} horas")
    print(f"Fact checking: {'Sí' if config.get('fact_check_enabled') else 'No'}")
    print(f"Modo académico: {'Sí' if config.get('academic_mode') else 'No'}")
    print(f"Delay entre búsquedas: {config.get('rate_limit_delay', 'N/A')}s")
    print(f"Máx fuentes por consulta: {config.get('max_sources_per_query', 'N/A')}")
    print(f"Template de reporte: {config.get('report_template', 'N/A')}")
    print("=" * 50)

# ========================================================================
# EJEMPLO DE USO
# ========================================================================

if __name__ == "__main__":
    # Ejemplo de uso de configuraciones
    
    print("CONFIGURACIONES DISPONIBLES PARA RESEARCHERAGENT")
    print("=" * 60)
    
    # Mostrar configuración de desarrollo
    print("\n1. Configuración de Desarrollo:")
    print_config_summary(DEVELOPMENT_CONFIG)
    
    # Mostrar configuración de producción
    print("\n2. Configuración de Producción:")
    print_config_summary(PRODUCTION_CONFIG)
    
    # Mostrar configuración académica
    print("\n3. Configuración Académica:")
    print_config_summary(ACADEMIC_CONFIG)
    
    # Validar configuración
    print("\n4. Validación de Configuración:")
    is_valid, errors = validate_config(PRODUCTION_CONFIG)
    if is_valid:
        print("✓ Configuración de producción válida")
    else:
        print("✗ Errores encontrados:")
        for error in errors:
            print(f"  - {error}")
    
    # Configuración desde entorno
    print("\n5. Configuración desde Entorno:")
    env_config = get_environment_config()
    print_config_summary(env_config)
