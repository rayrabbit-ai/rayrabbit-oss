# Especificación de Agent-to-Agent (A2A)

El protocolo **A2A** estandariza las llamadas de tareas, la negociación y el formato de los payloads intercambiados entre agentes heterogéneos dentro de la red descentralizada de RayRabbit. Se implementa sobre un formato asíncrono **JSON-RPC 2.0**.

---

## Estructura de Mensajes JSON-RPC 2.0

RayRabbit encapsula todos los flujos lógicos en sobres que cumplen estrictamente con la especificación de JSON-RPC 2.0:

### 1. Sobre de Petición (Request)
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/create",
  "params": {
    "prompt": "Evaluar la capacidad de carga en la región metropolitana",
    "priority": "high",
    "correlation_id": "corr-uuid-992a"
  },
  "id": "req-8b3c"
}
```

### 2. Sobre de Respuesta Exitosa (Success)
```json
{
  "jsonrpc": "2.0",
  "result": {
    "output": "Flota evaluada. 14 vehículos en estado activo y disponibles.",
    "correlation_id": "corr-uuid-992a"
  },
  "id": "req-8b3c"
}
```

### 3. Sobre de Respuesta de Error (Failure)
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": "El nodo destino no dispone de la capacidad: tasks/create"
  },
  "id": "req-8b3c"
}
```

---

## Protocolo de Handshake Criptográfico

Cuando los agentes de IA se configuran en **Modo P2P** (omitiendo la centralización de mensajes en el Core Hub), inicializan un intercambio directo de identidades gestionado por el **KeyExchangeAgent** antes de procesar payloads:

```
[Agente A]                                                    [Agente B]
    │                                                             │
    │ 1. Handshake Request: Hello + Tarjeta de Agente A (Clave A) │
    ├────────────────────────────────────────────────────────────>│
    │                                                             │
    │ 2. Verificación (Compara la Tarjeta con su Almacén Local)    │
    │                                                             │
    │ 3. Handshake Response: Accept + Tarjeta de Agente B         │
    │<────────────────────────────────────────────────────────────┤
    │                                                             │
    │ 4. Conexión Establecida: Transfieren mensajes firmados JWS.
```

---

## Tarjetas de Agente y Almacén de Confianza

Una **Tarjeta de Agente** (Agent Card) es un manifiesto firmado digitalmente que expone el identificador del agente, su dirección URL de red y su clave pública de identidad.

En la versión RayRabbit OSS, este directorio de tarjetas se gestiona de forma estática en el archivo **`AGENTS.md`** situado en la raíz del proyecto. Actúa como la agenda telefónica segura de la red.

La resolución de confianza física funciona como sigue:
1. Al querer invocar al Agente B, el Agente A busca su bloque de tarjeta en `AGENTS.md`.
2. Extrae la clave pública de identidad y su puerto de red.
3. Almacena la clave pública en su trust store local (`keystore` / `almacén local de claves`).
4. Cualquier mensaje recibido a partir de ese instante que declare ser del Agente B se descarta a nivel de red con un error HTTP `401 Unauthorized` si la firma criptográfica JWS recibida no coincide exactamente con dicha clave, evitando suplantaciones de identidad.
