"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
import json
from json.decoder import JSONDecodeError
import os
import importlib.resources
from typing import Any
from abc import ABC, abstractmethod

ENCODING = "utf-8"

class A2uiSchemaLoader(ABC):
    """Abstract base class for loading schema files."""
    @abstractmethod
    def load(self, filename: str) -> Any:
        pass

class FileSystemLoader(A2uiSchemaLoader):
    """Loads schema files from the local filesystem."""
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def load(self, filename: str) -> Any:
        path = os.path.join(self.base_dir, filename)
        with open(path, "r", encoding=ENCODING) as f:
            return json.load(f)

class PackageLoader(A2uiSchemaLoader):
    """Loads schema files from package resources (agnostic)."""
    def __init__(self, package_path: str):
        self.package_path = package_path

    def load(self, filename: str) -> Any:
        try:
            # For Python 3.9+, use files() API
            traversable = importlib.resources.files(self.package_path)
            resource_path = traversable.joinpath(filename)
            with resource_path.open("r", encoding=ENCODING) as f:
                return json.load(f)
        except (ModuleNotFoundError, FileNotFoundError, JSONDecodeError, AttributeError) as e:
            raise IOError(
                f"Could not load package resource {filename} in {self.package_path}: {e}"
            ) from e
