# Contribuir a RayRabbit

¡Nos entusiasma enormemente que desee colaborar en la infraestructura de interoperabilidad agéntica de próxima generación de RayRabbit!

Al ser una base de código de código abierto regulada bajo la licencia **GNU Affero General Public License v3 (AGPL-3.0)**, exigimos el cumplimiento estricto de estándares de código, patrones de seguridad y suites de prueba para asegurar la robustez de la red.

---

## Código de Conducta

Al participar en este repositorio, se compromete a respetar nuestro Código de Conducta y a asegurar una comunicación profesional, asertiva y basada en el respeto en todo momento.

---

## Entorno de Desarrollo

Para configurar su espacio de trabajo local y herramientas de desarrollo, consulte nuestra [Guía de Instalación](getting-started/installation.md).

### 1. Herramientas de Calidad de Código
```bash
pip install -e .[dev]
```

### 2. Normas de Estilo de PEP 8
RayRabbit mantiene directrices de código estrictas basadas en el estándar **PEP 8**:
* Es obligatorio anotar de forma estática los tipos de datos en todos los módulos y funciones.
* Proporcione docstrings detallados en todas las clases, módulos y métodos públicos.
* Garantice que la totalidad de los flujos de comunicación asíncrona utilicen `async`/`await`.

---

## Directrices de Pruebas

Enforzamos un **100% de cobertura de código** en los componentes nucleares de comunicación (`message_bus`), transporte y criptografía de la suite MAESTRO. Verifique sus aportaciones ejecutando:

```bash
# Correr la totalidad de pruebas unitarias y de integración
pytest

# Generar reporte de cobertura de código
pytest --cov=rayrabbit
```

---

## Flujo de Ramas y Pull Requests (PR)

1. Realice un Fork del repositorio en GitHub.
2. Cree una rama limpia partiendo de `main` o `master`:
   ```bash
   git checkout -b feature/mi-mejora-increible
   ```
3. Realice sus commits siguiendo convenciones semánticas descriptivas:
   ```bash
   git commit -m "feat(security): integrate JWS verification on websocket ingest"
   ```
4. Suba su rama a su repositorio en GitHub:
   ```bash
   git push origin feature/mi-mejora-increible
   ```
5. Abra un Pull Request en el repositorio oficial. El sistema de CI/CD ejecutará los tests automáticos antes de validar el merge.
