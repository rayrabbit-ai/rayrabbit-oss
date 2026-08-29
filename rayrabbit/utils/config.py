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
Sistema de Configuración para la Infraestructura de IA RayRabbit

Gestiona la configuración de manera centralizada, unificando la carga desde
archivos, variables de entorno y modificaciones programáticas en una estructura tipada.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Dataclasses de Configuración Anidados --- #

@dataclass
class MessageBusConfig:
    """Configuración del MessageBus."""
    instance_id: str = "default_instance"
    enable_persistence: bool = True
    max_message_history: int = 1000
    heartbeat_interval: float = 5.0
    timeout: float = 30.0

@dataclass
class A2AConfig:
    """Configuración del protocolo A2A."""
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    compression: bool = True
    default_port: int = 8005

@dataclass
class MCPConfig:
    """Configuración del protocolo MCP."""
    heartbeat_interval: float = 5.0
    election_timeout: float = 10.0
    consensus_timeout: float = 30.0
    leader_timeout: float = 15.0
    consensus_threshold: float = 0.5

@dataclass
class LoggingConfig:
    """Configuración del sistema de logging."""
    level: str = "INFO"
    format_type: str = "colored"
    file_logging: bool = False
    log_file: str = "rayrabbit.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5

@dataclass
class SecurityConfig:
    """Configuración de seguridad."""
    enable_auth: bool = False
    auth_method: str = "oauth2"
    token_expiry: int = 3600  # segundos
    encryption_enabled: bool = False
    keystore_path: str = "./rayrabbit_keystore"
    master_secret: Optional[str] = None
    salt: Optional[str] = None
    authentication_config: Dict[str, Any] = field(default_factory=dict)
    authorization_config: Dict[str, Any] = field(default_factory=dict)
    auditing_config: Dict[str, Any] = field(default_factory=dict)
    validation_config: Dict[str, Any] = field(default_factory=dict)
    threat_detection_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuditingConfig:
    """Configuración del sistema de auditoría."""
    enable_audit: bool = True
    storage_provider: str = "sqlite"
    sqlite_db_path: str = "audit_logs/audit.db"

@dataclass
class RayRabbitConfig:
    """Dataclass raíz que contiene toda la configuración de la infraestructura."""
    message_bus: MessageBusConfig = field(default_factory=MessageBusConfig)
    a2a: A2AConfig = field(default_factory=A2AConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    auditing: AuditingConfig = field(default_factory=AuditingConfig) # <--- ADDED THIS LINE
    custom: Dict[str, Any] = field(default_factory=dict)

# --- Gestor de Configuración --- #

class ConfigManager:
    """
    Gestor de configuración centralizado para RayRabbit.
    
    Soporta configuración desde:
    - Variables de entorno
    - Archivos JSON/YAML
    - Configuración programática
    
    Opera sobre un dataclass RayRabbitConfig para proporcionar carga, guardado y acceso dinámico.
    """
    
    def __init__(self, config_object: Optional[RayRabbitConfig] = None):
        """Inicializa el gestor con una configuración por defecto o una existente."""
        self.data = config_object or RayRabbitConfig()
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Carga configuración desde variables de entorno."""
        env_mappings = {
            "RAYRABBIT_MESSAGE_BUS_PERSISTENCE": ("message_bus", "enable_persistence", bool),
            "RAYRABBIT_MESSAGE_BUS_MAX_HISTORY": ("message_bus", "max_message_history", int),
            "RAYRABBIT_MESSAGE_BUS_HEARTBEAT": ("message_bus", "heartbeat_interval", float),
            "RAYRABBIT_MESSAGE_BUS_TIMEOUT": ("message_bus", "timeout", float),
            "RAYRABBIT_A2A_TIMEOUT": ("a2a", "timeout", float),
            "RAYRABBIT_A2A_MAX_RETRIES": ("a2a", "max_retries", int),
            "RAYRABBIT_A2A_RETRY_DELAY": ("a2a", "retry_delay", float),
            "RAYRABBIT_A2A_COMPRESSION": ("a2a", "compression", bool),
            "RAYRABBIT_A2A_DEFAULT_PORT": ("a2a", "default_port", int),
            "RAYRABBIT_MCP_HEARTBEAT": ("mcp", "heartbeat_interval", float),
            "RAYRABBIT_MCP_ELECTION_TIMEOUT": ("mcp", "election_timeout", float),
            "RAYRABBIT_MCP_CONSENSUS_TIMEOUT": ("mcp", "consensus_timeout", float),
            "RAYRABBIT_MCP_LEADER_TIMEOUT": ("mcp", "leader_timeout", float),
            "RAYRABBIT_MCP_CONSENSUS_THRESHOLD": ("mcp", "consensus_threshold", float),
            "RAYRABBIT_LOG_LEVEL": ("logging", "level", str),
            "RAYRABBIT_LOG_FORMAT": ("logging", "format_type", str),
            "RAYRABBIT_LOG_FILE_ENABLED": ("logging", "file_logging", bool),
            "RAYRABBIT_LOG_FILE": ("logging", "log_file", str),
            "RAYRABBIT_AUTH_ENABLED": ("security", "enable_auth", bool),
            "RAYRABBIT_AUTH_METHOD": ("security", "auth_method", str),
            "RAYRABBIT_TOKEN_EXPIRY": ("security", "token_expiry", int),
            "RAYRABBIT_ENCRYPTION_ENABLED": ("security", "encryption_enabled", bool),
            "RAYRABBIT_MASTER_SECRET": ("security", "master_secret", str),
            "RAYRABBIT_SALT": ("security", "salt", str),
        }
        
        for env_var, (section_name, key, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if type_func is bool:
                        converted_value = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        converted_value = type_func(value)
                    
                    section_obj = getattr(self.data, section_name)
                    setattr(section_obj, key, converted_value)
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"Warning: Invalid value or section for {env_var}: {value} ({e})")

    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """
        Carga configuración desde un archivo.
        
        Args:
            file_path: Ruta al archivo de configuración (JSON o YAML)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    raw_data = yaml.safe_load(f)
                else:
                    raw_data = json.load(f)
            self._apply_dict(raw_data)
            # Reimponer las variables de entorno para que tengan precedencia
            self._load_from_env()
        except Exception as e:
            raise ValueError(f"Error cargando configuración desde {file_path}: {e}")

    def _apply_dict(self, raw_data: Dict[str, Any]) -> None:
        """
        Aplica un diccionario a la configuración del dataclass anidado.
        """
        for section_name, config_data in raw_data.items():
            # Tratar 'custom' como un caso especial para actualizar el diccionario
            if section_name == 'custom':
                self.data.custom.update(config_data)
            # Para otras secciones, aplicar a los atributos del dataclass
            elif hasattr(self.data, section_name) and isinstance(config_data, dict):
                section_obj = getattr(self.data, section_name)
                for key, value in config_data.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

    def save_to_file(self, file_path: Union[str, Path], format_type: str = "yaml") -> None:
        """
        Guarda la configuración actual a un archivo.
        
        Args:
            file_path: Ruta donde guardar el archivo
            format_type: Formato del archivo ("yaml" o "json")
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        config_dict = asdict(self.data)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if format_type.lower() == "yaml":
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Error guardando configuración en {file_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de punto.
        
        Args:
            key: Clave en formato "section.key" (ej: "a2a.timeout")
            default: Valor por defecto si no se encuentra
            
        Returns:
            Valor de configuración o default
        """
        try:
            section_name, key_name = key.split('.', 1)
            section = getattr(self.data, section_name, None)
            if section is None:
                return self.data.custom.get(key, default)
            return getattr(section, key_name, default)
        except (AttributeError, KeyError, ValueError):
            return self.data.custom.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración usando notación de punto.
        
        Args:
            key: Clave en formato "section.key"
            value: Valor a establecer
        """
        try:
            section_name, key_name = key.split('.', 1)
            section = getattr(self.data, section_name, None)
            if section is not None and hasattr(section, key_name):
                setattr(section, key_name, value)
            else:
                self.data.custom[key] = value
        except ValueError:
            self.data.custom[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte toda la configuración a un diccionario.
        
        Returns:
            Diccionario con toda la configuración
        """
        return asdict(self.data)

    def validate(self) -> bool:
        """
        Valida la configuración actual.
        
        Returns:
            True si la configuración es válida
        """
        try:
            assert 0 < self.data.message_bus.max_message_history <= 100000
            assert 0.1 <= self.data.message_bus.heartbeat_interval <= 60
            assert 1 <= self.data.message_bus.timeout <= 300
            assert 1 <= self.data.a2a.timeout <= 300
            assert 1 <= self.data.a2a.max_retries <= 10
            assert 0.1 <= self.data.a2a.retry_delay <= 10
            assert 1024 <= self.data.a2a.default_port <= 65535
            assert 0.1 <= self.data.mcp.heartbeat_interval <= 60
            assert 1 <= self.data.mcp.election_timeout <= 60
            assert 1 <= self.data.mcp.consensus_timeout <= 300
            assert 1 <= self.data.mcp.leader_timeout <= 60
            assert 0.1 <= self.data.mcp.consensus_threshold <= 1.0
            assert self.data.logging.level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            assert self.data.logging.format_type in ['colored', 'simple', 'json']
            assert self.data.security.auth_method in ['oauth2', 'jwt', 'basic']
            assert 60 <= self.data.security.token_expiry <= 86400
            return True
        except AssertionError:
            return False

    def reset_to_defaults(self) -> None:
        """Resetea toda la configuración a valores por defecto."""
        self.data = RayRabbitConfig()
        self._load_from_env()

# --- Instancia Global --- #

_global_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """
    Obtiene la instancia global del gestor de configuración.
    
    Returns:
        Instancia de configuración global
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager

def set_config_manager(manager: ConfigManager) -> None:
    """
    Establece la instancia global del gestor de configuración.
    
    Args:
        manager: Nueva instancia del gestor de configuración
    """
    global _global_config_manager
    _global_config_manager = manager