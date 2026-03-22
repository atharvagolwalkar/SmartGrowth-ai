"""
Configuration Management for SmartGrowth AI Platform

This module provides environment-based configuration for the ML platform,
supporting development, staging, and production environments.
"""

import os
from typing import Optional, List
from pydantic import Field, field_validator

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover - fallback for older environments
    from pydantic import BaseSettings  # type: ignore
    SettingsConfigDict = None  # type: ignore


BOOLEAN_TRUE_VALUES = {"1", "true", "yes", "on", "debug", "development"}
BOOLEAN_FALSE_VALUES = {"0", "false", "no", "off", "release", "prod", "production"}


def _coerce_bool(value):
    """Parse loose environment boolean values without crashing imports."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in BOOLEAN_TRUE_VALUES:
            return True
        if normalized in BOOLEAN_FALSE_VALUES:
            return False
    return value

class DatabaseConfig(BaseSettings):
    """Database configuration"""
    db_path: str = Field(default="smartgrowth.db", description="Database file path")
    db_url: Optional[str] = Field(default=None, description="Full database URL override")
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")

    if SettingsConfigDict:
        model_config = SettingsConfigDict(env_prefix="DATABASE_")
    
    @property
    def database_url(self) -> str:
        """Get the complete database URL"""
        if self.db_url:
            return self.db_url
        return f"sqlite:///{self.db_path}"

class MLModelConfig(BaseSettings):
    """ML Model configuration"""
    model_path: str = Field(default="ml_models/churn/enhanced_churn_model.joblib", description="Path to saved model")
    default_threshold: float = Field(default=0.5, description="Default prediction threshold")
    batch_size: int = Field(default=100, description="Batch prediction size limit")
    model_cache_ttl: int = Field(default=3600, description="Model cache TTL in seconds")

    if SettingsConfigDict:
        model_config = SettingsConfigDict(env_prefix="ML_", protected_namespaces=())

class APIConfig(BaseSettings):
    """API configuration"""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on changes")
    log_level: str = Field(default="info", description="Logging level")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")

    if SettingsConfigDict:
        model_config = SettingsConfigDict(env_prefix="API_")

    @field_validator("debug", "reload", mode="before")
    @classmethod
    def parse_bool_fields(cls, value):
        return _coerce_bool(value)

class DashboardConfig(BaseSettings):
    """Dashboard configuration"""
    host: str = Field(default="localhost", description="Dashboard host")
    port: int = Field(default=8501, description="Dashboard port")
    api_base_url: str = Field(default="http://localhost:8000", description="Backend API URL")
    page_title: str = Field(default="SmartGrowth AI Dashboard", description="Dashboard page title")

    if SettingsConfigDict:
        model_config = SettingsConfigDict(env_prefix="DASHBOARD_")

class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_bytes: int = Field(default=10485760, description="Max log file size (10MB)")
    backup_count: int = Field(default=5, description="Number of backup log files")

    if SettingsConfigDict:
        model_config = SettingsConfigDict(env_prefix="LOG_")

class SmartGrowthConfig(BaseSettings):
    """Main configuration class"""
    environment: str = Field(default="development", description="Environment: development, staging, production")
    project_name: str = Field(default="SmartGrowth AI", description="Project name")
    version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=True, description="Global debug flag")
    
    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ml_model: MLModelConfig = Field(default_factory=MLModelConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
            protected_namespaces=()
        )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_field(cls, value):
        return _coerce_bool(value)
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() == "production"
    
    def get_database_path(self) -> str:
        """Get the full database path"""
        if os.path.isabs(self.database.db_path):
            return self.database.db_path
        
        # Make relative to project root
        project_root = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(project_root, self.database.db_path)
    
    def get_model_path(self) -> str:
        """Get the full model path"""
        if os.path.isabs(self.ml_model.model_path):
            return self.ml_model.model_path
        
        # Make relative to project root
        project_root = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(project_root, self.ml_model.model_path)

# Global configuration instance
config = SmartGrowthConfig()

# Environment-specific overrides
if config.environment.lower() == "production":
    # Production settings
    config.debug = False
    config.api.debug = False
    config.api.reload = False
    config.api.cors_origins = ["https://yourdomain.com"]  # Configure for production
    config.logging.level = "WARNING"
    config.logging.file_path = "logs/smartgrowth.log"

elif config.environment.lower() == "staging":
    # Staging settings
    config.debug = False
    config.api.debug = False
    config.api.reload = False
    config.logging.level = "INFO"
    config.logging.file_path = "logs/smartgrowth_staging.log"

else:
    # Development settings (default)
    config.debug = True
    config.api.debug = True
    config.api.reload = True
    config.logging.level = "DEBUG"

def get_config() -> SmartGrowthConfig:
    """Get the global configuration"""
    return config

def load_config(env_file: Optional[str] = None) -> SmartGrowthConfig:
    """Load configuration from environment file"""
    if env_file:
        return SmartGrowthConfig(_env_file=env_file)
    return SmartGrowthConfig()

# Configuration validation
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check database path
    db_path = config.get_database_path()
    if not os.path.exists(os.path.dirname(db_path)):
        errors.append(f"Database directory does not exist: {os.path.dirname(db_path)}")
    
    # Check model path
    model_path = config.get_model_path()
    if not os.path.exists(os.path.dirname(model_path)):
        errors.append(f"Model directory does not exist: {os.path.dirname(model_path)}")
    
    # Check port availability (basic check)
    if config.api.port < 1024 or config.api.port > 65535:
        errors.append(f"Invalid API port: {config.api.port}")
    
    if config.dashboard.port < 1024 or config.dashboard.port > 65535:
        errors.append(f"Invalid dashboard port: {config.dashboard.port}")
    
    # Check logging configuration
    if config.logging.file_path:
        log_dir = os.path.dirname(config.logging.file_path)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create log directory {log_dir}: {e}")
    
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    return True

if __name__ == "__main__":
    # Configuration testing
    print("SmartGrowth AI Configuration")
    print("=" * 50)
    print(f"Environment: {config.environment}")
    print(f"Project: {config.project_name} v{config.version}")
    print(f"Debug: {config.debug}")
    print()
    
    print("Database Configuration:")
    print(f"  Path: {config.get_database_path()}")
    print(f"  URL: {config.database.database_url}")
    print()
    
    print("ML Model Configuration:")
    print(f"  Path: {config.get_model_path()}")
    print(f"  Threshold: {config.ml_model.default_threshold}")
    print()
    
    print("API Configuration:")
    print(f"  Host: {config.api.host}")
    print(f"  Port: {config.api.port}")
    print(f"  Debug: {config.api.debug}")
    print()
    
    print("Dashboard Configuration:")
    print(f"  Host: {config.dashboard.host}")
    print(f"  Port: {config.dashboard.port}")
    print(f"  API URL: {config.dashboard.api_base_url}")
    print()
    
    try:
        validate_config()
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
