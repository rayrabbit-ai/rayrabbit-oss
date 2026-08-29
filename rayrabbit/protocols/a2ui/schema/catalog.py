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
import json
import logging
import os
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from .constants import CATALOG_COMPONENTS_KEY, CATALOG_ID_KEY

if TYPE_CHECKING:
    from .validator import A2uiValidator

@dataclass
class CustomCatalogConfig:
    name: str
    catalog_path: str
    examples_path: Optional[str] = None

@dataclass(frozen=True)
class A2uiCatalog:
    version: str
    name: str
    s2c_schema: Dict[str, Any]
    catalog_schema: Dict[str, Any]
    common_types_schema: Optional[Dict[str, Any]] = None

    @property
    def catalog_id(self) -> str:
        if CATALOG_ID_KEY not in self.catalog_schema:
            raise ValueError(f"Catalog '{self.name}' missing catalogId")
        return self.catalog_schema[CATALOG_ID_KEY]

    @property
    def validator(self) -> "A2uiValidator":
        from .validator import A2uiValidator
        return A2uiValidator(self)

    def with_pruned_components(self, allowed_components: List[str]) -> "A2uiCatalog":
        if not allowed_components:
            return self
        schema_copy = copy.deepcopy(self.catalog_schema)
        if CATALOG_COMPONENTS_KEY in schema_copy and isinstance(schema_copy[CATALOG_COMPONENTS_KEY], dict):
            all_comps = schema_copy[CATALOG_COMPONENTS_KEY]
            schema_copy[CATALOG_COMPONENTS_KEY] = {
                k: v for k, v in all_comps.items() if k in allowed_components
            }
        return replace(self, catalog_schema=schema_copy)

    @staticmethod
    def _prune_schema_dict(schema: Any) -> Any:
        if isinstance(schema, dict):
            pruned = {}
            for k, v in schema.items():
                if k == "description" and isinstance(v, str):
                    if len(v) > 50:
                        pruned[k] = v[:47] + "..."
                    else:
                        pruned[k] = v
                elif k in ("title", "$schema", "$id"):
                    continue
                else:
                    pruned[k] = A2uiCatalog._prune_schema_dict(v)
            return pruned
        elif isinstance(schema, list):
            return [A2uiCatalog._prune_schema_dict(item) for item in schema]
        return schema

    def render_as_llm_instructions(self) -> str:
        all_schemas = ["---BEGIN A2UI JSON SCHEMA---"]
        if self.s2c_schema:
            pruned_s2c = self._prune_schema_dict(self.s2c_schema)
            all_schemas.append(f"### Server To Client Schema:\n{json.dumps(pruned_s2c, separators=(',', ':'))}")
        if self.common_types_schema:
            pruned_common = self._prune_schema_dict(self.common_types_schema)
            all_schemas.append(f"### Common Types Schema:\n{json.dumps(pruned_common, separators=(',', ':'))}")
        pruned_catalog = self._prune_schema_dict(self.catalog_schema)
        all_schemas.append(f"### Catalog Schema:\n{json.dumps(pruned_catalog, separators=(',', ':'))}")
        all_schemas.append("---END A2UI JSON SCHEMA---")
        return "\n\n".join(all_schemas)

    def load_examples(self, path: Optional[str], validate: bool = False) -> str:
        if not path or not os.path.isdir(path):
            return ""
        merged_examples = []
        for filename in sorted(os.listdir(path)):
            if filename.endswith(".json"):
                full_path = os.path.join(path, filename)
                basename = os.path.splitext(filename)[0]
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if validate:
                            json_data = json.loads(content)
                            self.validator.validate(json_data)
                        merged_examples.append(f"---BEGIN {basename}---\n{content}\n---END {basename}---")
                except Exception as e:
                    logging.warning(f"Failed to load example {full_path}: {e}")
        return "\n\n".join(merged_examples)
