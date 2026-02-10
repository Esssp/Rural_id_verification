"""
Unit tests for the EncryptionConfig system.
"""

import os
import tempfile
import pytest
from unittest.mock import patch

from rural_identity_verification.config.encryption import (
    EncryptionConfig, get_encryption_config, reset_encryption_config, generate_key_file
)


class TestEncryptionConfig:
    """Test cases for EncryptionConfig."""
    
    def test_default_encryption_config(self):
        """Test default encryption configuration values."""
        config = EncryptionConfig()
        
        assert config.salt_length == 32
        assert config.key_iterations == 100000
        assert config.algorithm == "AES-256-GCM"
        assert config.key_size == 32
        assert config.iv_size == 16
        
        # Keys should be auto-generated
        assert config.biometric_key is not None
        assert config.contact_info_key is not None
        assert config.session_key is not None
        
        # Keys should be correct size
        assert len(config.biometric_key) == 32
        assert len(config.contact_info_key) == 32
        assert len(config.session_key) == 32
    
    def test_keys_are_different(self):
        """Test that generated keys are different from each other."""
        config = EncryptionConfig()
        
        assert config.biometric_key != config.contact_info_key
        assert config.biometric_key != config.session_key
        assert config.contact_info_key != config.session_key
    
    @patch.dict(os.environ, {
        'BIOMETRIC_KEY': 'a' * 64,  # 32 bytes as hex
        'CONTACT_INFO_KEY': 'b' * 64,
        'SESSION_KEY': 'c' * 64
    })
    def test_keys_from_environment(self):
        """Test loading keys from environment variables."""
        config = EncryptionConfig()
        
        assert config.biometric_key == bytes.fromhex('a' * 64)
        assert config.contact_info_key == bytes.fromhex('b' * 64)
        assert config.session_key == bytes.fromhex('c' * 64)
    
    @patch.dict(os.environ, {
        'BIOMETRIC_KEY': 'invalid_hex'
    })
    def test_invalid_hex_key_raises_error(self):
        """Test that invalid hex key raises ValueError."""
        with pytest.raises(ValueError, match="Invalid hex key format"):
            EncryptionConfig()
    
    @patch.dict(os.environ, {
        'BIOMETRIC_KEY': 'a' * 32  # 16 bytes as hex (too short)
    })
    def test_invalid_key_size_raises_error(self):
        """Test that invalid key size raises ValueError."""
        with pytest.raises(ValueError, match="Invalid key size"):
            EncryptionConfig()
    
    def test_generate_salt(self):
        """Test salt generation."""
        config = EncryptionConfig()
        
        salt1 = config.generate_salt()
        salt2 = config.generate_salt()
        
        assert len(salt1) == 32
        assert len(salt2) == 32
        assert salt1 != salt2  # Should be different
    
    def test_generate_iv(self):
        """Test IV generation."""
        config = EncryptionConfig()
        
        iv1 = config.generate_iv()
        iv2 = config.generate_iv()
        
        assert len(iv1) == 16
        assert len(iv2) == 16
        assert iv1 != iv2  # Should be different
    
    def test_rotate_keys(self):
        """Test key rotation."""
        config = EncryptionConfig()
        
        # Store original keys
        original_biometric = config.biometric_key
        original_contact = config.contact_info_key
        original_session = config.session_key
        
        config.rotate_keys()
        
        # Keys should be different after rotation
        assert config.biometric_key != original_biometric
        assert config.contact_info_key != original_contact
        assert config.session_key != original_session
        
        # Keys should still be correct size
        assert len(config.biometric_key) == 32
        assert len(config.contact_info_key) == 32
        assert len(config.session_key) == 32
    
    def test_export_keys_hex(self):
        """Test exporting keys as hex strings."""
        config = EncryptionConfig()
        
        keys_hex = config.export_keys_hex()
        
        assert "BIOMETRIC_KEY" in keys_hex
        assert "CONTACT_INFO_KEY" in keys_hex
        assert "SESSION_KEY" in keys_hex
        
        # Verify hex format
        assert len(keys_hex["BIOMETRIC_KEY"]) == 64  # 32 bytes * 2 hex chars
        assert len(keys_hex["CONTACT_INFO_KEY"]) == 64
        assert len(keys_hex["SESSION_KEY"]) == 64
        
        # Verify they can be converted back to bytes
        assert bytes.fromhex(keys_hex["BIOMETRIC_KEY"]) == config.biometric_key
        assert bytes.fromhex(keys_hex["CONTACT_INFO_KEY"]) == config.contact_info_key
        assert bytes.fromhex(keys_hex["SESSION_KEY"]) == config.session_key
    
    def test_validate_keys_valid(self):
        """Test key validation with valid keys."""
        config = EncryptionConfig()
        
        assert config.validate_keys() is True
    
    def test_validate_keys_invalid_none(self):
        """Test key validation with None keys."""
        config = EncryptionConfig()
        config.biometric_key = None
        
        assert config.validate_keys() is False
    
    def test_validate_keys_invalid_size(self):
        """Test key validation with wrong size keys."""
        config = EncryptionConfig()
        config.biometric_key = b"too_short"
        
        assert config.validate_keys() is False


class TestGlobalEncryptionConfig:
    """Test cases for global encryption config management."""
    
    def test_get_encryption_config_singleton(self):
        """Test that get_encryption_config returns the same instance."""
        reset_encryption_config()  # Ensure clean state
        
        config1 = get_encryption_config()
        config2 = get_encryption_config()
        
        assert config1 is config2
    
    def test_reset_encryption_config(self):
        """Test that reset_encryption_config clears the global instance."""
        config1 = get_encryption_config()
        reset_encryption_config()
        config2 = get_encryption_config()
        
        assert config1 is not config2


class TestGenerateKeyFile:
    """Test cases for key file generation."""
    
    def test_generate_key_file(self):
        """Test generating a key file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            filepath = f.name
        
        try:
            generate_key_file(filepath)
            
            # Verify file was created and contains keys
            with open(filepath, 'r') as f:
                content = f.read()
            
            assert "BIOMETRIC_KEY=" in content
            assert "CONTACT_INFO_KEY=" in content
            assert "SESSION_KEY=" in content
            assert "# Rural Identity Verification System" in content
            
            # Verify keys are valid hex
            lines = content.split('\n')
            for line in lines:
                if '=' in line and not line.startswith('#'):
                    key_name, key_value = line.split('=', 1)
                    assert len(key_value) == 64  # 32 bytes as hex
                    bytes.fromhex(key_value)  # Should not raise exception
        
        finally:
            os.unlink(filepath)
    
    def test_generate_key_file_creates_valid_config(self):
        """Test that generated key file can be used to create valid config."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            filepath = f.name
        
        try:
            generate_key_file(filepath)
            
            # Load keys from file
            env_vars = {}
            with open(filepath, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
            
            # Use keys to create config
            with patch.dict(os.environ, env_vars):
                config = EncryptionConfig()
                assert config.validate_keys() is True
        
        finally:
            os.unlink(filepath)