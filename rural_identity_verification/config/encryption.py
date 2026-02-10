"""
Encryption configuration and key management.
"""

import os
import secrets
from dataclasses import dataclass
from typing import Optional


@dataclass
class EncryptionConfig:
    """
    Encryption configuration for the Rural Identity Verification System.
    
    Manages encryption keys and cryptographic settings for securing
    biometric data and sensitive information.
    """
    # AES-256 requires 32-byte keys
    biometric_key: bytes = None
    contact_info_key: bytes = None
    session_key: bytes = None
    
    # Key derivation settings
    salt_length: int = 32
    key_iterations: int = 100000
    
    # Encryption settings
    algorithm: str = "AES-256-GCM"
    key_size: int = 32  # 256 bits
    iv_size: int = 16   # 128 bits for GCM
    
    def __post_init__(self):
        """Initialize encryption keys if not provided."""
        if self.biometric_key is None:
            self.biometric_key = self._get_or_generate_key("BIOMETRIC_KEY")
        
        if self.contact_info_key is None:
            self.contact_info_key = self._get_or_generate_key("CONTACT_INFO_KEY")
        
        if self.session_key is None:
            self.session_key = self._get_or_generate_key("SESSION_KEY")
    
    def _get_or_generate_key(self, env_var: str) -> bytes:
        """Get encryption key from environment or generate a new one."""
        key_hex = os.getenv(env_var)
        
        if key_hex:
            try:
                key = bytes.fromhex(key_hex)
                if len(key) == self.key_size:
                    return key
                else:
                    raise ValueError(f"Invalid key size for {env_var}")
            except ValueError:
                raise ValueError(f"Invalid hex key format for {env_var}")
        
        # Generate a new key if not found in environment
        return secrets.token_bytes(self.key_size)
    
    def generate_salt(self) -> bytes:
        """Generate a random salt for key derivation."""
        return secrets.token_bytes(self.salt_length)
    
    def generate_iv(self) -> bytes:
        """Generate a random initialization vector."""
        return secrets.token_bytes(self.iv_size)
    
    def rotate_keys(self) -> None:
        """Rotate all encryption keys (generate new ones)."""
        self.biometric_key = secrets.token_bytes(self.key_size)
        self.contact_info_key = secrets.token_bytes(self.key_size)
        self.session_key = secrets.token_bytes(self.key_size)
    
    def export_keys_hex(self) -> dict:
        """Export keys as hex strings for environment configuration."""
        return {
            "BIOMETRIC_KEY": self.biometric_key.hex(),
            "CONTACT_INFO_KEY": self.contact_info_key.hex(),
            "SESSION_KEY": self.session_key.hex()
        }
    
    def validate_keys(self) -> bool:
        """Validate that all keys are properly configured."""
        keys = [self.biometric_key, self.contact_info_key, self.session_key]
        
        for key in keys:
            if key is None or len(key) != self.key_size:
                return False
        
        return True


# Global encryption config instance
_encryption_config: Optional[EncryptionConfig] = None


def get_encryption_config() -> EncryptionConfig:
    """Get the global encryption configuration instance."""
    global _encryption_config
    if _encryption_config is None:
        _encryption_config = EncryptionConfig()
    return _encryption_config


def reset_encryption_config() -> None:
    """Reset the global encryption config instance (mainly for testing)."""
    global _encryption_config
    _encryption_config = None


def generate_key_file(filepath: str) -> None:
    """Generate a key file with new encryption keys."""
    config = EncryptionConfig()
    keys = config.export_keys_hex()
    
    with open(filepath, 'w') as f:
        f.write("# Rural Identity Verification System - Encryption Keys\n")
        f.write("# WARNING: Keep these keys secure and never commit to version control\n\n")
        
        for key_name, key_value in keys.items():
            f.write(f"{key_name}={key_value}\n")
    
    print(f"Encryption keys generated and saved to {filepath}")
    print("WARNING: Keep this file secure and add it to .gitignore")