"""
Configuration management for the FastAPI ML Service.

This module handles loading and parsing YAML configuration files with
support for environment variable overrides and validation.
"""

import os
import yaml
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ModelsConfig(BaseModel):
    """Model-related configuration."""

    path: str = Field(default="../models", description="Path to models directory")
    preprocessor_path: str = Field(
        default="../models", description="Path to preprocessor artifacts"
    )
    cache_enabled: bool = Field(default=True, description="Enable model caching")


class JWTConfig(BaseModel):
    """JWT authentication configuration."""

    algorithm: str = Field(default="RS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=60, description="Token expiration in minutes")
    private_key: str = Field(..., description="RSA private key for signing tokens")
    public_key: str = Field(..., description="RSA public key for verifying tokens")


class APIConfig(BaseModel):
    """API server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=True, description="Enable auto-reload for development")
    rate_limit: str = Field(default="100/minute", description="Rate limiting configuration")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"], description="CORS allowed origins"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format"
    )


class HealthConfig(BaseModel):
    """Health check configuration."""

    include_model_accuracy: bool = Field(
        default=True, description="Include model accuracy in health check"
    )
    include_feature_info: bool = Field(
        default=True, description="Include feature info in health check"
    )


class RateLimitingRedisConfig(BaseModel):
    """Redis configuration for rate limiting."""

    url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")


class RateLimitingLimitsConfig(BaseModel):
    """Rate limit values for different endpoint types."""

    default: str = Field(default="100/minute", description="Default rate limit")
    predictions: str = Field(default="50/minute", description="Rate limit for ML predictions")
    health: str = Field(default="200/minute", description="Rate limit for health checks")
    auth: str = Field(default="20/minute", description="Rate limit for auth operations")


class RateLimitingConfig(BaseModel):
    """Rate limiting configuration."""

    storage_backend: str = Field(
        default="memory", description="Storage backend: 'memory' or 'redis'"
    )
    redis: RateLimitingRedisConfig = Field(default_factory=RateLimitingRedisConfig)
    limits: RateLimitingLimitsConfig = Field(default_factory=RateLimitingLimitsConfig)


class Config(BaseModel):
    """Complete application configuration."""

    environment: str = Field(default="development", description="Environment name")
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    jwt: JWTConfig
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    health: HealthConfig = Field(default_factory=HealthConfig)
    rate_limiting: RateLimitingConfig = Field(default_factory=RateLimitingConfig)


class ConfigManager:
    """Handles configuration loading and management."""

    def __init__(self, config_file: str = "config.yaml"):
        """Initialize configuration manager with config file path."""
        self.config_file = config_file
        self._config: Config = None

    def load_config(self) -> Config:
        """
        Load configuration from YAML file with environment variable overrides.

        Returns:
            Config: Loaded and validated configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            Exception: If config is invalid
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"Configuration file '{self.config_file}' not found. "
                f"Copy 'config.example.yaml' to '{self.config_file}' and update it."
            )

        try:
            # Load YAML configuration
            with open(self.config_file, "r") as f:
                config_data = yaml.safe_load(f)

            # Apply environment variable overrides
            config_data = self._apply_env_overrides(config_data)

            # Validate and create config object
            self._config = Config(**config_data)

            print(f"✅ Configuration loaded from {self.config_file}")
            print(f"📝 Environment: {self._config.environment}")

            return self._config

        except Exception as e:
            print(f"❌ Failed to load configuration: {str(e)}")
            raise

    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # Environment variable mapping
        env_mappings = {
            "ML_SERVICE_HOST": ["api", "host"],
            "ML_SERVICE_PORT": ["api", "port"],
            "ML_SERVICE_ENVIRONMENT": ["environment"],
            "ML_MODELS_PATH": ["models", "path"],
            "JWT_PRIVATE_KEY": ["jwt", "private_key"],
            "JWT_PUBLIC_KEY": ["jwt", "public_key"],
            "JWT_EXPIRE_MINUTES": ["jwt", "access_token_expire_minutes"],
            "RATE_LIMITING_BACKEND": ["rate_limiting", "storage_backend"],
            "REDIS_URL": ["rate_limiting", "redis", "url"],
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Navigate to the nested config location
                current = config_data
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                # Set the value (with type conversion for specific fields)
                final_key = config_path[-1]
                if final_key == "port" or final_key == "access_token_expire_minutes":
                    current[final_key] = int(env_value)
                elif final_key == "reload":
                    current[final_key] = env_value.lower() in ("true", "1", "yes")
                else:
                    current[final_key] = env_value

        return config_data

    @property
    def config(self) -> Config:
        """Get the loaded configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config


# Global configuration manager instance
config_manager = ConfigManager()
