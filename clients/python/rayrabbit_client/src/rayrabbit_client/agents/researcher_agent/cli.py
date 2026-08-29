import argparse
import asyncio
import json
from rayrabbit_client.agents.researcher_agent.researcher_agent import ResearcherAgent

async def run_cli():
    parser = argparse.ArgumentParser(description="RayRabbit Researcher Agent CLI")
    parser.add_argument("--query", type=str, help="Research query to execute")
    parser.add_argument("--hub", type=str, default="ws://localhost:8005/ws", help="Hub WebSocket URL")
    args = parser.parse_args()

    # Inicializar el agente SDK
    agent = ResearcherAgent(agent_id="cli_researcher", hub_url=args.hub)
    
    print(f"🚀 Iniciando ResearcherAgent CLI y conectando a {args.hub}...")
    # Lanzar la conexión en background
    connect_task = asyncio.create_task(agent.connect())
    
    if args.query:
        print(f"\n🔍 Ejecutando investigación: '{args.query}'...\n")
        # Invocar la herramienta directamente para la CLI
        try:
            result = await agent._command_web_search(query=args.query, max_results=3)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Error durante la investigación: {e}")
            
        print("\n✅ Investigación completada.")
    else:
        print("Esperando solicitudes externas vía Hub (presiona Ctrl+C para salir)...")
        await connect_task

if __name__ == "__main__":
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\nCLI Detenido.")
