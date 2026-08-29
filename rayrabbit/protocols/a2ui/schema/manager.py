"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import logging
from typing import List, Dict, Any, Optional, Callable
from .loader import PackageLoader
from ..inference_strategy import InferenceStrategy
from .constants import (
    A2UI_ASSET_PACKAGE,
    SERVER_TO_CLIENT_SCHEMA_KEY,
    COMMON_TYPES_SCHEMA_KEY,
    CATALOG_SCHEMA_KEY,
    CATALOG_ID_KEY,
    BASE_SCHEMA_URL,
    SPEC_VERSION_MAP,
    BASIC_CATALOG_NAME,
)
from .catalog import CustomCatalogConfig, A2uiCatalog

def _load_basic_component(version: str, spec_name: str) -> Dict:
    spec_map = SPEC_VERSION_MAP.get(version, {})
    if spec_name not in spec_map:
        return None
    filename = spec_map[spec_name]
    
    # Intentar cargar desde el subpaquete de versión (e.g., .v0_8)
    # Si falla, intentar desde el paquete base (e.g., rayrabbit.protocols.a2ui.specs)
    v_package = f"v{version.replace('.', '_')}"
    try:
        loader = PackageLoader(f"{A2UI_ASSET_PACKAGE}.{v_package}")
        return loader.load(filename)
    except (IOError, ModuleNotFoundError):
        # Fallback al paquete base
        loader = PackageLoader(A2UI_ASSET_PACKAGE)
        return loader.load(filename)

class A2uiSchemaManager(InferenceStrategy):
    def __init__(self, version: str, basic_examples_path: Optional[str] = None):
        self._version = version
        self._server_to_client_schema = _load_basic_component(version, SERVER_TO_CLIENT_SCHEMA_KEY)
        self._common_types_schema = _load_basic_component(version, COMMON_TYPES_SCHEMA_KEY)
        
        basic_catalog_schema = _load_basic_component(version, CATALOG_SCHEMA_KEY)
        if CATALOG_ID_KEY not in basic_catalog_schema:
            basic_catalog_schema[CATALOG_ID_KEY] = f"{BASE_SCHEMA_URL}specification/v{version.replace('.', '_')}/standard_catalog_definition.json"
        
        self._basic_catalog = A2uiCatalog(
            version=version,
            name=BASIC_CATALOG_NAME,
            catalog_schema=basic_catalog_schema,
            s2c_schema=self._server_to_client_schema,
            common_types_schema=self._common_types_schema,
        )
        self._examples_path = basic_examples_path

    def generate_system_prompt(
        self,
        role_description: str,
        workflow_description: str = "",
        ui_description: str = "",
        client_ui_capabilities: Optional[dict[str, Any]] = None,
        allowed_components: List[str] = [],
        include_schema: bool = False,
        include_examples: bool = False,
        validate_examples: bool = False,
    ) -> str:
        parts = [role_description]
        if workflow_description:
            parts.append(f"## Workflow Description:\n{workflow_description}")
        if ui_description:
            parts.append(f"## UI Description:\n{ui_description}")
        
        catalog = self._basic_catalog.with_pruned_components(allowed_components)
        if include_schema:
            parts.append(catalog.render_as_llm_instructions())
        if include_examples and self._examples_path:
            examples_str = catalog.load_examples(self._examples_path, validate=validate_examples)
            if examples_str:
                parts.append(f"### Examples:\n{examples_str}")
        return "\n\n".join(parts)
