# Directivas de RayRabbit para Anthropic Claude Code

Este archivo define las reglas de interacción y contratos operativos cuando Claude Code interactúa con la infraestructura RayRabbit.

## Directivas Esenciales:
1. **Agnosticismo de Entorno**: Usa siempre `pathlib.Path` para manipulación de archivos.
2. **Cero Mocks**: Todo código generado o refactorizado debe ser 100% funcional y probado.
3. **Consumo de Herramientas MCP**: Descubre herramientas dinámicamente mediante `tools/list` filtrando por categoría de dominio.
4. **Seguridad MAESTRO**: Respeta la arquitectura Zero-Trust y nunca expongas claves privadas en logs o código.
