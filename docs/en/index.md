# RayRabbit: Universal & Agnostic AI Interoperability Infrastructure (AI TCP/IP + TLS + HTTP)

Welcome to the official documentation for **RayRabbit**, the neutral **Layer 3 (L3)** industry standard designed for horizontal interconnection and mediation of heterogeneous AI agents.

---

## What is RayRabbit?

RayRabbit is to autonomous AI agents what **TCP/IP, TLS, and HTTP** were to the inception of the Internet: the **universal Layer 3 (L3) transport, cryptographic security, and interoperability standard** that enables any agentic entity to communicate seamlessly, securely, and without friction.

RayRabbit serves as the neutral network fabric that horizontally connects:

1. **Sovereign SDKs & Domain Atomic Tools (SDK)**: Scripts, database connectors, business APIs, and atomic functions registered via the Python and JavaScript/TypeScript SDKs.
2. **Proprietary Coding Assistants & Autonomous Agents**: Developer tools such as **Claude Code, OpenAI Codex CLI/SDK, Google Antigravity CLI/SDK, OpenHands, Hermes Agent, OpenClaw**, and any arbitrary $N$-Agent.
3. **Heterogeneous Cognitive Frameworks**: **CrewAI, AutoGen, LangChain, Microsoft Agent Framework (MAF), LlamaIndex**, and any arbitrary $N$-cognitive framework.
4. **Declarative Visual Portals (A2UI v0.9.1)**: Live telemetry dashboards and reactive UI surfaces rendered dynamically in real time.

All orchestrated through **horizontal mediation without central coordinators or shared global state (Shared-Nothing Architecture)**.

---

## The Five Levels of Agentic Evolution

To understand the architecture of RayRabbit, we place it in the context of the technical taxonomy of agentic grids:

| Level | Category | Technical Description | RayRabbit Layer |
|:---:|:---|:---|:---:|
| **L1** | **Monolithic Silos** | Multi-agent pipelines restricted to a single framework. Share process thread, memory, and code stack. | *Legacy Silo (Bypassed)* |
| **L2** | **Ad-hoc REST Bridging** | Connection of heterogeneous agents via custom API endpoints. Lacks transport standards, keystores, or cryptographic trust. | *Legacy Bridge (Bypassed)* |
| **L3** | **Decentralized Network (AI TCP/IP)** | Neutral horizontal transport and interoperability layer. RSA-4096 JWS signatures, asynchronous MessageBus, native WebSocket MCPv2, declarative A2UI, and formal contracts. Connects sovereign SDKs, coding assistants, and heterogeneous frameworks under Shared-Nothing. | **RayRabbit OSS** |
| **L4** | **AIOS Kernel / Hypervisor** | Intent-based IaC provisioning, WebAssembly (`wasmtime`) sandboxing, strict GPU/token quotas, AIDA Ouroboros cognitive defense engine, and enterprise KMS/HSM key rings. | **RayRabbit Enterprise** |
| **L5** | **Cognitive Automorphic Swarms** | Globally federated swarms running in autonomous logical micro-markets, auto-replicating and self-healing. | *Active Roadmap* |

---

## Explore the Architecture

<div class="premium-card" markdown="1">
### Get Started
Ready to deploy your first heterogeneous sovereign cluster? Learn how to install and boot the sovereign cluster in under 3 minutes.
* [Multi-Platform Installation](getting-started/installation.md)
* [Quickstart Guide](getting-started/quickstart.md)
* [Sovereign Cluster Launchers](guides/launchers.md)
</div>

<div class="premium-card" markdown="1">
### Deep Dive into Core Concepts
Understand the physical and logical structure of the RayRabbit protocol suite.
* [Universal Hub Architecture](concepts/architecture.md)
* [The 6 Pillars of Interoperability](concepts/pillars.md)
* [MAESTRO Zero-Trust Security](concepts/security.md)
* [Service Federation](concepts/federation.md)
</div>

<div class="premium-card" markdown="1">
### RayRabbit Enterprise: ARK + Hypervisor
Discover how RayRabbit scales to corporate multi-tenant grids with SOC2 compliance, sandboxing, and resource throttling.
* [Enterprise Feature Overview](enterprise.md)
* [ARK Shield Integration](concepts/protocols.md)
* [Hypervisor Agent and Sandboxing](enterprise.md)
</div>

---

## Premium Security and Trust

RayRabbit is built from the ground up on the **Zero-Trust** security architecture. Every single packet transmitted through the **MessageBus** is cryptographically signed using the **JWS standard** with **asymmetric encryption keys**. 

Unlike traditional platforms, RayRabbit does not rely on static API tokens or loose network perimeters. Each agent connected to the grid is a sovereign entity that holds its own cryptographic identity key pair securely inside the **local key store** (OSS) or in hardware HSM modules (Enterprise).
