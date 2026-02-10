"""
Unit tests for the Settings configuration system.
"""

import os
import pytest
from unittest.mock import patch

from rural_identity_verification.config.settings import (
    Settings, DatabaseConfig, AuthenticationConfig, 
    PerformanceConfig, SecurityConfig, get_settings, reset_settings
)


class TestDatabaseConfig:
    """Test cases for DatabaseConfig."""
    
    def test_default_database_config(self):
        """Test default database configuration values."""
        config = DatabaseConfig()
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "rural_identity_verification"
        assert config.username == "postgres"
        assert config.password == ""
    
    @patch.dict(os.environ, {
        'DB_HOST': 'test-host',
        'DB_PORT': '3306',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_pass'
    })
    def test_database_config_from_env(self):
        """Test database configuration from environment variables."""
        config = DatabaseConfig.from_env()
        
        assert config.host == "test-host"
        assert config.port == 3306
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_pass"


class TestAuthenticationConfig:
    """Test cases for AuthenticationConfig."""
    
    def test_default_authentication_config(self):
        """Test default authentication configuration values."""
        config = AuthenticationConfig()
        
        assert config.session_timeout_minutes == 15
        assert config.max_failed_attempts == 3
        assert config.otp_expiry_minutes == 5
        assert config.otp_delivery_timeout_seconds == 30
        assert config.biometric_accuracy_threshold == 0.95
    
    @patch.dict(os.environ, {
        'SESSION_TIMEOUT_MINUTES': '20',
        'MAX_FAILED_ATTEMPTS': '5',
        'OTP_EXPIRY_MINUTES': '10',
        'OTP_DELIVERY_TIMEOUT': '60',
        'BIOMETRIC_ACCURACY_THRESHOLD': '0.98'
    })
    def test_authentication_config_from_env(self):
        """Test authentication configuration from environment variables."""
        config = AuthenticationConfig.from_env()
        
        assert config.session_timeout_minutes == 20
        assert config.max_failed_attempts == 5
        assert config.otp_expiry_minutes == 10
        assert config.otp_delivery_timeout_seconds == 60
        assert config.biometric_accuracy_threshold == 0.98


class TestPerformanceConfig:
    """Test cases for PerformanceConfig."""
    
    def test_default_performance_config(self):
        """Test default performance configuration values."""
        config = PerformanceConfig()
        
        assert config.max_response_time_seconds == 10
        assert config.high_load_response_time_seconds == 30
        assert config.uptime_target_percentage == 99.5
        assert config.max_sync_retries == 5
    
    @patch.dict(os.environ, {
        'MAX_RESPONSE_TIME': '15',
        'HIGH_LOAD_RESPONSE_TIME': '45',
        'UPTIME_TARGET': '99.9',
        'MAX_SYNC_RETRIES': '10'
    })
    def test_performance_config_from_env(self):
        """Test performance configuration from environment variables."""
        config = PerformanceConfig.from_env()
        
        assert config.max_response_time_seconds == 15
        assert config.high_load_response_time_seconds == 45
        assert config.uptime_target_percentage == 99.9
        assert config.max_sync_retries == 10


class TestSecurityConfig:
    """Test cases for SecurityConfig."""
    
    def test_default_security_config(self):
        """Test default security configuration values."""
        config = SecurityConfig()
        
        assert config.encryption_algorithm == "AES-256"
        assert config.tls_version == "TLS1.3"
        assert config.data_retention_days == 365
        assert config.suspicious_activity_lockout_minutes == 30
    
    @patch.dict(os.environ, {
        'ENCRYPTION_ALGORITHM': 'AES-128',
        'TLS_VERSION': 'TLS1.2',
        'DATA_RETENTION_DAYS': '730',
        'LOCKOUT_MINUTES': '60'
    })
    def test_security_config_from_env(self):
        """Test security configuration from environment variables."""
        config = SecurityConfig.from_env()
        
        assert config.encryption_algorithm == "AES-128"
        assert config.tls_version == "TLS1.2"
        assert config.data_retention_days == 730
        assert config.suspicious_activity_lockout_minutes == 60


class TestSettings:
    """Test cases for Settings main configuration class."""
    
    def test_default_settings(self):
        """Test default settings configuration."""
        settings = Settings()
        
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.database is not None
        assert settings.authentication is not None
        assert settings.performance is not None
        assert settings.security is not None
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production',
        'DEBUG': 'true',
        'LOG_LEVEL': 'DEBUG'
    })
    def test_settings_from_env(self):
        """Test settings configuration from environment variables."""
        settings = Settings.from_env()
        
        assert settings.environment == "production"
        assert settings.debug is True
        assert settings.log_level == "DEBUG"
    
    def test_is_production(self):
        """Test production environment detection."""
        settings = Settings(environment="production")
        assert settings.is_production() is True
        
        settings = Settings(environment="development")
        assert settings.is_production() is False
        
        settings = Settings(environment="PRODUCTION")  # Case insensitive
        assert settings.is_production() is True
    
    def test_is_development(self):
        """Test development environment detection."""
        settings = Settings(environment="development")
        assert settings.is_development() is True
        
        settings = Settings(environment="production")
        assert settings.is_development() is False
        
        settings = Settings(environment="DEVELOPMENT")  # Case insensitive
        assert settings.is_development() is True
    
    def test_sub_configs_auto_initialization(self):
        """Test that sub-configurations are auto-initialized."""
        settings = Settings()
        
        assert isinstance(settings.database, DatabaseConfig)
        assert isinstance(settings.authentication, AuthenticationConfig)
        assert isinstance(settings.performance, PerformanceConfig)
        assert isinstance(settings.security, SecurityConfig)
    
    def test_custom_sub_configs(self):
        """Test providing custom sub-configurations."""
        custom_db = DatabaseConfig(host="custom-host")
        custom_auth = AuthenticationConfig(session_timeout_minutes=30)
        
        settings = Settings(
            database=custom_db,
            authentication=custom_auth
        )
        
        assert settings.database.host == "custom-host"
        assert settings.authentication.session_timeout_minutes == 30
        # Other configs should still be auto-initialized
        assert isinstance(settings.performance, PerformanceConfig)
        assert isinstance(settings.security, SecurityConfig)


class TestGlobalSettings:
    """Test cases for global settings management."""
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        reset_settings()  # Ensure clean state
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_reset_settings(self):
        """Test that reset_settings clears the global instance."""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()
        
        assert settings1 is not settings2
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'test'})
    def test_get_settings_from_env(self):
        """Test that get_settings uses environment variables."""
        reset_settings()
        
        settings = get_settings()
        
        assert settings.environment == "test"