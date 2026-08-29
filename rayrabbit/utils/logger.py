"""
RayRabbit OSS - Universal Agent Interoperability Infrastructure
Copyright © 2024-2026 RayRabbit Labs, Inc.

Este archivo forma parte del núcleo de código abierto de RayRabbit y está
licenciado bajo la GNU Affero General Public License v3.0 only.

Puedes usar, modificar y redistribuir este archivo bajo los términos de la AGPL v3.
Consulta LICENSE-AGPLv3.txt en la raíz del repositorio para el texto completo.

SPDX-License-Identifier: AGPL-3.0-only
"""
"""
Sistema de Logging para RayRabbit

Proporciona logging configurado y consistente para todo el framework.
"""

import logging
import sys
from typing import Dict
from datetime import datetime

class RayRabbitFormatter(logging.Formatter):
    """Formateador personalizado para logs de RayRabbit."""
    
    def __init__(self) -> None:
        super().__init__()
        
    def format(self, record: logging.LogRecord) -> str:
        colors = {
            'DEBUG': '\033[36m',
            'INFO': '\033[32m',
            'WARNING': '\033[33m',
            'ERROR': '\033[31m',
            'CRITICAL': '\033[35m',
        }
        reset = '\033[0m'
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level_color = colors.get(record.levelname, '')
        formatted = f"{timestamp} | {level_color}{record.levelname:8}{reset} | {record.name:20} | {record.getMessage()}"
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        return formatted

class RayRabbitLogger:
    """Gestor de logging para RayRabbit."""
    
    _loggers: Dict[str, logging.Logger] = {}
    _configured = False
    
    @classmethod
    def configure(cls, level: str = "INFO", format_type: str = "colored") -> None:
        if cls._configured:
            return
        root_logger = logging.getLogger("rayrabbit")
        root_logger.setLevel(getattr(logging, level.upper()))
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        formatter: logging.Formatter
        if format_type == "colored":
            formatter = RayRabbitFormatter()
        elif format_type == "simple":
            formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        else:
            formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        root_logger.propagate = False
        cls._configured = True
        
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        if not cls._configured:
            cls.configure()
        if name in cls._loggers:
            return cls._loggers[name]
        full_name = f"rayrabbit.{name}" if not name.startswith("rayrabbit") else name
        logger = logging.getLogger(full_name)
        cls._loggers[name] = logger
        return logger

def get_logger(name: str) -> logging.Logger:
    return RayRabbitLogger.get_logger(name)

def configure_logging(level: str = "INFO", format_type: str = "colored") -> None:
    RayRabbitLogger.configure(level, format_type)
