# Suite RayRabbit Enterprise (ARK + Hypervisor)

Bienvenido a **RayRabbit Enterprise**, la suite corporativa de grado militar diseñada para operar clústeres multi-inquilino de alto tráfico e importancia crítica. Mientras RayRabbit OSS asienta los cimientos del protocolo de mensajería descentralizado (Nivel 3 de Red), RayRabbit Enterprise proporciona el sistema operativo virtualizado completo (Nivel 4 de Kernel AIOS) necesario para la orquestación, gobernanza y compliance regulatoria de enjambres masivos de IAs.

---

## Matriz de Arquitectura Enterprise

```
   ┌─────────────────────────────────────────────────────────────┐
   │                  ENTERPRISE HYPERVISOR (AIOS)               │
   ├──────────────────────────────┬──────────────────────────────┤
   │  Motor IaC Swarms Dinámico   │  Scheduler de GPU y Tokens   │
   ├──────────────────────────────┼──────────────────────────────┤
   │  Runtimes Sandboxing Aislado │  Pasarela WAN mTLS Bridge    │
   └──────────────────────────────┴──────────────────────────────┘
                                  ▲
                                  │ (Túneles mTLS Seguros WAN)
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                  ENTERPRISE ARK SIDE-CAR                    │
   ├──────────────────────────────┬──────────────────────────────┤
   │  Handshake mTLS Automático   │  Sanitización L7 de Prompt   │
   └──────────────────────────────┴──────────────────────────────┘
```

---

## Características Core de la Versión Enterprise

### 1. RayRabbit ARK (Agentic Runtime Kit)
El **ARK** es un SDK optimizado y de código cerrado diseñado para encapsular la complejidad de la suite de seguridad MAESTRO dentro de su software agéntico de producción. En lugar de forzar a sus desarrolladores a programar flujos de firma manual, descifrado y control de red, el perímetro del micro-servicio se integra de forma limpia y transparente.

Para conocer las especificaciones del SDK corporativo y las guías de integración de la versión comercial, contacte a nuestro equipo de ingeniería de soluciones.

#### Funcionalidades Clave de ARK:
* **Conectividad mTLS Automática**: Negocia certificados asimétricos con el clúster a través del canal en caliente sin intervención humana.
* **Llaves Seguras en RAM**: Integración nativa con módulos criptográficos HSM y sistemas KMS empresariales, asegurando que las llaves privadas nunca toquen el almacenamiento físico de la máquina.
* **Filtros de Seguridad Capa 7**: Sanitiza de forma proactiva prompts e instrucciones entrantes, mitigando inyecciones de prompt y fugas de propiedad intelectual en tiempo real.

---

### 2. El Agente Hypervisor (Kernel AIOS)
El **Hypervisor Agent** actúa como el núcleo de un sistema operativo diseñado exclusivamente para inteligencias artificiales agénticas. Al capturar intenciones expresadas por las áreas de negocio, el Hypervisor ejecuta de forma autónoma:
* **Aprovisionamiento IaC en Caliente**: Traduce intenciones lógicas en diagramas docker-compose y levanta instantáneamente contenedores efímeros.
* **Planificación Dinámica de Recursos (Scheduling)**: Monitorea el consumo de tokens y el uso financiero de APIs de LLM. Si detecta un desborde o bucle infinito de prompts en un agente, suspende su conexión de red preventivamente.
* **Aislamiento en Runtimes Seguros y MicroVMs**: Procesa la ejecución de scripts generados autónomamente por los agentes de IA dentro de runtimes de ejecución aislados (sandboxes) o contenedores MicroVM seguros, garantizando que un jailbreak no comprometa los datos ni el sistema operativo host.

---

## Diferenciación Técnica Real

| Característica Técnica | RayRabbit OSS (AGPL-3.0) | RayRabbit Enterprise |
|------------------------|--------------------------|-------------------------|
| **Capa de Protocolo** | Soporte nativo para A2A, MCP y A2AUI. | Soporte nativo más transporte optimizado de ultra-baja latencia. |
| **Modelo de Confianza**| Handshake estático dependiente del almacén local de claves. | Handshake Zero-Trust administrado por KMS corporativo. |
| **Aislamiento Físico** | Ejecución de herramientas directamente en el host. | Ejecución aislada en runtimes seguros y cajas de arena. |
| **Auditoría Forense**  | Base de datos de auditoría local estructurada e inmutable. | Exportación cifrada en tiempo real a motores SIEM con bloqueos WORM. |
| **Aprovisionamiento**  | Levantamiento manual de terminales y YAMLs planos. | Orquestación IaC automatizada basada en intenciones. |
| **Lanzamientos IaC**   | Configuración local básica. | Compatible con tuberías de despliegue HCL estándares. |

---

## Los Cuatro Vectores de Protección Enterprise

=== "Vector 1: Validación Semántica"
    Analiza semánticamente las intenciones de las IAs antes de inyectar datos a sus contextos, bloqueando ataques de inyección indirecta AIDA.
=== "Vector 2: Sandboxing Activo"
    Ejecuta scripts generados dinámicamente por las IAs de forma controlada y estricta en runtimes de ejecución aislados de su intranet.
=== "Vector 3: Gestión de Identidades HSM"
    Custodia llaves asimétricas de los agentes dentro de módulos HSM o KMS empresarial, reusando y rotando llaves en la memoria RAM volátil.
=== "Vector 4: Centralización SIEM"
    Canaliza de forma cifrada el flujo de transacciones del motor de auditoría directo a plataformas SIEM corporativas con bloqueos inmutables WORM.

---

## Despliegue de Infraestructura como Código (IaC)

RayRabbit Enterprise posee soporte completo para tuberías de despliegue basadas en estándares HCL de la industria.

Desplegar las pasarelas, bóvedas criptográficas y el Hypervisor en la VPC privada de su compañía se realiza de forma totalmente automatizada. Esto consolida las políticas SOC2 y NIST, inyecta la red perimetral cifrada y levanta los enjambres listos para operar de forma soberana en su compañía en menos de tres minutos.

## Contacto y Próximos Pasos

<div class="enterprise-cta-grid">
 <a href="demo/" class="cta-button primary"> Solicitar Demo Técnica</a>
 <a href="contact/" class="cta-button secondary"> Contacto / Arquitectura</a>
 <a href="pricing/" class="cta-button outline"> Ver Planes y Precios</a>
 <a href="https://wa.me/5491124055854?text=Hola%2C%20quisiera%20consultar%20sobre%20RayRabbit%20Enterprise." target="_blank" rel="noopener noreferrer" class="cta-button whatsapp"> WhatsApp Directo</a>
</div>

> ℹ **Licenciamiento Dual**: El núcleo OSS se distribuye bajo AGPL v3. Para integrar RayRabbit en código propietario sin obligación de liberar tu código fuente, adquiere la Licencia Comercial Enterprise. Leer [FAQ legal](enterprise/faq.md).
