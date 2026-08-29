"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import copy
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple
from jsonschema import Draft202012Validator

if TYPE_CHECKING:
    from .catalog import A2uiCatalog

from .constants import CATALOG_COMPONENTS_KEY, CATALOG_STYLES_KEY

def _inject_additional_properties(schema: Dict[str, Any], source_properties: Dict[str, Any]) -> Tuple[Dict[str, Any], Set[str]]:
    injected_keys = set()
    def recursive_inject(obj):
        if isinstance(obj, dict):
            new_obj = {}
            for k, v in obj.items():
                if isinstance(v, dict) and v.get("additionalProperties") is True:
                    if k in source_properties:
                        injected_keys.add(k)
                        new_node = dict(v)
                        new_node["additionalProperties"] = False
                        new_node["properties"] = {**new_node.get("properties", {}), **source_properties[k]}
                        new_obj[k] = new_node
                    else:
                        new_obj[k] = recursive_inject(v)
                else:
                    new_obj[k] = recursive_inject(v)
            return new_obj
        elif isinstance(obj, list):
            return [recursive_inject(i) for i in obj]
        return obj
    return recursive_inject(schema), injected_keys

def _wrap_main_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "array", "items": schema}

class A2uiValidator:
    def __init__(self, catalog: "A2uiCatalog"):
        self._catalog = catalog
        self._validator = self._build_validator()

    def _build_validator(self) -> Draft202012Validator:
        bundled = copy.deepcopy(self._catalog.s2c_schema)
        source_properties = {}
        catalog_schema = self._catalog.catalog_schema
        if catalog_schema:
            if CATALOG_COMPONENTS_KEY in catalog_schema:
                source_properties["component"] = catalog_schema[CATALOG_COMPONENTS_KEY]
            if CATALOG_STYLES_KEY in catalog_schema:
                source_properties[CATALOG_STYLES_KEY] = catalog_schema[CATALOG_STYLES_KEY]
        bundled, _ = _inject_additional_properties(bundled, source_properties)
        full_schema = _wrap_main_schema(bundled)
        return Draft202012Validator(full_schema)

    def validate(self, message: Dict[str, Any]) -> None:
        error = next(self._validator.iter_errors(message), None)
        if error is not None:
            raise ValueError(f"A2UI Validation failed: {error.message}")
