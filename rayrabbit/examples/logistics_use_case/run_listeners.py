"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
"""
run_listeners.py - Ejecutor de los Agentes Listener de Logística.
🐇 Estos agentes actúan como el sistema nervioso del flujo AAIF (Modo Bridges).
"""

import asyncio
import logging
from rayrabbit.examples.logistics_use_case.listener_agents import (
    LangChainResponseListenerAgent,
    CrewAIWorkflowListenerAgent,
    CrewAIFinalDecisionListenerAgent,
    AutoGenUpdateListenerAgent,
    FinalCustomerResponseListenerAgent
)

# Configuración del Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("listeners_runner")

async def main():
    logger.info("NS: Iniciando Sistema Nervioso (Listeners)...")
    
    from rayrabbit.core.message_bus import MessageBus
    from rayrabbit.utils.config import MessageBusConfig

    # 1. Inicializar MessageBus Local (Conectado al Hub por defecto en config)
    bus = MessageBus(config=MessageBusConfig())
    await bus.start()

    # 2. Instanciar y Registrar Agentes
    listeners = [
        LangChainResponseListenerAgent(),
        CrewAIWorkflowListenerAgent(),
        CrewAIFinalDecisionListenerAgent(),
        AutoGenUpdateListenerAgent(),
        FinalCustomerResponseListenerAgent()
    ]
    
    for agent in listeners:
        await bus.register_agent(agent)
        bus.subscribe("*", agent.id)
        logger.info(f"✅ Agente {agent.id} registrado.")

    logger.info("[SUCCESS] Sistema Nervioso operativo.")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Cerrando Listeners...")
        await bus.stop()

if __name__ == "__main__":
    asyncio.run(main())
