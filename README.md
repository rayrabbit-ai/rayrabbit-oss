# RayRabbit AI Interoperability Infrastructure

Infraestructura agéntico avanzado para la interoperabilidad de IA que implementa nativamente los protocolos A2A (Agent2Agent) de Google y MCP (Model Context Protocol) de Anthropic.

## Introducción

RayRabbit es Infrastructure AI Interoperability  agéntico propietario diseñado para abordar los desafíos inherentes a la comunicación y orquestación de sistemas de inteligencia artificial distribuidos. En la era actual de la IA, donde la complejidad de las aplicaciones crece exponencialmente, la necesidad de que los agentes de IA interactúen de manera fluida, segura y estandarizada se ha vuelto primordial. RayRabbit se posiciona como la solución fundamental para construir ecosistemas de agentes robustos y escalables, permitiendo una verdadera interoperabilidad entre diversas entidades de IA. Este documento sirve como el manifiesto de RayRabbit, delineando su propósito, principios fundamentales, arquitectura de alto nivel y la visión que impulsa su desarrollo. Nuestro objetivo es empoderar a desarrolladores, investigadores y empresas para crear sistemas multi-agente que trasciendan las limitaciones de los enfoques monolíticos y aislados.


## ¿Qué Problema Resuelve RayRabbit?

El panorama actual de la inteligencia artificial se caracteriza por una proliferación de modelos, herramientas y plataformas, cada una con sus propias interfaces y paradigmas de comunicación. Esta heterogeneidad, si bien fomenta la innovación, también crea silos de información y funcionalidad, dificultando la colaboración efectiva entre diferentes agentes de IA. Los problemas clave que RayRabbit busca resolver incluyen:

1. **Falta de Interoperabilidad Estándar:** Los agentes desarrollados con diferentes frameworks o tecnologías a menudo luchan por comunicarse de manera significativa, lo que lleva a soluciones ad-hoc y frágiles para la integración.  
     
2. **Complejidad en la Orquestación:** Coordinar las acciones de múltiples agentes para lograr un objetivo común es una tarea intrínsecamente compleja, que requiere mecanismos sofisticados para el descubrimiento, la asignación de tareas y la gestión del estado.  
     
3. **Desafíos de Seguridad y Confianza:** En un entorno multi-agente, asegurar la comunicación, autenticar a los participantes y mantener la integridad de los datos son preocupaciones críticas que a menudo se pasan por alto o se implementan de manera inconsistente.  
     
4. **Dificultad en el Despliegue y Escalabilidad:** Desplegar y escalar sistemas agénticos en entornos de producción presenta obstáculos significativos relacionados con la gestión de recursos, la tolerancia a fallos y el rendimiento.  
     
5. **Curva de Aprendizaje Elevada:** La construcción de sistemas multi-agente desde cero puede ser abrumadora para los desarrolladores debido a la necesidad de comprender múltiples protocolos, patrones de diseño y consideraciones de infraestructura. RayRabbit aborda estos problemas proporcionando un marco unificado y estandarizado que abstrae la complejidad subyacente de la comunicación y la orquestación, permitiendo a los desarrolladores centrarse en la lógica de negocio de sus agentes.
   

## 🚀 Características Principales

### Protocolos Nativos

- **A2A (Agent2Agent)**: Comunicación directa entre agentes usando JSON-RPC 2.0 sobre HTTP/HTTPS

- **MCP (Model Context Protocol)**: Integración con modelos de lenguaje y herramientas externas

- **MessageBus**: Sistema de mensajería centralizado y escalable

### Agentes Especializados

- **SimpleAgent**: Agente básico con respuestas automáticas y comandos personalizables

- **Arquitectura extensible**: Fácil creación de agentes especializados

### Integraciones Nativas

- **LangChain Bridge**: Integración completa con cadenas, agentes y herramientas de LangChain

- **CrewAI Bridge**: Soporte para crews y agentes colaborativos de CrewAI

- **AutoGen Bridge**: Comunicación con agentes conversacionales de Microsoft AutoGen

### Seguridad y Monitoreo

- **Marco MAESTRO**: Sistema de seguridad integrado

- **Logging avanzado**: Sistema de logging estructurado y configurable

- **Métricas en tiempo real**: Monitoreo de rendimiento y estado del sistema

## 📦 Instalación [disponible proximamente]

### Dependencias Básicas

```bash
pip install aiohttp websockets pydantic
```

### Dependencias Opcionales (para integraciones)

```bash
# Para LangChain
pip install langchain

# Para CrewAI  
pip install crewai

# Para AutoGen
pip install pyautogen
```

## 🏗️ Arquitectura

```
rayrabbit/
├── core/                    # Componentes fundamentales
│   ├── agent.py            # Clase base Agent
│   └── message_bus.py      # MessageBus centralizado
├── agents/                  # Agentes especializados
│   └── simple_agent.py     # SimpleAgent básico
├── communication/           # Sistema de comunicación
│   ├── message.py          # Estructura de mensajes
│   └── transport.py        # Capa de transporte
├── protocols/               # Protocolos A2A y MCP
│   ├── a2a.py             # Protocolo A2A completo
│   └── mcp.py             # Protocolo MCP completo
├── integrations/            # Bridges externos
│   ├── langchain.py        # Integración LangChain
│   ├── crewai.py          # Integración CrewAI
│   └── autogen.py         # Integración AutoGen
├── security/                # Marco de seguridad MAESTRO
│   ├── authentication.py   # Autenticación
│   ├── authorization.py    # Autorización
│   ├── encryption.py       # Cifrado
│   └── maestro.py         # Coordinador de seguridad
└── utils/                   # Utilidades
    └── logger.py           # Sistema de logging
```

## 🚀 Inicio Rápido

### Ejemplo Básico

```python
import asyncio
from rayrabbit import MessageBus, SimpleAgent, A2AProtocol, MCPProtocol

async def main():
    # 1. Inicializar MessageBus
    message_bus = MessageBus("main_bus")
    await message_bus.start()
    
    # 2. Crear agentes
    agent1 = SimpleAgent("agent_001", "Asistente", "Agente asistente general")
    agent1.add_auto_response("hola", "¡Hola! Soy {name}")
    
    # 3. Registrar agentes
    await message_bus.register_agent(agent1.id, agent1, agent1.capabilities)
    
    # 4. Inicializar protocolos
    a2a_protocol = A2AProtocol(
        message_bus=message_bus,
        agent_id="coordinator",
        agent_name="Coordinator",
        agent_description="Coordinador A2A",
        capabilities=["communication"],
        endpoint="http://localhost:8080"
    )
    await a2a_protocol.start()
    
    # 5. Usar el framework
    from rayrabbit.communication.message import Message, MessageType
    
    test_message = Message(
        sender_id="system",
        recipient_id=agent1.id,
        content={"text": "hola"},
        message_type=MessageType.REQUEST
    )
    
    response = await message_bus.send_direct(test_message)
    print(f"Respuesta: {response}")
    
    # Limpieza
    await message_bus.stop()
    await a2a_protocol.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Ejecutar Ejemplo Completo

```bash
python example_basic_rayrabbit.py
```

## 🔧 Configuración Avanzada

### Configurar Logging

```python
from rayrabbit.utils.logger import configure_logging

# Configurar nivel de logging
configure_logging("DEBUG")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Crear Agente Personalizado

```python
from rayrabbit.core.agent import Agent

class CustomAgent(Agent):
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name, "Agente personalizado")
        self.add_capability("custom_processing")
    
    async def _handle_request(self, message):
        # Lógica personalizada
        return self._create_response(message, {"result": "processed"})
```

### Integración con LangChain

```python
from rayrabbit.integrations import LangChainBridge
from langchain.chains import LLMChain

# Inicializar bridge
langchain_bridge = LangChainBridge("lc_bridge")
await langchain_bridge.connect()

# Registrar cadena LangChain
chain = LLMChain(...)  # Tu cadena LangChain
langchain_bridge.register_chain("my_chain", chain)

# Usar cadena
result = await langchain_bridge.invoke_chain("my_chain", {"input": "test"})
```

## 🔒 Seguridad

RayRabbit incluye el marco de seguridad MAESTRO que proporciona:

- **Autenticación**: Verificación de identidad de agentes

- **Autorización**: Control de acceso basado en roles

- **Cifrado**: Protección de comunicaciones

- **Auditoría**: Registro de actividades de seguridad

- **Detección de amenazas**: Monitoreo proactivo

```python
from rayrabbit.security.maestro import MAESTROSecurity

# Inicializar seguridad
security = MAESTROSecurity()
await security.initialize()

# Configurar en MessageBus
message_bus.set_security_manager(security)
```

## 📊 Monitoreo y Métricas

### Métricas del Sistema

```python
# Métricas del MessageBus
print(f"Estado: {message_bus.status.value}")
print(f"Agentes registrados: {len(message_bus.agents)}")

# Métricas de agentes
print(f"Estado del agente: {agent.status.value}")
print(f"Capacidades: {len(agent.capabilities)}")

# Métricas de bridges
if langchain_bridge:
    metrics = langchain_bridge.get_metrics()
    print(f"Componentes registrados: {metrics['components_registered']}")
```

## 🧪 Testing

La Infrastructure incluye un ejemplo completo que demuestra:

1. ✅ Inicialización del Infrastructure

1. ✅ Creación y registro de agentes

1. ✅ Comunicación entre agentes

1. ✅ Protocolos A2A y MCP funcionando

1. ✅ Integración con frameworks externos

1. ✅ Métricas y monitoreo

## 🤝 Contribución

RayRabbit es un Infrastructure de código abierto. Las contribuciones son bienvenidas:

1. Fork el repositorio

1. Crea una rama para tu feature

1. Implementa tus cambios

1. Añade tests

1. Envía un pull request

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.

## 🆘 Soporte

- **Documentación**: Ver archivos en `/docs`

- **Ejemplos**: Ver `example_basic_rayrabbit.py`

- **Issues**: Reportar en GitHub Issues

## 🔄 Roadmap

- [ ] Soporte para más protocolos de comunicación

- [ ] Dashboard web para monitoreo

- [ ] Integración con más frameworks de IA

- [ ] Optimizaciones de rendimiento

- [ ] Documentación extendida

---

**RayRabbit Infrastructure AI** - Construyendo el futuro de los sistemas agénticos interoperables.

El nombre comercial **"[RayRabbit]"** se encuentra reservado por su autor [Santiago Dichiera](https://www.linkedin.com/in/santiago-dichiera-a7201938/)



**

