# RayRabbit Enterprise Suite (ARK + Hypervisor)

Welcome to **RayRabbit Enterprise**, the sovereign, military-grade operational suite designed to run multi-tenant, high-volume agentic grids. While RayRabbit OSS establishes the decentralized communication protocol (Level 3 Network), RayRabbit Enterprise provides the virtualized operating system kernel (Level 4 AIOS) required to secure and govern large-scale AI operations.

---

## The Enterprise Architecture Matrix

```
   ┌─────────────────────────────────────────────────────────────┐
   │                  ENTERPRISE HYPERVISOR (AIOS)               │
   ├──────────────────────────────┬──────────────────────────────┤
   │  Dynamic Swarm IaC Engine    │  Resource Scheduler (GPU)    │
   ├──────────────────────────────┼──────────────────────────────┤
   │  Isolated Runtime Sandbox    │  mTLS Gateway WAN Bridge     │
   └──────────────────────────────┴──────────────────────────────┘
                                  ▲
                                  │ (mTLS Tunneling)
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                  ENTERPRISE ARK SIDE-CAR                    │
   ├──────────────────────────────┬──────────────────────────────┤
   │  Zero-Touch mTLS Handshake   │  Runtime prompt sanitization │
   └──────────────────────────────┴──────────────────────────────┘
```

---

## Core Enterprise Offerings

### 1. RayRabbit ARK (Agentic Runtime Kit)
The **ARK** is a highly optimized corporate SDK that encapsulates all MAESTRO security requirements inside a single local adapter. Instead of spending months coding custom cryptography, routing, and telemetry bridges, developers can secure their nodes with minimal integration overhead.

For custom corporate SDK specs and implementation guides, please contact our solutions engineering team.

#### What ARK automates:
* **Zero-Touch mTLS**: Establishes secure local loops, negotiating identities with external gateways.
* **RAM-Only Key Management**: Integrates with HSM modules and cloud KMS, ensuring private identity keys are never stored on persistent disk.
* **L7 Prompt Filter**: Sanitizes incoming and outgoing instructions, detecting prompt injection attempts and data leaks dynamically.

---

### 2. The Hypervisor Agent (AIOS Kernel)
The **Hypervisor Agent** acts as a virtualized cognitive operating system. Upon receiving abstract requirements from business workflows, the Hypervisor:
* **Sovereign Provisioning (IaC)**: Writes docker-compose schemas and spins up stateless container swarms on the fly.
* **Resource Scheduling**: Monitors GPU tokens, context windows, and financial budgets. If an agent overconsumes resources, the Hypervisor throttles execution at the network bridge to prevent unexpected cost spikes.
* **Isolated Runtime Sandboxing & MicroVM Isolation**: Runs untrusted agent-generated Python or bash scripts inside isolated runtime sandboxes or secure MicroVM containers, protecting your corporate host OS from system compromises.

---

## Technical Advantage Matrix

| Technical Capability | RayRabbit OSS (AGPL-3.0) | RayRabbit Enterprise |
|----------------------|--------------------------|-------------------------|
| **Core Protocol** | A2A, MCP, and A2AUI native communication. | Native plus optimized low-latency enterprise transport. |
| **Trust Model** | Static handshakes based on the local key store. | Dynamic Zero-Trust keys managed via enterprise KMS. |
| **Execution Sandboxing** | Runs physical tools directly on the host OS. | Secure isolated sandboxing and execution perimeters. |
| **Audit Trails** | Structured local audit database files stored locally. | Real-time SIEM streaming with immutable logs. |
| **Provisioning** | Manual shell execution and static config files. | Fully automated intent-based container deployment. |
| **IaC Standards** | Basic manual setups. | Compatible with industry-standard HCL deployment pipelines. |

---

## The 4 Vectors of Enterprise Protection

=== "Vector 1: Prompt Validation"
    Prevents indirect prompt injections by intercepting JWS-signed payloads and analyzing inputs semantically before they reach model context.
=== "Vector 2: Sandboxing Execution"
    Untrusted Python code compiled on-the-fly by autonomous agents is executed strictly inside isolated runtime sandboxes.
=== "Vector 3: HSM Key Security"
    Private keys reside exclusively in volatile memory, backed by HSM modules and rotatable enterprise KMS rings, never written to disk.
=== "Vector 4: SIEM Logs"
    Structured local audit database transaction tables are streamed live and encrypted directly to centralized corporate SIEM databases with strict WORM locks.

---

RayRabbit Enterprise is fully compatible with industry-standard HCL pipelines.

Deploying the central Hypervisor cluster to your private corporate VPC is fully automated. This deploys the secure Gateway Agents, mounts the KMS clusters, spins up the centralized telemetry aggregators, and registers the network routes in your cloud VPC in under three minutes.

---

## Contact and Next Steps

<div class="enterprise-cta-grid">
 <a href="demo/" class="cta-button primary"> Request Technical Demo</a>
 <a href="contact/" class="cta-button secondary"> Contact / Architecture</a>
 <a href="pricing/" class="cta-button outline"> View Plans & Pricing</a>
 <a href="https://wa.me/5491124055854?text=Hello%2C%20I%20would%20like%20to%20inquire%20about%20RayRabbit%20Enterprise." target="_blank" rel="noopener noreferrer" class="cta-button whatsapp"> WhatsApp Direct</a>
</div>

> ℹ **Dual Licensing**: The OSS core is distributed under the AGPL v3 license. To integrate RayRabbit into proprietary code bases without the obligation to open-source your code, acquire a commercial Enterprise License. Read [legal FAQ](enterprise/faq.md).
