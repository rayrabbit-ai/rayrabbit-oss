"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import os

# Asset package for importlib.resources
A2UI_ASSET_PACKAGE = "rayrabbit.protocols.a2ui.specs"
SERVER_TO_CLIENT_SCHEMA_KEY = "server_to_client"
COMMON_TYPES_SCHEMA_KEY = "common_types"
CATALOG_SCHEMA_KEY = "catalog"
CATALOG_COMPONENTS_KEY = "components"
CATALOG_ID_KEY = "catalogId"
CATALOG_STYLES_KEY = "styles"

BASE_SCHEMA_URL = "https://a2ui.org/"
BASIC_CATALOG_NAME = "basic"
INLINE_CATALOG_NAME = "inline"

SPEC_VERSION_MAP = {
    "0.8": {
        SERVER_TO_CLIENT_SCHEMA_KEY: "v0_8/server_to_client.json",
        CATALOG_SCHEMA_KEY: "v0_8/standard_catalog_definition.json",
    },
    "0.9": {
        SERVER_TO_CLIENT_SCHEMA_KEY: "server_to_client.json",
        COMMON_TYPES_SCHEMA_KEY: "common_types.json",
        CATALOG_SCHEMA_KEY: "standard_catalog.json",
    },
    "0.9.1": {
        SERVER_TO_CLIENT_SCHEMA_KEY: "server_to_client.json",
        COMMON_TYPES_SCHEMA_KEY: "common_types.json",
        CATALOG_SCHEMA_KEY: "standard_catalog.json",
    },
    "0.10": {
        SERVER_TO_CLIENT_SCHEMA_KEY: "server_to_client.json",
        COMMON_TYPES_SCHEMA_KEY: "common_types.json",
        CATALOG_SCHEMA_KEY: "standard_catalog.json",
    }
}
