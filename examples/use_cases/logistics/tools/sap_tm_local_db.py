"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import sqlite3
from pathlib import Path
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("SapTmLocal")

class SapTmLocalDb:
    """
    Gestor de Base de Datos Local para SAP TM (Soberanía Agéntica).
    Maneja su propia persistencia de pedidos sin depender de RayRabbit.
    """
    def __init__(self, db_name="sap_tm_orders.db"):
        self.db_path = Path(__file__).parent / db_name
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        is_new = not self.db_path.exists()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    status TEXT,
                    customer_id TEXT,
                    items TEXT,
                    priority TEXT,
                    location TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    sku TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    price REAL,
                    image_url TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transporters (
                    id TEXT PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    dni TEXT,
                    vehicle_id TEXT
                )
            ''')
            conn.commit()
        if is_new:
            self._seed_data()

    def _seed_data(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            orders_data = [
                ("ORD-2025-001", "delayed", "CUST-99", "Laptop, Monitor", "high", "Madrid_Sort_Center"),
                ("ORD-2025-002", "in_transit", "CUST-10", "Keyboard", "standard", "A2_Highway_Km_120"),
                ("ORD-2025-003", "ready", "CUST-05", "Office Chairs", "medium", "Warehouse_A"),
                ("REAL-E2E-123", "in_transit", "CUST-RR", "Motormech 4cv", "urgent", "Madrid_Warehouse")
            ]
            cursor.executemany("INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?)", orders_data)
            
            products_data = [
                ("MM-4CV-001", "Motormech 4cv", "Motor de alto rendimiento para logística ligera.", 1250.00, "/static/assets/motormech_4cv.png")
            ]
            cursor.executemany("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)", products_data)
            
            transporters_data = [
                ("T-100", "Carlos", "Rodríguez", "12345678X", "V-502")
            ]
            cursor.executemany("INSERT OR IGNORE INTO transporters VALUES (?,?,?,?,?)", transporters_data)
            conn.commit()

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_product_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE name LIKE ?", (f"%{name}%",))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_transporter_by_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        # Por simplicidad para este caso de uso, vinculamos el transportista T-100
        # a cualquier consulta de transportista si el pedido existe.
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transporters LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_fleet_availability(self, cargo_type: str, weight: int):
        return [{"vehicle_id": "V-502", "driver": "Carlos Rodriguez", "capacity": 2000}]

    def create_assignment(self, vehicle_id: str, driver_id: str, date: str, package_id: str = None):
        return {"status": "assigned", "vehicle": vehicle_id, "driver": driver_id, "date": date}

    def get_assignment_by_package(self, package_id: str):
        return {"status": "assigned", "vehicle": "V-502", "driver": "Carlos Rodriguez"}
