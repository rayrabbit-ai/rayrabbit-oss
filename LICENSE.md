# RayRabbit Licensing and Distribution Model / Modelo de Licenciamiento y Distribución de RayRabbit

## [EN] English Version

RayRabbit operates under a **Dual Licensing and Open-Core Model** designed to ensure the software remains free, transparent, and open-source for community development, while providing commercial guarantees and advanced infrastructure compliance for enterprise environments.

### 1. Open Source Core: AGPLv3

The core of the RayRabbit infrastructure (`rayrabbit-oss`) is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-only)**. 

#### Why AGPLv3?
* **Copyleft Protection:** If you modify RayRabbit or build a service on top of it, and expose it to users over a network, you **must make the source code of your modifications available** to those users under the same AGPLv3 license.
* **Anti-SaaS Loophole:** This prevents cloud service providers and third parties from offering RayRabbit as a closed-source managed service (SaaS) without contributing back to the open-source community.
* **OSI Compliant:** AGPLv3 is a fully approved Open Source Initiative (OSI) license, guaranteeing the freedom to read, run, modify, and distribute the core codebase.

The full terms of the AGPLv3 license can be found in [LICENSE](LICENSE) (or [LICENSE-AGPLv3.txt](LICENSE-AGPLv3.txt)).

---

### 2. Client SDKs: Apache 2.0

To ensure maximum interoperability and ease of integration, any official client SDKs (e.g., lightweight libraries used by external agents or applications to speak to the RayRabbit cluster) are licensed under the permissive **Apache License 2.0**. This allows developers to integrate client-side logic into proprietary products without triggering copyleft requirements.

The full terms of the Apache 2.0 license can be found in [clients/LICENSE](clients/LICENSE) (or [LICENSE-Apache-2.0.txt](LICENSE-Apache-2.0.txt)).

---

### 3. Commercial Licensing: RayRabbit Enterprise

For organizations that cannot comply with the AGPLv3 terms, or require enterprise-grade infrastructure security, we offer the **RayRabbit Enterprise ARK (Agentic Runtime Kit)** subscription.

#### Enterprise Features (Not in OSS):
* **Hypervisor Sandboxing:** Dynamic runtime execution of untrusted AI-generated code in WebAssembly (WASM) and MicroVMs (AWS Firecracker).
* **HSM & KMS Integration:** Storing identity keys in secure hardware modules (AWS KMS, HashiCorp Vault) rather than the local filesystem.
* **Active Cognitive Defense:** Automated counter-attacks, honeytoken injection, and isolation of cognitively compromised agents.
* **SIEM Auditing:** Real-time tamper-proof (WORM) audit forwarding to Splunk, Elastic, or Datadog.

#### Commercial License Guarantees:
* Waiver of all AGPLv3 copyleft obligations.
* Professional support SLAs and deployment warranty.
* Access to the private registry for `rayrabbit-enterprise-ark` packages.

To purchase a commercial license or request a trial, contact us at: [https://rayrabbit-ai.github.io/contact](https://rayrabbit-ai.github.io/contact) or visit [https://rayrabbit-ai.github.io/](https://rayrabbit-ai.github.io/).

---

## [ES] Versión en Español

RayRabbit opera bajo un **Modelo de Licenciamiento Dual y Open-Core** diseñado para garantizar que el software permanezca libre, transparente y de código abierto para el desarrollo de la comunidad, mientras proporciona garantías comerciales y cumplimiento de infraestructura avanzada para entornos empresariales.

### 1. Núcleo de Código Abierto: AGPLv3

El núcleo de la infraestructura de RayRabbit (`rayrabbit-oss`) está licenciado bajo la **GNU Affero General Public License v3.0 (AGPL-3.0-only)**.

#### ¿Por qué AGPLv3?
* **Protección de Copyleft:** Si modifica RayRabbit o construye un servicio sobre él, y lo expone a los usuarios a través de una red, **debe poner el código fuente de sus modificaciones a disposición** de esos usuarios bajo la misma licencia AGPLv3.
* **Evita el Vacío de SaaS:** Esto evita que los proveedores de servicios en la nube y terceros ofrezcan RayRabbit como un servicio administrado de código cerrado (SaaS) sin contribuir de vuelta a la comunidad de código abierto.
* **Cumple con la OSI:** AGPLv3 es una licencia completamente aprobada por la Open Source Initiative (OSI), lo que garantiza la libertad de leer, ejecutar, modificar y distribuir la base de código del núcleo.

Los términos completos de la licencia AGPLv3 se pueden encontrar en [LICENSE](LICENSE) (o [LICENSE-AGPLv3.txt](LICENSE-AGPLv3.txt)).

---

### 2. SDKs de Cliente: Apache 2.0

Para garantizar la máxima interoperabilidad y facilidad de integración, los SDK de cliente oficiales (por ejemplo, bibliotecas ligeras utilizadas por agentes o aplicaciones externas para comunicarse con el clúster de RayRabbit) están licenciados bajo la permisiva **Licencia Apache 2.0**. Esto permite a los desarrolladores integrar la lógica del lado del cliente en productos propietarios sin activar los requisitos de copyleft.

Los términos completos de la licencia Apache 2.0 se pueden encontrar en [clients/LICENSE](clients/LICENSE) (o [LICENSE-Apache-2.0.txt](LICENSE-Apache-2.0.txt)).

---

### 3. Licenciamiento Comercial: RayRabbit Enterprise

Para las organizaciones que no pueden cumplir con los términos de la AGPLv3, o requieren seguridad de infraestructura de nivel empresarial, ofrecemos la suscripción **RayRabbit Enterprise ARK (Agentic Runtime Kit)**.

#### Características Enterprise (No incluidas en OSS):
* **Sandboxing con Hipervisor:** Ejecución dinámica en tiempo de ejecución de código no confiable generado por IA dentro de WebAssembly (WASM) y MicroVMs (AWS Firecracker).
* **Integración con HSM y KMS:** Almacenamiento de claves de identidad en módulos de hardware seguros (AWS KMS, HashiCorp Vault) en lugar del sistema de archivos local.
* **Defensa Cognitiva Activa:** Contraataques automatizados, inyección de honeytokens y aislamiento de agentes comprometidos cognitivamente.
* **Auditoría SIEM:** Envío de auditorías en tiempo real a prueba de alteraciones (WORM) a Splunk, Elastic o Datadog.

#### Garantías de la Licencia Comercial:
* Exención de todas las obligaciones de copyleft de AGPLv3.
* SLAs de soporte profesional y garantía de despliegue.
* Acceso al registro privado para los paquetes de `rayrabbit-enterprise-ark`.

Para adquirir una licencia comercial o solicitar una prueba, contáctenos en: [https://rayrabbit-ai.github.io/contact](https://rayrabbit-ai.github.io/contact) o visite [https://rayrabbit-ai.github.io/](https://rayrabbit-ai.github.io/).
