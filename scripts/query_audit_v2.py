import asyncio
import json
from typing import List
import os

from rayrabbit.utils.config import ConfigManager
from rayrabbit.security.maestro import MAESTROSecurity
from rayrabbit.security.sqlite_audit_provider import SQLiteAuditProvider
from rayrabbit.security.auditing import AuditManager, AuditEvent


async def query_and_print_logs(db_path_arg: str = None) -> None:
    """
    Initializes the necessary security components to securely read, decrypt,
    and print events from the audit database.
    """
    print("--- Lector de Logs de Auditoría de RayRabbit (MAESTRO) ---")
    
    audit_manager = None
    try:
        # Pre-cargar variables de entorno del caso de uso logístico para consistencia de claves
        from dotenv import load_dotenv
        env_path = os.path.join("rayrabbit", "examples", "logistics_use_case", ".env")
        if os.path.exists(env_path):
            print(f"Cargando .env desde: {env_path}")
            load_dotenv(env_path)
        else:
            print(f"ADVERTENCIA: No se encontró .env en {env_path}, intentando claves de sistema...")

        # 1. Cargar la configuración
        print("Cargando configuración desde config.yaml...")
        config_manager = ConfigManager()
        config_manager.load_from_file("config.yaml")
        security_config = config_manager.data.security
        
        # OSS: El single source of truth es config.yaml para evitar discrepancias.
        # Solo usamos ENV si config está vacío.
        if not security_config.master_secret:
            security_config.master_secret = os.getenv("RAYRABBIT_MASTER_SECRET")
        if not security_config.salt:
            security_config.salt = os.getenv("RAYRABBIT_SECURITY_SALT")

        print(f"[DEBUG QUERY] Final Key Used: {security_config.master_secret[:5]}... / {security_config.salt[:5]}...")

        if not security_config.master_secret or not security_config.salt:
            print("\nERROR: 'master_secret' y 'salt' no encontrados en config.yaml.")
            return

        # 2. Determinar la base de datos a usar
        default_db = security_config.auditing_config.get('db_path', 'audit_logs/audit.db')
        target_db = db_path_arg or default_db
        
        # Ajustar ruta si es relativa
        if not os.path.isabs(target_db):
            target_db = os.path.join(os.getcwd(), target_db)
            
        print(f"Objetivo de auditoría: {target_db}")
        
        # Inferir Agent ID del nombre del archivo para derivar las claves correctas
        # Formato esperado: agent_{AGENT_ID}_audit.db o audit.db (core)
        filename = os.path.basename(target_db)
        if filename.startswith("agent_") and filename.endswith("_audit.db"):
            agent_id = filename[6:-9]  # Remove 'agent_' and '_audit.db'
            print(f"Detectado Agente Log: {agent_id} (usando esta identidad para desencriptar)")
        else:
            agent_id = "rayrabbit_framework_core"
            print(f"Detectado Log Core (usando identidad framework_core)")

        # 3. Implementar la secuencia de inicialización limpia
        # Crear AuditManager
        audit_manager = AuditManager()
        # Crear MAESTRO con la identidad correcta para que coincidan las claves derivadas
        maestro = MAESTROSecurity(agent_id, security_config, audit_manager)
        
        # Crear el Provider apuntando a la DB específica
        provider = SQLiteAuditProvider(db_path=target_db, maestro=maestro)
        # Completar el ciclo
        audit_manager.set_storage_provider(provider)
        
        await audit_manager.start()

        # 4. Consultar los eventos
        print(f"\nConsultando los últimos 100 eventos...")
        events: List[AuditEvent] = await provider.get_events(limit=100)

        if not events:
            print("\nNo se encontraron eventos de auditoría en la base de datos.")
        else:
            print(f"\n--- Mostrando {len(events)} evento(s) ---")
            for event in events:
                print("-" * 60)
                print(f"  ID Evento      : {event.event_id}")
                print(f"  Timestamp      : {event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else event.timestamp}")
                print(f"  Nivel/Categoría : {event.level.value if hasattr(event.level, 'value') else event.level} / {event.category.value if hasattr(event.category, 'value') else event.category}")
                print(f"  Tipo/Acción    : {event.event_type} -> {event.action}")
                print(f"  Agente/Usuario : {event.agent_id or 'N/A'} / {event.user_id or 'N/A'}")
                print(f"  Correlation ID : {event.correlation_id or 'N/A'}")
                print(f"  Resultado      : {event.result}")
                
                # Mostrar detalles de forma legible y resumida
                details = event.details
                if isinstance(details, str):
                    try: details = json.loads(details)
                    except: pass
                
                if isinstance(details, dict):
                    # Simplificación inteligente para logs de comunicación
                    if "recipient_id" in details and "message_type" in details:
                        summary = f"Destino: {details['recipient_id']} | Tipo: {details['message_type']}"
                        if details.get("is_broadcast"): summary += " [BROADCAST]"
                        print(f"  Detalles       : {summary}")
                    else:
                        # Para otros eventos, mostrar una versión compacta
                        compact = json.dumps(details, ensure_ascii=False)
                        print(f"  Detalles       : {compact[:120]}..." if len(compact) > 120 else f"  Detalles       : {compact}")
                else:
                    print(f"  Detalles       : {details}")
            print("-" * 60)

    except FileNotFoundError:
        print("\nERROR: No se encontró el archivo 'config.yaml'. Ejecuta este script desde la raíz del proyecto.")
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")
    finally:
        if audit_manager:
            await audit_manager.stop()

if __name__ == "__main__":
    asyncio.run(query_and_print_logs())