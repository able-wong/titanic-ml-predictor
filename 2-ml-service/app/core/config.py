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
    access_token_expire_minutes: int = Field(
        default=60, description="Token expiration in minutes"
    )
    private_key: str = Field(..., description="RSA private key for signing tokens")
    public_key: str = Field(..., description="RSA public key for verifying tokens")


class APIConfig(BaseModel):
    """API server configuration."""

    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=True, description="Enable auto-reload for development")
    rate_limit: str = Field(
        default="100/minute", description="Rate limiting configuration"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"], description="CORS allowed origins"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
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

    url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )


class RateLimitingLimitsConfig(BaseModel):
    """Rate limit values for different endpoint types."""

    default: str = Field(default="100/minute", description="Default rate limit")
    predictions: str = Field(
        default="50/minute", description="Rate limit for ML predictions"
    )
    health: str = Field(
        default="200/minute", description="Rate limit for health checks"
    )
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
        Load configuration with the following priority:
        1. Environment variables (highest priority)
        2. config.yaml file (if exists)
        3. Default configuration (fallback)

        This approach works for local dev, CI/CD, and production deployments.

        Returns:
            Config: Loaded and validated configuration

        Raises:
            Exception: If config is invalid
        """
        config_data = None
        config_source = None
        
        # Start with defaults
        config_data = self._get_default_config()
        config_source = "defaults"
        
        # Override with config file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    file_config = yaml.safe_load(f)
                    # Deep merge file config into defaults
                    config_data = self._deep_merge(config_data, file_config)
                    config_source = f"{self.config_file}"
            except Exception as e:
                print(f"⚠️  Warning: Could not load {self.config_file}: {e}")
                # Continue with defaults
        
        try:
            # Apply environment variable overrides (highest priority)
            config_data = self._apply_env_overrides(config_data)
            
            # Check if we have minimal required config
            if not self._has_required_config(config_data):
                # For local development, provide helpful message
                if not os.getenv("JWT_PRIVATE_KEY") and not os.path.exists(self.config_file):
                    print(f"💡 Tip: For local development, copy 'config.example.yaml' to '{self.config_file}'")
            
            # Validate and create config object
            self._config = Config(**config_data)

            print(f"✅ Configuration loaded from {config_source} + environment overrides")
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

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _has_required_config(self, config_data: Dict[str, Any]) -> bool:
        """Check if we have the minimal required configuration."""
        # Check for JWT keys (required for authentication)
        jwt_config = config_data.get("jwt", {})
        has_keys = bool(jwt_config.get("private_key") and jwt_config.get("public_key"))
        
        # In production/testing, we should have real keys from env vars
        # In local dev, config.yaml should provide them
        return has_keys

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for CI/testing mode."""
        return {
            "environment": "testing",
            "models": {
                "path": "../models",
                "preprocessor_path": "../models", 
                "cache_enabled": True
            },
            "jwt": {
                "algorithm": "RS256",
                "access_token_expire_minutes": 60,
                # Test keys (NOT for production)
                "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCul2RlJhUd1srP
SabhKjQCdMmusBn8i3jDPLBYUh1/rupJzrtA2bKSm37Ja/SMfrmB2ov3RMMO8TCC
kuqfSDWOFewzNSLzvn82x1Ajv2ynhmUesH052jeLqVQzXZb4ymA00uWHYXWM5nLL
qwdmV7FDov2dFYgBaAJI+FTZKV4eO+y7Q8KdZ7qiQaJ9JwcSmcJ8jPl9p1Le0Rpk
ajkniIHsFyvY4iZS7Ps8HlKi/TzFRWSj6TooGnFjLHM22Ty9vXevXadqHfqGRUJB
OteoEiCpcqg8bw9AhUaMUOzRW+AV7RO6QUKTnfSG88TwIOdQlJxwredNZ6HuonhF
iER8ggB1AgMBAAECgf9poRr/A7LC7omx3/s0odP9Cuar06SCzi39LE5JvscaIHSf
MwgD72NMASpH2jn9FUwm65Kbmy/K0KuSoxVj+i6UDTlG1a33QGdUn3z6cpFULCzG
qXbyursbf2DKn0FLpv3cqPcOIpAtaivO0irs3eZED3Y5//4X72kjvMw2b2R4NBdx
CieR9BSWhUUVt6FXa5TgaXfXoGRWelF9PxEeRBeEdBSB/USkrrRnd3wHnWoVdP7y
ybLDsuq+MYnIm/FGL+/i3eXqM0ZypJmaVZLqqze26NhW9tiJ+5gryyw7b1T/4xhS
qkFHapBRTCqnN7RWiFF67Ic0zYW51G82TGME+ssCgYEA4/QZlb7oN3rw2HmHQAiS
NxmHjoFZfI15v5EZP0wMonG4ccdPoOfaL0IGidb/TjqVXUsrzMswKY9ABDOlahXb
HRxY0gjDq+D8L6oFicoj+JspkA9C6z2LvbpGJL0UZOqExF1UehjosqmZ4JQPvugv
+5afvIeRBaJZLXiDuApvnecCgYEAxBKInCCfv4qCi7ssrTIfcnwkcV4L+NUFaHvt
ND+hSW1j59cZeJytRWGe7e2VczQgOgq25CduZh7BL4sAJb6++iSaQ4c0nQm8T6hK
TuoNdzQnfn67L7QMcuN0cLCtJutY5Y1BA0+0kE5a73BYyIO35vMVVjsWkP+cHUdC
4BaPS0MCgYEAqrnbn6fHzCWr1LXQckj5GYNpX3XJS9u535wQyLNwkwmRFsYsAVsk
slhFBV+c/z4pOCJgv5U+kSHU1FDKBtYvsXHVpBkkU8rBlgFE/JoEruGnE1oayIzj
6Elm14U1jQ+IOHmeF4QoZAdaVDUQRe8oYMnDATSXjRy2pbOpE2HdjukCgYEAsrFx
b1kMPjSt5Usg3Hfh0STy0Z80qgL6es72z7dt9s2LT6/pttKT17ewcIcmvWe0NzGs
nSKSqt88kWfNKpk81BynuwNuH/DPfomRr3n/67PMiqxVTJR7A/noFQvvwpia3Bpw
NeReW2YN2ko5oATrhb/kokIXvu42CTj46eGllqECgYEAv93k52SPeqUsFJENrrWh
KSo0FnKK5slYVG6deHMoPt9xRSLFTlullKplm24BKkMiz3Ez2AqE9yVNYBRH5imz
DbZ4L8H9IqVMQq+I7UpjS1AmvUf3OMsOozr41Dh8j1GuukNWWSylLaY+GSqLBW6N
s+ctrW2CrMxvmFf3EX9x2jc=
-----END PRIVATE KEY-----""",
                "public_key": """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArpdkZSYVHdbKz0mm4So0
AnTJrrAZ/It4wzywWFIdf67qSc67QNmykpt+yWv0jH65gdqL90TDDvEwgpLqn0g1
jhXsMzUi875/NsdQI79sp4ZlHrB9Odo3i6lUM12W+MpgNNLlh2F1jOZyy6sHZlex
Q6L9nRWIAWgCSPhU2SleHjvsu0PCnWe6okGifScHEpnCfIz5fadS3tEaZGo5J4iB
7Bcr2OImUuz7PB5Sov08xUVko+k6KBpxYyxzNtk8vb13r12nah36hkVCQTrXqBIg
qXKoPG8PQIVGjFDs0VvgFe0TukFCk530hvPE8CDnUJSccK3nTWeh7qJ4RYhEfIIA
dQIDAQAB
-----END PUBLIC KEY-----"""
            },
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
                "reload": False,  # Disable reload in testing
                "rate_limit": "100/minute",
                "cors_origins": ["http://localhost:3000"]
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "health": {
                "include_model_accuracy": True,
                "include_feature_info": True
            },
            "rate_limiting": {
                "storage_backend": "memory",  # Always use memory for testing
                "redis": {
                    "url": "redis://localhost:6379/0"
                },
                "limits": {
                    "default": "1000/minute",  # Higher limits for testing
                    "predictions": "500/minute",
                    "health": "2000/minute", 
                    "auth": "200/minute"
                }
            }
        }

    @property
    def config(self) -> Config:
        """Get the loaded configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config


# Global configuration manager instance
config_manager = ConfigManager()
