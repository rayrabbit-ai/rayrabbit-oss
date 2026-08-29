# RayRabbit OpenSpec — Spec-Driven Development (SDD) Standard

Welcome to the **OpenSpec (SDD)** engineering standard of **RayRabbit OSS**.

In RayRabbit, every architectural change, communication protocol, and core evolution adheres to the **Spec-Driven Development (SDD)** workflow to ensure mathematical rigor, cross-platform parity, and zero regressions in the L3 infrastructure.

---

## Development Philosophy

1. **Design Before Implementation**: No production code is modified without an approved proposal (`proposal.md`), technical specifications (`specs/`), and verified task checklists (`tasks.md`).
2. **Zero Mocks in Production**: Every specification must yield 100% functional, tested, and deterministic code.
3. **Environment Agnosticism**: All path handling strictly uses `pathlib.Path`, and transports enforce Star Topology isolation.

---

## Using OpenSpec with AI Coding Assistants

RayRabbit integrates native automated workflows for AI coding assistants (Antigravity, Claude Code, Cursor, Codex, OpenHands).

### 1. OpenSpec CLI Installation
If you wish to manage proposals and specifications from your terminal:

```bash
# Install OpenSpec CLI globally via npm
npm install -g @fission-codes/openspec

# Or use integrated slash commands in your AI assistant:
/opsx:propose   # Propose a new capability or architectural change
/opsx:apply     # Apply tasks from an approved change
/opsx:explore   # Thinking, exploration, and audit session
```

### 2. Directory Layout

* **`config.yaml`**: Project architectural rules, MAESTRO Zero-Trust security directives, protocol contracts (A2A, MCP, A2UI), and proposal schema validators.
* **`specs/`**: Formal system specifications organized by capability domain.
* **`changes/`**: Local workspace for active proposals, designs, and task trackers.

---

## Validation Rules
Refer to [`config.yaml`](./config.yaml) for strict validation constraints enforced automatically during change lifecycle reviews.

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# 📐 RayRabbit OpenSpec — Spec-Driven Development (SDD) Standard

Bienvenido a la especificación de ingeniería **OpenSpec (SDD)** de **RayRabbit OSS**.

En RayRabbit, todo cambio arquitectónico, protocolo de comunicación o evolución del núcleo sigue la metodología **Spec-Driven Development (SDD)** para garantizar rigor técnico, paridad entre plataformas y cero regresiones en la infraestructura L3.

---

## Filosofía de Desarrollo

1. **Diseño Previo a la Implementación**: No se modifica código productivo sin una propuesta (proposal.md), especificaciones técnicas (specs/) y tareas verificables (	asks.md).
2. **Cero Mocks en Producción**: Toda especificación debe resultar en código 100% funcional, probado y determinista.
3. **Agnosticismo de Entorno**: Todo manejo de archivos utiliza pathlib.Path y los transportes respetan la Topología en Estrella.

---

## Cómo Utilizar OpenSpec con Asistentes de IA

RayRabbit integra flujos nativos para asistentes de IA (Antigravity, Claude Code, Cursor, Codex, OpenHands).

### 1. Instalación del CLI OpenSpec
Si deseas gestionar propuestas y cambios desde la terminal:

`ash
# Instalar OpenSpec CLI globalmente vía npm
npm install -g @fission-codes/openspec

# O utilizar los comandos integrados en tu asistente de IA
/opsx:propose   # Proponer una nueva capacidad o cambio
/opsx:apply     # Aplicar tareas de un cambio aprobado
/opsx:explore   # Sesión de pensamiento y auditoría
`

### 2. Estructura de este Directorio

* **config.yaml**: Reglas arquitectónicas del proyecto, directivas de seguridad MAESTRO Zero-Trust, contratos de protocolos (A2A, MCP, A2UI) y validaciones de cambios.
* **specs/**: Especificaciones formales del sistema organizadas por capacidades.
* **changes/**: Directorio de trabajo local para propuestas y tareas activas en desarrollo.

---

## Reglas de Validación
Consulta [config.yaml](./config.yaml) para conocer las directivas de validación que los asistentes de IA aplican automáticamente a cada propuesta.

</details>
