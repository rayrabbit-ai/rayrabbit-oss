"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
from typing import Dict, Any, Optional, List
from ...protocols.a2ui.agent import SovereignA2UIAgent
from ...communication.message import Message, MessageType

class LogisticsA2UIAgent(SovereignA2UIAgent):
    """
    Specialized A2UI Agent for the Logistics Use Case.
    Defines dynamic surfaces for fleet monitoring and package tracking.
    """
    
    def __init__(self, agent_id: str = "logistics_ui_manager", name: str = "Logistics UI Manager"):
        super().__init__(agent_id, name, "Manages the logistics dynamic dashboard and tracking interfaces.")
        
        # Define initial data model
        self.data_model = {
            "fleet_status": "Operational",
            "active_shipments": 12,
            "alerts": []
        }

    async def generate_dashboard(self) -> List[Dict[str, Any]]:
        """Generates the initial A2UI Dashboard surface."""
        return [
            {
                "beginRendering": {
                    "surfaceId": "logistics_dashboard",
                    "root": "main_column"
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": "logistics_dashboard",
                    "components": [
                        {
                            "id": "main_column",
                            "component": {
                                "Column": {
                                    "children": {
                                        "explicitList": ["header_text", "status_row", "fleet_list_card"]
                                    }
                                }
                            }
                        },
                        {
                            "id": "header_text",
                            "component": {
                                "Text": {
                                    "text": {"literalString": "Logistics Operations Dashboard"},
                                    "usageHint": "h1"
                                }
                            }
                        },
                        {
                            "id": "status_row",
                            "component": {
                                "Row": {
                                    "children": {
                                        "explicitList": ["status_label", "shipment_count"]
                                    },
                                    "distribution": "spaceBetween"
                                }
                            }
                        },
                        {
                            "id": "status_label",
                            "component": {
                                "Text": {
                                    "text": {"path": "/fleet_status"},
                                    "usageHint": "body"
                                }
                            }
                        },
                        {
                            "id": "shipment_count",
                            "component": {
                                "Text": {
                                    "text": {"literalString": f"Active: {self.data_model['active_shipments']}"},
                                    "usageHint": "h2"
                                }
                            }
                        }
                    ]
                }
            },
            {
                "dataModelUpdate": {
                    "surfaceId": "logistics_dashboard",
                    "contents": [
                        {"key": "fleet_status", "valueString": self.data_model["fleet_status"]},
                        {"key": "active_shipments", "valueNumber": self.data_model["active_shipments"]}
                    ]
                }
            }
        ]

    async def _handle_request(self, message: Message) -> Optional[Message]:
        """Handles logistics-specific requests."""
        content = message.content or {}
        
        if content.get("action") == "get_dashboard":
            events = await self.generate_dashboard()
            return message.create_response({
                "events": events,
                "status": "A2UI_STREAM_READY"
            })
            
        return await super()._handle_request(message)

    async def update_shipment_count(self, new_count: int):
        """Simulates a real-time update from the MessageBus."""
        self.data_model["active_shipments"] = new_count
        self.logger.info(f"UI Model Updated: active_shipments={new_count}")
