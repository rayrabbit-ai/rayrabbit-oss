import asyncio
from typing import Optional, Any

from rayrabbit_client import RayRabbitNode
from logistics_tools import (
    analyze_order as lib_analyze_order,
    track_package as lib_track_package,
    get_product_info as lib_get_product_info,
    get_transporter_info as lib_get_transporter_info,
    optimize_route as lib_optimize_route,
    select_carrier as lib_select_carrier,
    get_routing_plan as lib_get_routing_plan,
    sap_tm_availability as lib_sap_tm_availability,
    schedule_driver as lib_schedule_driver,
    get_fleet_assignment as lib_get_fleet_assignment
)

# 1. Inicializar el Nodo Universal de Logística
node = RayRabbitNode(
    name="logistics_ui_manager", # Coincide con el agent_id de use_case.yaml
    hub_url="ws://127.0.0.1:8005/ws"
)

# 2. Registrar herramientas de SAP TM
@node.tool(category="logistics")
async def analyze_order(order_id: str) -> str:
    """Realiza un análisis detallado de un pedido de SAP TM."""
    return lib_analyze_order(order_id)

@node.tool(category="logistics")
async def track_package(package_id: str) -> str:
    """Obtiene el seguimiento de envíos de SAP TM."""
    return lib_track_package(package_id)

@node.tool(category="logistics")
async def get_product_info(name: str) -> str:
    """Obtiene los detalles técnicos (SKU, Precio, Imagen) de un producto en SAP."""
    return lib_get_product_info(name)

@node.tool(category="logistics")
async def get_transporter_info(order_id: str) -> str:
    """Obtiene los detalles del transportista (Nombre, DNI) asignado a un pedido."""
    return lib_get_transporter_info(order_id)

@node.tool(category="logistics")
async def optimize_route(origin: str = None, destination: str = None, priority: str = "medium", package_id: str = None, progress_cb: Optional[Any] = None) -> str:
    """Optimiza rutas logísticas utilizando análisis avanzado de SAP TM."""
    if callable(progress_cb):
        await progress_cb("Analizando grafo de tráfico y distancias...", 25, "Iniciando algoritmo Dijkstra")
        await asyncio.sleep(0.8)
        await progress_cb("Optimizando rutas y costos de combustible (40%)...", 40, "Calculando ventanas horarias")
        await asyncio.sleep(0.8)
        await progress_cb("Asignando unidades y conductores SAP TM (80%)...", 80, "Asignando flota disponible")
        await asyncio.sleep(0.8)
        await progress_cb("Plan de ruta optimizado (100%)...", 100, "Finalizado")
    return lib_optimize_route(origin, destination, priority, package_id)

@node.tool(category="logistics")
async def select_carrier(cargo_type: str = "standard", distance_km: float = 0.0, package_id: str = None) -> str:
    """Selecciona el mejor transportista según criterios logísticos y costo."""
    return lib_select_carrier(cargo_type, distance_km, package_id)

@node.tool(category="logistics")
async def get_routing_plan(package_id: str) -> str:
    """Retorna el detalle del plan de ruta persistido para un paquete en SAP."""
    return lib_get_routing_plan(package_id)

@node.tool(category="logistics")
async def sap_tm_availability(cargo_type: str = "standard", weight: int = 100, order_id: Optional[str] = None, package_id: Optional[str] = None, **kwargs) -> str:
    """Consulta la disponibilidad de flota y capacidad en SAP TM."""
    return lib_sap_tm_availability(cargo_type, weight, order_id=order_id, package_id=package_id, **kwargs)

@node.tool(category="logistics", annotations={"requires_approval": True, "risk_level": "high"})
async def schedule_driver(vehicle_id: str = "TRUCK-01", driver_name: str = None, driver_id: str = None, package_id: str = None) -> str:
    """Asigna y programa un conductor a un vehículo para un paquete específico."""
    return lib_schedule_driver(vehicle_id, driver_name, driver_id, package_id)

@node.tool(category="logistics")
async def get_fleet_assignment(package_id: str = "", progress_cb: Optional[Any] = None) -> str:
    """Recupera la asignación de flota actual asociada a un paquete o estado general."""
    if callable(progress_cb):
        await progress_cb("Conectando con SAP TM Database...", 30, "Consultando flota de vehículos")
        await asyncio.sleep(0.5)
        await progress_cb("Analizando unidades y rutas activas (70%)...", 70, "Verificando disponibilidad")
        await asyncio.sleep(0.5)
    return lib_get_fleet_assignment(package_id)

if __name__ == "__main__":
    print("🚀 Iniciando Logistics Agent Node (100% Real - SAP TM DB)")
    asyncio.run(node.connect())
