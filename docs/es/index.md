# RayRabbit: Infraestructura Universal y Agnóstica de Interoperabilidad para IA (AI TCP/IP + TLS + HTTP)

Bienvenido a la documentación oficial de **RayRabbit**, el estándar neutral de **Capa L3 (Layer 3)** diseñado para la interconexión y mediación horizontal de agentes de IA heterogéneos.

---

## ¿Qué es RayRabbit?

RayRabbit es a la era de los agentes de Inteligencia Artificial lo que **TCP/IP, TLS y HTTP** fueron para el nacimiento de Internet: la **capa de transporte, seguridad criptográfica e interoperabilidad universal (L3)** que permite a cualquier entidad agéntica comunicarse de forma fluida, segura y sin fricción.

RayRabbit actúa como el sustrato neutral de red que conecta horizontalmente:

1. **SDKs Soberanos y Herramientas Atómicas de Dominio (SDK)**: Scripts, conectores de bases de datos, APIs de negocio y herramientas atómicas registradas mediante el SDK de Python/JavaScript.
2. **Asistentes de Código y Agentes Autónomos Propietarios**: Herramientas de desarrollo como **Claude Code, OpenAI Codex CLI/SDK, Google Antigravity CLI/SDK, OpenHands, Hermes Agent, OpenClaw** y cualquier $N$-Agente autónomo.
3. **Frameworks Cognitivos Heterogéneos**: **CrewAI, AutoGen, LangChain, Microsoft Agent Framework (MAF), LlamaIndex** y cualquier $N$-framework cognitivo.
4. **Portales Visuales Declarativos (A2UI v0.9.1)**: Paneles telemáticos y superficies reactivas renderizadas en tiempo real.

Todo esto mediante **mediación horizontal sin coordinadores centrales ni estado global compartido (Shared-Nothing Architecture)**.

---

## Los Cinco Niveles de Evolución Agéntica

Para comprender el diseño y alcance de RayRabbit, definimos la siguiente taxonomía de redes multi-agente:

| Nivel | Categoría | Descripción Técnica | Capa RayRabbit |
|:---:|:---|:---|:---:|
| **L1** | **Silos Monolíticos** | Agentes limitados a un mismo framework. Comparten espacio de memoria, proceso del sistema y stack. | *Silo Monolítico (Superado)* |
| **L2** | **APIs REST de Acoplamiento** | Conexión de frameworks mediante endpoints REST ad-hoc. Sin estándares de red, keystores ni seguridad criptográfica. | *Puente REST (Superado)* |
| **L3** | **Capa de Red Descentralizada (AI TCP/IP)** | Capa horizontal neutral de transporte e interoperabilidad. Firmas JWS RSA-4096, MessageBus asíncrono, MCPv2 nativo sobre WebSocket, A2UI declarativo y contratos formales. Conecta SDKs soberanos, asistentes de código y frameworks heterogéneos bajo Shared-Nothing. | **RayRabbit OSS** |
| **L4** | **Kernel AIOS / Hypervisor** | Aprovisionamiento dinámico IaC basado en lenguaje natural, sandboxing WebAssembly (`wasmtime`), control de cuotas GPU/Tokens, motor cognitivo AIDA Ouroboros y KMS/HSM corporativo. | **RayRabbit Enterprise** |
| **L5** | **Ecosistemas Auto-Evolutivos** | Enjambres distribuidos globalmente operando en micro-mercados lógicos, auto-replicándose y auto-reparándose. | *Roadmap Activo* |

---

## Explore la Arquitectura

<div class="premium-card" markdown="1">
### Comencemos
¿Listo para desplegar su primer clúster agéntico soberano local? Aprenda a instalar e inicializar RayRabbit en menos de 3 minutos.
* [Instalación Multiplataforma](getting-started/installation.md)
* [Guía de Inicio Rápido](getting-started/quickstart.md)
* [Lanzadores de Clúster Soberanos](guides/launchers.md)
</div>

<div class="premium-card" markdown="1">
### Conceptos Core
Profundice en la estructura lógica y física de los protocolos de RayRabbit.
* [Arquitectura del Hub Universal](concepts/architecture.md)
* [Los 6 Pilares de Interoperabilidad](concepts/pillars.md)
* [Seguridad Zero-Trust MAESTRO](concepts/security.md)
* [Federación de Servicios](concepts/federation.md)
</div>

<div class="premium-card" markdown="1">
### RayRabbit Enterprise: ARK + Hypervisor
Descubra cómo escalar RayRabbit a entornos corporativos de alta seguridad con cumplimiento SOC2, sandboxing y control financiero de APIs.
* [Características Enterprise](enterprise.md)
* [Integración de ARK](concepts/protocols.md)
* [Agente Hypervisor e Isolation](enterprise.md)
</div>

---

## Seguridad y Confianza Absoluta

RayRabbit se diseña desde el primer día bajo una filosofía **Zero-Trust**. Cada instrucción procesada en el **MessageBus** requiere firmas criptográficas bajo el **estándar JWS** mediante **claves asimétricas de alta seguridad**.

A diferencia de los frameworks tradicionales, RayRabbit no confía en tokens estáticos de red. Cada agente es una entidad soberana que protege sus llaves de identidad en su **almacén local de claves** (OSS) o en módulos HSM (Enterprise).
