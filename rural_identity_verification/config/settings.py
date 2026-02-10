"""
System settings and configuration management.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str = "localhost"
    port: int = 5432
    database: str = "rural_identity_verification"
    username: str = "postgres"
    password: str = ""
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create database config from environment variables."""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "rural_identity_verification"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )


@dataclass
class AuthenticationConfig:
    """Authentication system configuration."""
    session_timeout_minutes: int = 15
    max_failed_attempts: int = 3
    otp_expiry_minutes: int = 5
    otp_delivery_timeout_seconds: int = 30
    biometric_accuracy_threshold: float = 0.95
    
    @classmethod
    def from_env(cls) -> 'AuthenticationConfig':
        """Create authentication config from environment variables."""
        return cls(
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "15")),
            max_failed_attempts=int(os.getenv("MAX_FAILED_ATTEMPTS", "3")),
            otp_expiry_minutes=int(os.getenv("OTP_EXPIRY_MINUTES", "5")),
            otp_delivery_timeout_seconds=int(os.getenv("OTP_DELIVERY_TIMEOUT", "30")),
            biometric_accuracy_threshold=float(os.getenv("BIOMETRIC_ACCURACY_THRESHOLD", "0.95"))
        )


@dataclass
class PerformanceConfig:
    """Performance and reliability configuration."""
    max_response_time_seconds: int = 10
    high_load_response_time_seconds: int = 30
    uptime_target_percentage: float = 99.5
    max_sync_retries: int = 5
    
    @classmethod
    def from_env(cls) -> 'PerformanceConfig':
        """Create performance config from environment variables."""
        return cls(
            max_response_time_seconds=int(os.getenv("MAX_RESPONSE_TIME", "10")),
            high_load_response_time_seconds=int(os.getenv("HIGH_LOAD_RESPONSE_TIME", "30")),
            uptime_target_percentage=float(os.getenv("UPTIME_TARGET", "99.5")),
            max_sync_retries=int(os.getenv("MAX_SYNC_RETRIES", "5"))
        )


@dataclass
class SecurityConfig:
    """Security and privacy configuration."""
    encryption_algorithm: str = "AES-256"
    tls_version: str = "TLS1.3"
    data_retention_days: int = 365
    suspicious_activity_lockout_minutes: int = 30
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Create security config from environment variables."""
        return cls(
            encryption_algorithm=os.getenv("ENCRYPTION_ALGORITHM", "AES-256"),
            tls_version=os.getenv("TLS_VERSION", "TLS1.3"),
            data_retention_days=int(os.getenv("DATA_RETENTION_DAYS", "365")),
            suspicious_activity_lockout_minutes=int(os.getenv("LOCKOUT_MINUTES", "30"))
        )


@dataclass
class Settings:
    """
    Main settings class for the Rural Identity Verification System.
    
    Aggregates all configuration sections and provides environment-based
    initialization.
    """
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    database: DatabaseConfig = None
    authentication: AuthenticationConfig = None
    performance: PerformanceConfig = None
    security: SecurityConfig = None
    
    def __post_init__(self):
        """Initialize sub-configurations if not provided."""
        if self.database is None:
            self.database = DatabaseConfig.from_env()
        if self.authentication is None:
            self.authentication = AuthenticationConfig.from_env()
        if self.performance is None:
            self.performance = PerformanceConfig.from_env()
        if self.security is None:
            self.security = SecurityConfig.from_env()
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """Create settings from environment variables."""
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (mainly for testing)."""
    global _settings
    _settings = None