"""
Templates para Generación de Reportes del ResearcherAgent

Este módulo contiene templates predefinidos para la generación automática
de diferentes tipos de reportes de investigación.

Autor: RayRabbit Enterprise
Versión: 1.0.0
"""

from typing import Dict, Any, List
from datetime import datetime


class ReportTemplates:
    """Clase que contiene todos los templates de reportes."""
    
    # ========================================================================
    # TEMPLATE: RESUMEN EJECUTIVO
    # ========================================================================
    
    EXECUTIVE_SUMMARY_TEMPLATE = """
# RESUMEN EJECUTIVO

**Fecha de análisis:** {analysis_date}
**Consultor:** ResearcherAgent Enterprise
**Período analizado:** {timeframe}

---

## RESUMEN EJECUTIVO

{summary_text}

## HALLAZGOS PRINCIPALES

{findings_section}

## ANÁLISIS DE MERCADO

{market_analysis_section}

## IMPLICACIONES ESTRATÉGICAS

{strategic_implications_section}

## RECOMENDACIONES CLAVE

{recommendations_section}

## MÉTRICAS CLAVE

{metrics_section}

## CONCLUSIONES

{conclusions_section}

---

**Confianza del análisis:** {confidence_score}%
**Fuentes consultadas:** {sources_count}
**Próxima revisión recomendada:** {next_review_date}

---
*Este reporte fue generado automáticamente por ResearcherAgent Enterprise v1.0.0*
"""

    # ========================================================================
    # TEMPLATE: REPORTE DE INVESTIGACIÓN
    # ========================================================================
    
    RESEARCH_REPORT_TEMPLATE = """
# REPORTE DE INVESTIGACIÓN

**Título del estudio:** {study_title}
**Investigador principal:** ResearcherAgent Enterprise
**Fecha de inicio:** {start_date}
**Fecha de finalización:** {end_date}
**Tipo de investigación:** {research_type}

---

## RESUMEN EJECUTIVO

{executive_summary}

## 1. INTRODUCCIÓN

### 1.1 Contexto
{context_section}

### 1.2 Objetivos
{objectives_section}

### 1.3 Hipótesis
{hypothesis_section}

### 1.4 Justificación
{justification_section}

## 2. METODOLOGÍA

### 2.1 Diseño del estudio
{methodology_design}

### 2.2 Fuentes de datos
{data_sources_section}

### 2.3 Criterios de selección
{selection_criteria_section}

### 2.4 Limitaciones metodológicas
{methodological_limitations_section}

## 3. RESULTADOS

### 3.1 Análisis cuantitativo
{quantitative_results_section}

### 3.2 Análisis cualitativo
{qualitative_results_section}

### 3.3 Análisis comparativo
{comparative_analysis_section}

### 3.4 Hallazgos estadísticamente significativos
{statistical_findings_section}

## 4. ANÁLISIS Y DISCUSIÓN

### 4.1 Interpretación de resultados
{results_interpretation_section}

### 4.2 Comparación con literatura existente
{literature_comparison_section}

### 4.3 Implicaciones teóricas
{theoretical_implications_section}

### 4.4 Implicaciones prácticas
{practical_implications_section}

## 5. LIMITACIONES

{limitations_section}

## 6. RECOMENDACIONES

### 6.1 Recomendaciones para investigación futura
{future_research_recommendations_section}

### 6.2 Recomendaciones para la práctica
{practice_recommendations_section}

### 6.3 Recomendaciones para políticas
{policy_recommendations_section}

## 7. CONCLUSIONES

{conclusions_section}

## 8. REFERENCIAS BIBLIOGRÁFICAS

{references_section}

---

## ANEXOS

### Anexo A: Datos tabulares detallados
{detailed_data_section}

### Anexo B: Metodología estadística detallada
{statistical_methodology_section}

### Anexo C: Lista de fuentes consultadas
{sources_detailed_section}

---
*Fecha de generación: {generation_date}*
*Sistema: ResearcherAgent Enterprise v1.0.0*
"""

    # ========================================================================
    # TEMPLATE: ANÁLISIS COMPETITIVO
    # ========================================================================
    
    COMPETITIVE_ANALYSIS_TEMPLATE = """
# ANÁLISIS COMPETITIVO

**Industria/Mercado:** {industry_sector}
**Alcance geográfico:** {geographic_scope}
**Período de análisis:** {analysis_period}
**Fecha del reporte:** {report_date}

---

## RESUMEN EJECUTIVO

{executive_summary}

## 1. PANORAMA DEL MERCADO

### 1.1 Tamaño del mercado
{market_size_section}

### 1.2 Tendencias del mercado
{market_trends_section}

### 1.3 Segmentación del mercado
{market_segmentation_section}

### 1.4 Factores de crecimiento
{growth_factors_section}

## 2. ANÁLISIS DE COMPETIDORES

### 2.1 Competidores principales
{top_competitors_section}

### 2.2 Matriz competitiva
{competitive_matrix_section}

### 2.3 Análisis individual de competidores

#### 2.3.1 {competitor_1_name}
- **Posición en el mercado:** {competitor_1_position}
- **Fortalezas principales:** {competitor_1_strengths}
- **Debilidades identificadas:** {competitor_1_weaknesses}
- **Estrategia actual:** {competitor_1_strategy}
- **Cuota de mercado:** {competitor_1_market_share}

#### 2.3.2 {competitor_2_name}
- **Posición en el mercado:** {competitor_2_position}
- **Fortalezas principales:** {competitor_2_strengths}
- **Debilidades identificadas:** {competitor_2_weaknesses}
- **Estrategia actual:** {competitor_2_strategy}
- **Cuota de mercado:** {competitor_2_market_share}

#### 2.3.3 {competitor_3_name}
- **Posición en el mercado:** {competitor_3_position}
- **Fortalezas principales:** {competitor_3_strengths}
- **Debilidades identificadas:** {competitor_3_weaknesses}
- **Estrategia actual:** {competitor_3_strategy}
- **Cuota de mercado:** {competitor_3_market_share}

## 3. ANÁLISIS FODA COMPETITIVO

### 3.1 Fortalezas de la industria
{industry_strengths_section}

### 3.2 Oportunidades de mercado
{market_opportunities_section}

### 3.3 Debilidades identificadas
{industry_weaknesses_section}

### 3.4 Amenazas del entorno
{environmental_threats_section}

## 4. POSICIONAMIENTO COMPETITIVO

### 4.1 Mapa de posicionamiento
{positioning_map_section}

### 4.2 Barreras de entrada
{entry_barriers_section}

### 4.3 Factores diferenciadores
{differentiating_factors_section}

### 4.4 Estrategias competitivas observadas
{competitive_strategies_section}

## 5. ANÁLISIS FINANCIERO COMPARATIVO

### 5.1 Indicadores financieros clave
{financial_indicators_section}

### 5.2 Análisis de rentabilidad
{profitability_analysis_section}

### 5.3 Eficiencia operativa
{operational_efficiency_section}

### 5.4 Capacidad de innovación
{innovation_capacity_section}

## 6. IMPLICACIONES ESTRATÉGICAS

### 6.1 Oportunidades identificadas
{opportunities_identified_section}

### 6.2 Amenazas a considerar
{threats_to_consider_section}

### 6.3 Gaps en el mercado
{market_gaps_section}

### 6.4 Ventajas competitivas potenciales
{potential_competitive_advantages_section}

## 7. RECOMENDACIONES ESTRATÉGICAS

### 7.1 Estrategia de diferenciación
{differentiation_strategy_section}

### 7.2 Estrategia de posicionamiento
{positioning_strategy_section}

### 7.3 Estrategia de desarrollo de productos
{product_development_strategy_section}

### 7.4 Estrategia de precios
{pricing_strategy_section}

### 7.5 Estrategia de mercado
{market_strategy_section}

## 8. PLAN DE ACCIÓN

### 8.1 Acciones a corto plazo (0-6 meses)
{short_term_actions_section}

### 8.2 Acciones a mediano plazo (6-18 meses)
{medium_term_actions_section}

### 8.3 Acciones a largo plazo (18+ meses)
{long_term_actions_section}

## 9. CONCLUSIONES

{conclusions_section}

---

**Nivel de confianza del análisis:** {confidence_level}%
**Competidores analizados:** {competitors_analyzed}
**Fuentes de información consultadas:** {information_sources}
**Próxima actualización recomendada:** {next_update_recommended}

---
*Generado por ResearcherAgent Enterprise v1.0.0*
*Fecha: {generation_timestamp}*
"""

    # ========================================================================
    # TEMPLATE: ANÁLISIS DE TENDENCIAS
    # ========================================================================
    
    TREND_ANALYSIS_TEMPLATE = """
# ANÁLISIS DE TENDENCIAS

**Tema analizado:** {topic_analyzed}
**Período de estudio:** {study_period}
**Horizonte temporal:** {time_horizon}
**Fecha de análisis:** {analysis_date}

---

## RESUMEN EJECUTIVO

{executive_summary}

## 1. METODOLOGÍA DE ANÁLISIS

### 1.1 Fuentes de datos
{data_sources_methodology}

### 1.2 Período de observación
{observation_period}

### 1.3 Herramientas de análisis
{analysis_tools}

### 1.4 Limitaciones del análisis
{analysis_limitations}

## 2. TENDENCIAS IDENTIFICADAS

### 2.1 Tendencia Principal #1: {trend_1_name}
- **Dirección:** {trend_1_direction}
- **Magnitud:** {trend_1_magnitude}
- **Velocidad de cambio:** {trend_1_velocity}
- **Persistencia:** {trend_1_persistence}
- **Impacto esperado:** {trend_1_impact}

### 2.2 Tendencia Principal #2: {trend_2_name}
- **Dirección:** {trend_2_direction}
- **Magnitud:** {trend_2_magnitude}
- **Velocidad de cambio:** {trend_2_velocity}
- **Persistencia:** {trend_2_persistence}
- **Impacto esperado:** {trend_2_impact}

### 2.3 Tendencia Principal #3: {trend_3_name}
- **Dirección:** {trend_3_direction}
- **Magnitud:** {trend_3_magnitude}
- **Velocidad de cambio:** {trend_3_velocity}
- **Persistencia:** {trend_3_persistence}
- **Impacto esperado:** {trend_3_impact}

## 3. ANÁLISIS TEMPORAL

### 3.1 Evolución histórica
{historical_evolution_section}

### 3.2 Puntos de inflexión históricos
{inflection_points_section}

### 3.3 Patrones estacionales
{seasonal_patterns_section}

### 3.4 Correlaciones temporales
{temporal_correlations_section}

## 4. ANÁLISIS DE SENTIMIENTO

### 4.1 Sentimiento general del mercado
{general_market_sentiment_section}

### 4.2 Evolución del sentimiento
{sentiment_evolution_section}

### 4.3 Sentimiento por segmentos
{segment_sentiment_section}

### 4.4 Factores que influyen en el sentimiento
{sentiment_influencing_factors_section}

## 5. FACTORES IMPULSORES

### 5.1 Factores tecnológicos
{technological_drivers_section}

### 5.2 Factores económicos
{economic_drivers_section}

### 5.3 Factores sociales
{social_drivers_section}

### 5.4 Factores regulatorios
{regulatory_drivers_section}

### 5.5 Factores ambientales
{environmental_drivers_section}

## 6. ANÁLISIS DE IMPACTO

### 6.1 Impacto en la industria
{industry_impact_section}

### 6.2 Impacto en los consumidores
{consumer_impact_section}

### 6.3 Impacto en la cadena de suministro
{supply_chain_impact_section}

### 6.4 Impacto en la inversión
{investment_impact_section}

## 7. PREDICCIONES Y PROYECCIONES

### 7.1 Proyecciones a corto plazo (0-6 meses)
{short_term_predictions_section}

### 7.2 Proyecciones a mediano plazo (6-18 meses)
{medium_term_predictions_section}

### 7.3 Proyecciones a largo plazo (18+ meses)
{long_term_predictions_section}

### 7.4 Escenarios futuros
{future_scenarios_section}

## 8. ANÁLISIS DE RIESGOS

### 8.1 Riesgos asociados a las tendencias
{trend_related_risks_section}

### 8.2 Riesgos de no adaptación
{non_adaptation_risks_section}

### 8.3 Riesgos de volatilidad
{volatility_risks_section}

### 8.4 Factores de incertidumbre
{uncertainty_factors_section}

## 9. IMPLICACIONES ESTRATÉGICAS

### 9.1 Oportunidades de negocio
{business_opportunities_section}

### 9.2 Amenazas emergentes
{emerging_threats_section}

### 9.3 Necesidades de adaptación
{adaptation_needs_section}

### 9.4 Innovaciones requeridas
{required_innovations_section}

## 10. RECOMENDACIONES

### 10.1 Recomendaciones estratégicas
{strategic_recommendations_section}

### 10.2 Recomendaciones operativas
{operational_recommendations_section}

### 10.3 Recomendaciones de inversión
{investment_recommendations_section}

### 10.4 Recomendaciones de gestión de riesgos
{risk_management_recommendations_section}

## 11. PLAN DE SEGUIMIENTO

### 11.1 Indicadores de seguimiento
{tracking_indicators_section}

### 11.2 Frecuencia de monitoreo
{monitoring_frequency_section}

### 11.3 Criterios de alerta temprana
{early_warning_criteria_section}

### 11.4 Plan de revisión
{review_plan_section}

## 12. CONCLUSIONES

{conclusions_section}

---

**Nivel de confianza en las tendencias:** {confidence_level}%
**Precisión de las predicciones:** {prediction_accuracy}%
**Fuentes de datos analizadas:** {data_sources_analyzed}
**Período de validez de este análisis:** {validity_period}

---
*Análisis generado por ResearcherAgent Enterprise v1.0.0*
*Fecha de generación: {generation_timestamp}*
"""

    # ========================================================================
    # TEMPLATE: PAPER ACADÉMICO
    # ========================================================================
    
    ACADEMIC_PAPER_TEMPLATE = """
# {paper_title}

**Autor(es):** {authors}
**Afiliación:** {affiliation}
**Fecha de publicación:** {publication_date}
**Fecha de recepción:** {received_date}
**Fecha de aceptación:** {accepted_date}

---

## RESUMEN

{abstract}

**Palabras clave:** {keywords}

## 1. INTRODUCCIÓN

### 1.1 Contexto y motivación
{context_motivation_section}

### 1.2 Problema de investigación
{research_problem_section}

### 1.3 Objetivos del estudio
{study_objectives_section}

### 1.4 Contribuciones del trabajo
{work_contributions_section}

### 1.5 Estructura del documento
{document_structure_section}

## 2. TRABAJO RELACIONADO

### 2.1 Literatura relevante
{relevant_literature_section}

### 2.2 Estado del arte
{state_of_art_section}

### 2.3 Brechas identificadas
{identified_gaps_section}

### 2.4 Posicionamiento del trabajo
{work_positioning_section}

## 3. METODOLOGÍA

### 3.1 Diseño de investigación
{research_design_section}

### 3.2 Descripción de métodos
{methods_description_section}

### 3.3 Protocolo experimental
{experimental_protocol_section}

### 3.4 Instrumentos de medición
{measurement_instruments_section}

### 3.5 Validación de métodos
{methods_validation_section}

### 3.6 Consideraciones éticas
{ethical_considerations_section}

## 4. RESULTADOS

### 4.1 Resultados descriptivos
{descriptive_results_section}

### 4.2 Análisis estadístico
{statistical_analysis_section}

### 4.3 Comparación de grupos
{group_comparison_section}

### 4.4 Correlaciones y relaciones
{correlations_relations_section}

### 4.5 Validación de hipótesis
{hypothesis_validation_section}

### 4.6 Análisis de sensibilidad
{sensitivity_analysis_section}

## 5. DISCUSIÓN

### 5.1 Interpretación de resultados
{results_interpretation_section}

### 5.2 Implicaciones teóricas
{theoretical_implications_section}

### 5.3 Implicaciones prácticas
{practical_implications_section}

### 5.4 Comparación con estudios previos
{previous_studies_comparison_section}

### 5.5 Limitaciones del estudio
{study_limitations_section}

### 5.6 Amenazas a la validez
{validity_threats_section}

## 6. CONCLUSIONES Y TRABAJO FUTURO

### 6.1 Síntesis de hallazgos
{findings_synthesis_section}

### 6.2 Contribuciones principales
{main_contributions_section}

### 6.3 Implicaciones para la práctica
{practice_implications_section}

### 6.4 Implicaciones para la investigación
{research_implications_section}

### 6.5 Trabajo futuro
{future_work_section}

### 6.6 Recomendaciones finales
{final_recommendations_section}

## REFERENCIAS

{references_section}

## ANEXOS

### Anexo A: Instrumentos utilizados
{used_instruments_section}

### Anexo B: Datos adicionales
{additional_data_section}

### Anexo C: Análisis estadístico detallado
{detailed_statistical_analysis_section}

### Anexo D: Código y materiales complementarios
{supplementary_materials_section}

---

**Número de palabras:** {word_count}
**Número de figuras:** {figure_count}
**Número de tablas:** {table_count}
**Referencias citadas:** {cited_references_count}

---
*Manuscrito recibido el {received_date_formatted}*
*Manuscrito aceptado el {accepted_date_formatted}*
*Versión final publicada el {final_publication_date_formatted}*

---
*Generado por ResearcherAgent Enterprise v1.0.0*
"""

    # ========================================================================
    # TEMPLATE: REPORTE DE VERIFICACIÓN DE HECHOS
    # ========================================================================
    
    FACT_CHECK_REPORT_TEMPLATE = """
# REPORTE DE VERIFICACIÓN DE HECHOS

**Afirmación analizada:** "{fact_claim}"
**Fecha de verificación:** {verification_date}
**Investigador:** ResearcherAgent Enterprise
**Nivel de confianza:** {confidence_level}%

---

## RESUMEN EJECUTIVO

{executive_summary}

## AFIRMACIÓN ORIGINAL

> **"{fact_claim}"**

## METODOLOGÍA DE VERIFICACIÓN

### Fuentes consultadas
{sources_consulted_section}

### Criterios de verificación
{verification_criteria_section}

### Herramientas utilizadas
{tools_used_section}

## EVIDENCIA RECOPILADA

### Evidencia a favor
{supporting_evidence_section}

### Evidencia en contra
{contradicting_evidence_section}

### Evidencia neutral o mixta
{neutral_evidence_section}

## ANÁLISIS DE FUENTES

### Fuentes de alta confiabilidad
{high_reliability_sources_section}

### Fuentes de confiabilidad media
{medium_reliability_sources_section}

### Fuentes de baja confiabilidad
{low_reliability_sources_section}

## ANÁLISIS TEMPORAL

### Antecedentes históricos
{historical_antecedents_section}

### Desarrollo reciente
{recent_developments_section}

### Estado actual
{current_status_section}

## CONTEXTO Y MATIZ

### Contexto relevante
{relevant_context_section}

### Perspectivas múltiples
{multiple_perspectives_section}

### Factores influyentes
{influencing_factors_section}

## EVALUACIÓN DE CREDIBILIDAD

### Evaluación de la afirmación original
{original_claim_assessment_section}

### Evaluación de las evidencias presentadas
{evidence_assessment_section}

### Evaluación del contexto proporcionado
{context_assessment_section}

## ANÁLISIS DE SESGOS

### Posibles sesgos en las fuentes
{source_biases_section}

### Sesgos del investigador
{researcher_biases_section}

### Sesgos del contexto temporal
{temporal_biases_section}

## FACTORES ADICIONALES

### Información faltante
{missing_information_section}

### Inconsistencias encontradas
{inconsistencies_found_section}

### Puntos de incertidumbre
{uncertainty_points_section}

## CONCLUSIONES

### Conclusión principal
{main_conclusion_section}

### Nivel de confianza
{confidence_assessment_section}

### Certidumbre de la verificación
{verification_certainty_section}

### Recomendaciones adicionales
{additional_recommendations_section}

## FUENTES CONSULTADAS

{consulted_sources_section}

## NOTA METODOLÓGICA

{methodological_note_section}

---

**Veredicto final:** {final_verdict}
**Confianza en la verificación:** {final_confidence}%
**Fecha de la próxima revisión:** {next_review_date}

---
*Este reporte fue generado por ResearcherAgent Enterprise v1.0.0*
*Para más información sobre metodología de verificación, consulte: https://researcher-agent.com/methodology*
"""

    # ========================================================================
    # FUNCIONES DE UTILIDAD PARA TEMPLATES
    # ========================================================================
    
    @staticmethod
    def format_section(title: str, content: str, level: int = 2) -> str:
        """Formatea una sección con título."""
        hashes = "#" * level
        return f"\n{hashes} {title}\n\n{content}\n"
    
    @staticmethod
    def format_list(items: List[str], list_type: str = "bulleted") -> str:
        """Formatea una lista de elementos."""
        if not items:
            return ""
        
        if list_type == "numbered":
            return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
        else:
            return "\n".join(f"- {item}" for item in items)
    
    @staticmethod
    def format_table(data: Dict[str, Any], headers: List[str]) -> str:
        """Formatea datos en formato tabla markdown."""
        if not data or not headers:
            return ""
        
        # Header
        table = f"| {' | '.join(headers)} |\n"
        table += f"| {' | '.join(['---'] * len(headers))} |\n"
        
        # Data rows
        for row_data in data if isinstance(data, list) else [data]:
            if isinstance(row_data, dict):
                row_values = [str(row_data.get(header, "")) for header in headers]
            else:
                row_values = [str(row_data)]
            table += f"| {' | '.join(row_values)} |\n"
        
        return table
    
    @staticmethod
    def apply_template(template: str, data: Dict[str, Any]) -> str:
        """Aplica datos a un template."""
        try:
            return template.format(**data)
        except KeyError as e:
            # Reemplazar campos faltantes con valores por defecto
            formatted_template = template
            import re
            placeholders = re.findall(r'\{([^}]+)\}', template)
            
            for placeholder in placeholders:
                key = placeholder
                if key not in data:
                    formatted_template = formatted_template.replace(f"{{{key}}}", f"[{key.upper()}_NO_PROPORCIONADO]")
            
            return formatted_template
    
    @staticmethod
    def get_available_templates() -> Dict[str, str]:
        """Retorna todos los templates disponibles."""
        return {
            "executive_summary": ReportTemplates.EXECUTIVE_SUMMARY_TEMPLATE,
            "research_report": ReportTemplates.RESEARCH_REPORT_TEMPLATE,
            "competitive_analysis": ReportTemplates.COMPETITIVE_ANALYSIS_TEMPLATE,
            "trend_analysis": ReportTemplates.TREND_ANALYSIS_TEMPLATE,
            "academic_paper": ReportTemplates.ACADEMIC_PAPER_TEMPLATE,
            "fact_check_report": ReportTemplates.FACT_CHECK_REPORT_TEMPLATE
        }
    
    @staticmethod
    def validate_template_data(template_name: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Valida que todos los campos requeridos estén presentes."""
        templates = ReportTemplates.get_available_templates()
        
        if template_name not in templates:
            return {"error": [f"Template '{template_name}' no encontrado"]}
        
        template = templates[template_name]
        import re
        
        # Extraer todos los placeholders del template
        placeholders = set(re.findall(r'\{([^}]+)\}', template))
        
        # Encontrar campos faltantes
        missing_fields = []
        for field in placeholders:
            if field not in data:
                missing_fields.append(field)
        
        return {
            "missing_fields": missing_fields,
            "total_placeholders": len(placeholders),
            "provided_fields": len(data),
            "completeness": f"{((len(placeholders) - len(missing_fields)) / len(placeholders) * 100):.1f}%" if placeholders else "100%"
        }


def get_template(template_name: str) -> str:
    """Función de conveniencia para obtener un template."""
    templates = ReportTemplates.get_available_templates()
    return templates.get(template_name, "")


def generate_report_from_template(template_name: str, data: Dict[str, Any]) -> str:
    """Función de conveniencia para generar un reporte."""
    template = get_template(template_name)
    if not template:
        return f"Error: Template '{template_name}' no encontrado"
    
    return ReportTemplates.apply_template(template, data)


def list_available_templates() -> Dict[str, str]:
    """Lista todos los templates disponibles con descripciones."""
    return {
        "executive_summary": "Resumen ejecutivo para tomadores de decisiones",
        "research_report": "Reporte completo de investigación académica",
        "competitive_analysis": "Análisis competitivo detallado",
        "trend_analysis": "Análisis de tendencias del mercado",
        "academic_paper": "Paper académico con formato estándar",
        "fact_check_report": "Reporte de verificación de hechos"
    }
