# Sovereign Node Catalog and Port Registry

This document lists the active sovereign agent nodes, reference cognitive services, and federated external endpoints connected to the **RayRabbit Universal Interoperability Infrastructure (L3)**.

---

## 1. Logistics Orchestrator (LangChain Agent Node)
- **ID**: `logistics_manager`
- **Name**: Global Logistics Manager
- **Protocols**: `["a2a", "mcp", "http"]`
- **Capabilities**: `["order_analysis", "inventory_dispatch", "conflict_resolution", "analyze_order", "track_package"]`
- **Endpoints**:
  - **A2A Endpoint**: `http://127.0.0.1:8002/a2a`
  - **MCP Base**: `http://127.0.0.1:8002/mcp`
  - **MCP Tools List**: `http://127.0.0.1:8002/mcp/tools`
  - **MCP Tool Invocation**: `http://127.0.0.1:8002/mcp/call`
- **Description**: Ingests customer intentions, coordinates multi-modal logistics plans, and fulfills orders. Exposes atomic MCP tools: `analyze_order`, `track_package`.

---

## 2. Shipping & Route Planner (CrewAI Squad Node)
- **ID**: `route_optimizer`
- **Name**: DeepRoute Optimizer
- **Protocols**: `["a2a", "mcp", "http"]`
- **Capabilities**: `["route_planning", "carrier_selection", "eta_calculation", "optimize_route", "select_carrier"]`
- **Endpoints**:
  - **A2A Endpoint**: `http://127.0.0.1:8001/a2a`
  - **MCP Base**: `http://127.0.0.1:8001/mcp`
  - **MCP Tools List**: `http://127.0.0.1:8001/mcp/tools`
  - **MCP Tool Invocation**: `http://127.0.0.1:8001/mcp/call`
- **Description**: Multi-agent hierarchical squad that calculates optimal freight routes across multimodal carriers. Exposes atomic MCP tools: `optimize_route`, `select_carrier`.

---

## 3. Fleet Manager (AutoGen Agent Node)
- **ID**: `fleet_commander`
- **Name**: Autonomous Fleet Commander
- **Protocols**: `["a2a", "mcp", "http"]`
- **Capabilities**: `["vehicle_assignment", "fuel_optimization", "driver_scheduling", "sap_tm_availability", "schedule_driver"]`
- **Endpoints**:
  - **A2A Endpoint**: `http://127.0.0.1:8003/a2a`
  - **MCP Base**: `http://127.0.0.1:8003/mcp`
  - **MCP Tools List**: `http://127.0.0.1:8003/mcp/tools`
  - **MCP Tool Invocation**: `http://127.0.0.1:8003/mcp/call`
- **Description**: Real-time vehicle dispatching, telemetry monitoring, and SAP TM schedule synchronization. Exposes atomic MCP tools: `sap_tm_availability`, `schedule_driver`.

---

## 4. Federated External Systems (Shared Services via DeclarativeBridge)
### Global Inventory Service
- **Type**: `MCP_SERVICE` / `REST_BRIDGE`
- **OpenAPI URL**: `http://127.0.0.1:8010/openapi.json`
- **Description**: High-concurrency warehouse inventory registry across regional fulfillment hubs.

### Weather Intelligence Service
- **Type**: `MCP_SERVICE` / `REST_BRIDGE`
- **OpenAPI URL**: `https://weather.rayrabbit.io/openapi.json`
- **Description**: Weather telemetry and road condition analysis for real-time route re-routing.

---