# RayRabbit L3 Interoperability Playbook: 10 Natural Language Prompt Combinations

This playbook contains 10 **natural language prompts** ready to type directly into the **RayRabbit Chat UI** and **A2UI Visual Portal (:8006)**.
Because RayRabbit integrates an OS-level **BM25 Dynamic Tool Search Engine** (
ayrabbit/utils/tool_search_engine.py), users **do not need to write technical function calls, JSON parameters, or tool names**. The BM25 algorithm dynamically tokenizes user intentions, scores them against the indexed schemas and parameters of active tools, and executes cross-framework actions automatically.

All prompts map to **real database entities** in sap_tm_orders.db, real products (Motormech 4cv), real transporters (Carlos Rodríguez), and real active agent nodes.

---

## 1. Quick Reference: Natural Intent to BM25 Action

| # | Natural Human Intent | BM25 Keywords Matched | Participating Nodes & Tools |
|---|---|---|---|
| **01** | Diagnose delayed order in Madrid | order, delayed, madrid, 
oute | LangChain (nalyze_order) -> CrewAI (optimize_route) |
| **02** | Check truck availability & assign driver | sap, 	ruck, ehicle, driver, ssign | AutoGen (start_autogen_chat, schedule_assignment) |
| **03** | Real-time GPS tracking on dashboard | 	rack, location, highway, 	elemetry | Core (	rack_package) -> A2UI Portal (:8006) |
| **04** | Retrieve technical specs and pricing | product, motormech, specs, sku, price | Logistics Tools (get_product_info) |
| **05** | Save session operational preference | 
emember, session, preferred, driver | Sovereign SDK (save_memory_fact on /ws) |
| **06** | Query cross-session memory facts | saved, preferences, operational, acts | Sovereign SDK (
ead_session_memory, 
ayrabbit://memory) |
| **07** | Inspect source code with redacted secrets | 
ead, ile, crewai, 
edact, secrets | System Tools SDK (
ead_file with regex masking) |
| **08** | Verify external warehouse stock in ERP | inventory, stock, external, motormech | DeclarativeBridge (:8010/openapi.json) |
| **09** | Verify JWS signatures and audit logs | security, udit, signatures, jws, 	amper | MAESTRO Zero-Trust (udit.db verification) |
| **10** | End-to-end urgent mission dispatch | urgent, order, 
oute, ssign, screen | Full Grid (LangChain + CrewAI + AutoGen + A2UI) |

---

## 2. The 10 Natural Language Prompts (English)

### Prompt 01: Delayed Order Diagnosis & Route Recovery
> **Scenario:** Customer CUST-99 needs urgent delivery of delayed laptops and monitors.  
> **What to type in the Chat UI:**
> `	ext
> Customer CUST-99 is asking about order ORD-2025-001. Could you check why it is delayed at the Madrid sort center and calculate an urgent alternative route to deliver it today?
> `
> *BM25 Resolution:* Identifies keywords order, delayed, 
oute -> Triggers nalyze_order (LangChain) and delegates to optimize_route (CrewAI).

---

### Prompt 02: Transporter & Fleet Vehicle Assignment
> **Scenario:** Dispatching truck V-502 to Carlos Rodríguez in SAP TM.  
> **What to type in the Chat UI:**
> `	ext
> We need to coordinate dispatch for order ORD-2025-001. Check if vehicle V-502 is available in SAP TM and assign driver Carlos Rodriguez to the shipment.
> `
> *BM25 Resolution:* Matches sap, ehicle, driver -> Invokes start_autogen_chat and schedule_assignment on AutoGen node.

---

### Prompt 03: Highway GPS Tracking on Visual Dashboard
> **Scenario:** Visualizing real-time package progress on the A2UI dashboard.  
> **What to type in the Chat UI:**
> `	ext
> Where is keyboard order ORD-2025-002 right now? Show me its current location on the highway and stream the live tracking card to my dashboard.
> `
> *BM25 Resolution:* Matches location, highway, 	rack -> Runs 	rack_package and streams a Server-Driven UI surface to A2UI (:8006).

---

### Prompt 04: Product Catalog & Price Lookup
> **Scenario:** Inquiring about Motormech 4cv motor specs.  
> **What to type in the Chat UI:**
> `	ext
> A client is asking for a quote on the Motormech 4cv engine. Look up its technical specifications, inventory SKU, and list price in SAP TM.
> `
> *BM25 Resolution:* Matches product, motormech, sku, price -> Calls get_product_info returning SKU MM-4CV-001 (,250.00).

---

### Prompt 05: Session Operational Memory Storing
> **Scenario:** Teaching the agent a logistics preference for the current session.  
> **What to type in the Chat UI:**
> `	ext
> Remember for all deliveries in this session that Carlos Rodriguez (T-100) is our preferred trusted driver for critical tech shipments.
> `
> *BM25 Resolution:* Matches 
emember, session, preferred, driver -> Invokes save_memory_fact on sovereign_memory_node.

---

### Prompt 06: Sovereign Memory Fact Retrieval
> **Scenario:** Checking operational facts stored across sessions.  
> **What to type in the Chat UI:**
> `	ext
> What driver preferences or operational facts do we currently have saved for this session?
> `
> *BM25 Resolution:* Matches saved, preferences, acts, session -> Executes 
ead_session_memory or resolves 
ayrabbit://memory.

---

### Prompt 07: Secure Code Inspection with Secret Masking
> **Scenario:** Inspecting backend service code without leaking API keys.  
> **What to type in the Chat UI:**
> `	ext
> Inspect the CrewAI service configuration file to check how it initializes, but make sure all sensitive API keys and tokens are redacted.
> `
> *BM25 Resolution:* Matches inspect, ile, crewai, 
edacted -> Calls 
ead_file on system_tools_node with regex redaction.

---

### Prompt 08: External ERP Inventory Stock Validation
> **Scenario:** Consulting the REST inventory bridge before committing stock.  
> **What to type in the Chat UI:**
> `	ext
> Before scheduling shipment for order REAL-E2E-123, check with our external inventory service on port 8010 if we have units in stock for Motormech 4cv.
> `
> *BM25 Resolution:* Matches inventory, stock, external, motormech -> Queries DeclarativeBridge at http://127.0.0.1:8010/openapi.json.

---

### Prompt 09: MAESTRO Zero-Trust Cryptographic Audit
> **Scenario:** Verifying that message bus transactions are cryptographically signed.  
> **What to type in the Chat UI:**
> `	ext
> Perform a security audit on recent order dispatches to verify that all JWS digital signatures in audit.db are valid and free from tampering.
> `
> *BM25 Resolution:* Matches security, udit, signatures, jws -> Queries udit.db via MAESTRO security provider.

---

### Prompt 10: End-to-End Urgent Mission Dispatch
> **Scenario:** Full autonomous grid orchestration across LangChain, CrewAI, AutoGen, and A2UI.  
> **What to type in the Chat UI:**
> `	ext
> We have an urgent delivery: dispatch the Motormech 4cv cargo for order REAL-E2E-123 from Madrid. Analyze the order, optimize the route with the shipping crew, assign Carlos Rodriguez in SAP, and stream the live tracking to my screen.
> `
> *BM25 Resolution:* Matches multimodal chain -> Dispatches across LangChain (nalyze_order), CrewAI (optimize_route), AutoGen (schedule_assignment), and streams live telemetry to A2UI (:8006).

---

<details>
<summary>🇪🇸 Documentación Completa en Español (Haz clic para desplegar)</summary>

# Playbook de Interoperabilidad RayRabbit L3: 10 Prompts en Lenguaje Natural

Este playbook contiene 10 **prompts en lenguaje natural humano** listos para escribir directamente en la **Interfaz de Chat de RayRabbit** o en el **Portal Visual A2UI (:8006)**.
Gracias a que RayRabbit incorpora un **Motor de Búsqueda Dinámica BM25 de Herramientas** (
ayrabbit/utils/tool_search_engine.py), **no necesitas escribir código, funciones técnicas ni parámetros JSON**. El algoritmo BM25 tokeniza tu intención en lenguaje natural, la compara contra los esquemas y descripciones de las herramientas activas, y ejecuta automáticamente las acciones correspondientes entre los diferentes frameworks.

Todos los prompts están basados en **datos reales** de sap_tm_orders.db, productos reales (Motormech 4cv), transportistas reales (Carlos Rodríguez) y nodos activos.

---

## 1. Matriz de Referencia: Intención Natural a Acción BM25

| # | Intención Humana Natural | Palabras Clave BM25 Detectadas | Nodos y Herramientas Participantes |
|---|---|---|---|
| **01** | Diagnosticar pedido demorado en Madrid | pedido, demorado, madrid, 
uta | LangChain (nalyze_order) -> CrewAI (optimize_route) |
| **02** | Verificar camión y asignar chofer en SAP | sap, camión, ehículo, chofer, signar | AutoGen (start_autogen_chat, schedule_assignment) |
| **03** | Rastreo GPS en vivo en el dashboard visual | 
astrear, ubicación, utopista, 	elemetría | Core (	rack_package) -> Portal A2UI (:8006) |
| **04** | Consultar ficha técnica y precio de producto | producto, motormech, sku, precio | Logistics Tools (get_product_info) |
| **05** | Guardar preferencia operativa en sesión | 
ecuerda, sesión, preferido, chofer | SDK Soberano (save_memory_fact vía /ws) |
| **06** | Consultar memoria soberana de la sesión | guardado, preferencias, hechos, sesión | SDK Soberano (
ead_session_memory, 
ayrabbit://memory) |
| **07** | Inspeccionar código fuente ocultando secretos | leer, rchivo, crewai, ocultar, secretos | System Tools SDK (
ead_file con filtro regex) |
| **08** | Validar existencias en almacén externo | inventario, stock, externo, motormech | DeclarativeBridge (:8010/openapi.json) |
| **09** | Verificar firmas JWS y registros de auditoría | seguridad, uditoría, irmas, jws | Seguridad MAESTRO (verificación de udit.db) |
| **10** | Misión urgente integral de extremo a extremo | urgente, pedido, 
uta, signar, pantalla | Malla Completa (LangChain + CrewAI + AutoGen + A2UI) |

---

## 2. Los 10 Prompts en Lenguaje Natural (Español)

### Prompt 01: Diagnóstico de Demora y Recuperación de Ruta
> **Escenario:** El cliente CUST-99 reclama por su pedido de monitores demorado.  
> **Qué escribir en el Chat UI:**
> `	ext
> El cliente CUST-99 está consultando por el pedido ORD-2025-001. ¿Podrías revisar por qué está demorado en el centro de distribución de Madrid y calcular una ruta alternativa urgente para entregarlo hoy?
> `
> *Resolución BM25:* Detecta pedido, demorado, 
uta -> Dispara nalyze_order en LangChain y delega en optimize_route de CrewAI.

---

### Prompt 02: Asignación de Chofer y Vehículo en SAP TM
> **Escenario:** Coordinar la flota y verificar la disponibilidad del camión V-502.  
> **Qué escribir en el Chat UI:**
> `	ext
> Necesitamos coordinar el despacho del pedido ORD-2025-001. Verifica si el camión V-502 está disponible en SAP TM y asigna al transportista Carlos Rodríguez para realizar el viaje.
> `
> *Resolución BM25:* Identifica sap, camión, 	ransportista, signar -> Invoca start_autogen_chat y schedule_assignment en AutoGen.

---

### Prompt 03: Rastreo GPS en Tiempo Real en Pantalla A2UI
> **Escenario:** Visualizar el paquete en tránsito en el portal de telemetría visual.  
> **Qué escribir en el Chat UI:**
> `	ext
> ¿Por dónde va el envío del teclado ORD-2025-002 en este momento? Muéstrame su ubicación actual en la autopista y proyecta la tarjeta de seguimiento en vivo en mi pantalla.
> `
> *Resolución BM25:* Identifica ubicación, utopista, seguimiento, pantalla -> Ejecuta 	rack_package y emite la tarjeta dinámica al Portal A2UI (:8006).

---

### Prompt 04: Consulta de Ficha Técnica y Precio en Catálogo
> **Escenario:** Cotización inmediata de un motor Motormech 4cv.  
> **Qué escribir en el Chat UI:**
> `	ext
> Un cliente nos pide cotización del motor Motormech 4cv. Búscame sus especificaciones técnicas, el código SKU de inventario y su precio oficial en SAP TM.
> `
> *Resolución BM25:* Identifica motormech, especificaciones, sku, precio -> Llama a get_product_info devolviendo SKU MM-4CV-001 (.250,00).

---

### Prompt 05: Memorizar Preferencia Operativa en la Sesión
> **Escenario:** Enseñar al agente una preferencia de negocio persistente.  
> **Qué escribir en el Chat UI:**
> `	ext
> Recuerda para todas las entregas de esta sesión que Carlos Rodríguez (T-100) es nuestro chofer preferido de confianza para envíos de tecnología delicada.
> `
> *Resolución BM25:* Identifica 
ecuerda, sesión, preferido, chofer -> Invoca save_memory_fact en sovereign_memory_node.

---

### Prompt 06: Recuperación de Hechos desde la Memoria Soberana
> **Escenario:** Consultar qué decisiones o preferencias quedaron registradas.  
> **Qué escribir en el Chat UI:**
> `	ext
> ¿Qué preferencias de transporte o hechos operativos tenemos guardados actualmente para esta sesión?
> `
> *Resolución BM25:* Identifica preferencias, hechos, guardados, sesión -> Consulta 
ead_session_memory o resuelve la URI 
ayrabbit://memory.

---

### Prompt 07: Inspección Segura de Código con Censura de Secretos
> **Escenario:** Revisar código del repositorio sin exponer claves de API.  
> **Qué escribir en el Chat UI:**
> `	ext
> Revisa el archivo de configuración del servicio de CrewAI para comprobar cómo inicializa, pero asegúrate de ocultar cualquier clave de API sensible o token privado.
> `
> *Resolución BM25:* Identifica 
evisa, rchivo, crewai, ocultar, secretos -> Ejecuta 
ead_file en system_tools_node con censura regex automática.

---

### Prompt 08: Verificación de Stock en Servicio Externo de Inventario
> **Escenario:** Comprobar existencias en almacén antes de confirmar despacho.  
> **Qué escribir en el Chat UI:**
> `	ext
> Antes de programar el envío del pedido REAL-E2E-123, consulta con el servicio externo de inventario en el puerto 8010 si tenemos unidades disponibles del producto Motormech 4cv.
> `
> *Resolución BM25:* Identifica inventario, unidades, disponibles, motormech -> Consulta DeclarativeBridge en http://127.0.0.1:8010/openapi.json.

---

### Prompt 09: Auditoría Criptográfica Zero-Trust MAESTRO
> **Escenario:** Validar que los mensajes cursados por el bus no han sido alterados.  
> **Qué escribir en el Chat UI:**
> `	ext
> Realiza una auditoría de seguridad sobre los últimos pedidos despachados para certificar que todas las firmas digitales JWS en audit.db son válidas y no sufrieron alteraciones.
> `
> *Resolución BM25:* Identifica seguridad, uditoría, irmas, jws -> Inspecciona los registros firmados con RSA-4096 en udit.db.

---

### Prompt 10: Despacho Autónomo Integral de Extremo a Extremo
> **Escenario:** Operación completa y autónoma en toda la malla.  
> **Qué escribir en el Chat UI:**
> `	ext
> Tenemos una entrega urgente: despacha el motor Motormech 4cv del pedido REAL-E2E-123 desde Madrid. Analiza el pedido, optimiza la ruta con el equipo de rutas, asigna a Carlos Rodríguez en SAP y proyecta el progreso en vivo en mi pantalla.
> `
> *Resolución BM25:* Resuelve la cadena completa: LangChain (nalyze_order) -> CrewAI (optimize_route) -> AutoGen (schedule_assignment) -> Streaming de telemetría en Portal A2UI (:8006).

</details>
