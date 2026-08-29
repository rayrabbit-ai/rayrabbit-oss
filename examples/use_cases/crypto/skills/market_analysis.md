---
name: market_analysis
description: Protocolo estándar para el análisis de mercados de criptomonedas antes de ejecutar cualquier operación.
---

# Skill: Market Analysis

Cuando se te solicite analizar una moneda o el mercado en general, debes seguir estrictamente este flujo de trabajo:

1. **Obtención del Precio Spot**:
   - Usa la herramienta `get_crypto_price(symbol)` para obtener el precio en tiempo real desde Binance.
   - Si la moneda no existe, reporta el error y detén el análisis.

2. **Evaluación de Profundidad**:
   - Usa `get_order_book_depth(symbol)` para obtener los niveles de soporte y resistencia inmediatos.
   - No te bases en datos históricos, solo en el order book actual devuelto por la herramienta.

3. **Decisión de Trading (Simulada para A2UI)**:
   - Si la profundidad indica un fuerte soporte y el precio spot está por debajo de los promedios históricos de tu conocimiento, considera la recomendación de "COMPRA".
   - Genera el objeto A2UI para mostrar el precio y el análisis en un `Card` para la UI del usuario.
