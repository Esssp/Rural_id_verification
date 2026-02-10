"""
Configuration management for the Rural Identity Verification System.

This module handles encryption keys, system settings, and environment-specific
configuration for the verification system.
"""

from .settings import Settings, get_settings
from .encryption import EncryptionConfig, get_encryption_config

__all__ = [
    "Settings",
    "get_settings", 
    "EncryptionConfig",
    "get_encryption_config"
]