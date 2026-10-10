<!--
trigger: always_on
-->

# RayRabbit Sovereign Mesh - Directivas de Integración

Este espacio de trabajo está conectado a la infraestructura soberana de **RayRabbit (AI TCP/IP + TLS + HTTP)** a través del plugin oficial de Antigravity.

## Directivas para el Asistente

1. **Comunicación Inter-Agente y Consensos:**
   * Cuando necesites coordinar tareas, pedir validación o enviar informes a otros agentes o sesiones de Antigravity (ej. `antigravity_core`, `antigravity_devops`), utiliza la herramienta `rayrabbit_send_message` indicando el `recipient_id` y un payload estructurado.
   * Utiliza `rayrabbit_read_inbox` para verificar si han llegado respuestas o consensos entrantes.

2. **Descubrimiento de la Red (Discovery):**
   * Antes de asumir el estado o ubicación de un nodo, invoca `rayrabbit_list_agents` para conocer los servicios y sesiones activas en la malla (local o remota).

3. **Invocación de Herramientas Distribuidas:**
   * Si el usuario solicita datos logísticos, planes de ruta, estado de flota o inventario WMS, puedes ejecutar herramientas distribuidas en los nodos soberanos (`crewai_service`, `langchain_service`, `autogen_service`) usando `rayrabbit_call_tool`.

4. **Persistencia en Memoria Soberana L3:**
   * Para hechos arquitectónicos o consensos aprobados por múltiples agentes, utiliza `rayrabbit_publish_fact` para persistirlos de forma inmutable en la Memoria L3 compartida.
