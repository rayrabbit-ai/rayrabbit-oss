# Directivas de RayRabbit para OpenAI Codex y Cursor

Este archivo define las reglas de desarrollo y contratos para OpenAI Codex y Cursor operando sobre el repositorio `rayrabbit-oss`.

## Directivas Principales:
1. **Agnosticismo de Rutas**: Utiliza `pathlib.Path` exclusivamente; nunca uses `os.path` o `sys.path`.
2. **Sin Placeholders**: Genera código completo y verificable sin funciones dummy o comentarios `// TODO: implement later`.
3. **Validación de Esquemas**: Valida parámetros de herramientas utilizando Pydantic v2 o Zod (en TypeScript).
