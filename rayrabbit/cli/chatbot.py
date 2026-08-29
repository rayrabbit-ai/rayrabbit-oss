# -*- coding: utf-8 -*-
"""
RayRabbit OSS - CLI TMS Chatbot with Slash Commands
Copyright © 2024-2026 RayRabbit Labs, Inc.

Licensed under the GNU Affero General Public License v3.0 only.
See LICENSE-AGPLv3.txt in the repository root for full terms.

SPDX-License-Identifier: AGPL-3.0-only
"""

import asyncio
import sys
import json
import argparse
import uuid
from colorama import Fore, Style, init
import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

init(autoreset=True)

# No hardcoded slash commands in a universal CLI.
SLASH_COMMANDS = []

class UniversalChatbot:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url

    def validate_query(self, query: str) -> bool:
        if not query or not query.strip():
            print(f"{Fore.RED}Debe ingresar un comando valido{Style.RESET_ALL}")
            return False
        return True

    async def run_repl(self):
        print(f"\n{Fore.CYAN}{Style.BRIGHT}=======================================================")
        print(f"{Fore.CYAN}{Style.BRIGHT}          RAYRABBIT UNIVERSAL A2UI CLI                 ")
        print(f"{Fore.CYAN}{Style.BRIGHT}=======================================================")
        print(f"Conectándose al stream de actualización...")
        
        correlation_id = str(uuid.uuid4())
        ws_endpoint = f"{self.ws_url.replace('http://', 'ws://').replace('https://', 'wss://').rstrip('/')}/ws/a2ui/{correlation_id}"
        
        max_retries = 15
        for attempt in range(1, max_retries + 1):
            try:
                async with websockets.connect(ws_endpoint) as websocket:
                    print(f"{Fore.GREEN}¡Conectado exitosamente!{Style.RESET_ALL}")
                    print("Escriba su consulta (ej. '¿Cuál es el valor del BTC?' o 'Muéstrame el dashboard')")
                    print("Escriba 'salir' o 'exit' para terminar.\n")
                    
                    # Start background task to listen to incoming websocket messages
                    listener_task = asyncio.create_task(self._websocket_listener(websocket))
                    
                    # Configure autocompletion
                    completer = WordCompleter(SLASH_COMMANDS, ignore_case=True)
                    session = PromptSession(completer=completer)
                    
                    while True:
                        try:
                            # Get user input with prompt_toolkit for autocompletion
                            user_input = await session.prompt_async("A2UI> ", completer=completer)
                        except (KeyboardInterrupt, EOFError):
                            print("\nSaliendo...")
                            break
                        
                        if user_input.strip().lower() in ["salir", "exit"]:
                            print("Saliendo...")
                            break
                        
                        if not self.validate_query(user_input):
                            continue
                        
                        # Send human_query request over websocket
                        query_payload = {
                            "name": "human_query",
                            "params": {
                                "query_input": user_input
                            }
                        }
                        await websocket.send(json.dumps(query_payload))
                        print(f"{Fore.YELLOW}Enviando consulta...{Style.RESET_ALL}")
                        
                        # Sleep slightly to let the listener print output
                        await asyncio.sleep(1)

                    listener_task.cancel()
                    break
            except Exception as e:
                if attempt < max_retries:
                    print(f"{Fore.YELLOW}Esperando a que el Hub esté listo ({attempt}/{max_retries})...{Style.RESET_ALL}")
                    await asyncio.sleep(2)
                else:
                    print(f"{Fore.RED}Error de conexión tras {max_retries} intentos: {e}{Style.RESET_ALL}")

    async def run_one_shot(self, query: str):
        if not self.validate_query(query):
            sys.exit(1)
            
        correlation_id = str(uuid.uuid4())
        ws_endpoint = f"{self.ws_url.replace('http://', 'ws://').replace('https://', 'wss://').rstrip('/')}/ws/a2ui/{correlation_id}"
        
        try:
            async with websockets.connect(ws_endpoint) as websocket:
                # Send human_query request
                query_payload = {
                    "name": "human_query",
                    "params": {
                        "query_input": query
                    }
                }
                await websocket.send(json.dumps(query_payload))
                
                # Wait for response
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    a2ui_data = data.get("a2ui", {})
                    if a2ui_data.get("version") == "v0.9.1":
                        update_model = a2ui_data.get("updateDataModel", {})
                        if update_model.get("path") == "/narrative":
                            narrative = update_model.get("value", "")
                            print(f"\n{Fore.GREEN}{Style.BRIGHT}[RESPUESTA]:{Style.RESET_ALL}")
                            print(narrative)
                            print()
                        if update_model.get("path") == "/working" and update_model.get("value") is False:
                            break
        except Exception as e:
            print(f"{Fore.RED}Error de conexión: {e}{Style.RESET_ALL}")
            sys.exit(1)

    async def _websocket_listener(self, websocket):
        try:
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                a2ui_data = data.get("a2ui", {})
                if a2ui_data.get("version") == "v0.9.1":
                    update_model = a2ui_data.get("updateDataModel", {})
                    
                    if update_model.get("path") == "/narrative":
                        narrative = update_model.get("value", "")
                        print(f"\n{Fore.GREEN}{Style.BRIGHT}[RESPUESTA]:{Style.RESET_ALL}")
                        print(narrative)
                        print("\nA2UI> ", end="", flush=True)
                    
                    elif update_model.get("path") == "/working":
                        working = update_model.get("value")
                        if working:
                            print(f"\n{Fore.BLUE}[Pensando...]{Style.RESET_ALL}", end="", flush=True)
                        else:
                            # Finished thinking
                            pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n{Fore.RED}Error en el stream de eventos: {e}{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="RayRabbit Universal A2UI CLI")
    parser.add_argument("-q", "--query", type=str, help="Ejecutar consulta en una sola llamada (one-shot)")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8005", help="URL del hub de RayRabbit")
    args = parser.parse_args()
    
    chatbot = UniversalChatbot(args.url)
    
    if args.query:
        asyncio.run(chatbot.run_one_shot(args.query))
    else:
        try:
            asyncio.run(chatbot.run_repl())
        except KeyboardInterrupt:
            print("\nSaliendo...")

if __name__ == "__main__":
    main()
