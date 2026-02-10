"""
Unit tests for biometric data models and encryption utilities.
"""

import pytest
import secrets
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import patch

from rural_identity_verification.models.biometric_data import (
    BiometricTemplate,
    EncryptedBiometricData,
    BiometricDataManager,
    get_biometric_manager,
    reset_biometric_manager
)
from rural_identity_verification.config.encryption import reset_encryption_config


class TestBiometricTemplate:
    """Test cases for BiometricTemplate."""
    
    def test_create_valid_template(self):
        """Test creating a valid biometric template."""
        user_id = uuid4()
        feature_vector = secrets.token_bytes(256)
        
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=feature_vector,
            quality_score=0.95,
            extraction_algorithm="test_algorithm"
        )
        
        assert template.user_id == user_id
        assert template.feature_vector == feature_vector
        assert template.quality_score == 0.95
        assert template.extraction_algorithm == "test_algorithm"
        assert template.template_type == "facial_recognition"
        assert isinstance(template.template_id, UUID)
        assert isinstance(template.created_at, datetime)
    
    def test_template_requires_user_id(self):
        """Test that template creation requires user ID."""
        with pytest.raises(ValueError, match="User ID is required"):
            BiometricTemplate(
                user_id=None,
                feature_vector=secrets.token_bytes(256)
            )
    
    def test_template_requires_feature_vector(self):
        """Test that template creation requires feature vector."""
        with pytest.raises(ValueError, match="Feature vector is required"):
            BiometricTemplate(
                user_id=uuid4(),
                feature_vector=None
            )
        
        with pytest.raises(ValueError, match="Feature vector is required"):
            BiometricTemplate(
                user_id=uuid4(),
                feature_vector=b""
            )
    
    def test_quality_score_validation(self):
        """Test quality score validation."""
        user_id = uuid4()
        feature_vector = secrets.token_bytes(256)
        
        # Valid quality scores
        for score in [0.0, 0.5, 1.0]:
            template = BiometricTemplate(
                user_id=user_id,
                feature_vector=feature_vector,
                quality_score=score
            )
            assert template.quality_score == score
        
        # Invalid quality scores
        for score in [-0.1, 1.1, 2.0]:
            with pytest.raises(ValueError, match="Quality score must be between"):
                BiometricTemplate(
                    user_id=user_id,
                    feature_vector=feature_vector,
                    quality_score=score
                )
    
    def test_template_to_dict(self):
        """Test converting template to dictionary."""
        user_id = uuid4()
        feature_vector = secrets.token_bytes(256)
        metadata = {"test_key": "test_value"}
        
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=feature_vector,
            quality_score=0.85,
            metadata=metadata
        )
        
        template_dict = template.to_dict()
        
        assert template_dict["user_id"] == str(user_id)
        assert template_dict["quality_score"] == 0.85
        assert template_dict["metadata"] == metadata
        assert "feature_vector" in template_dict
        assert "created_at" in template_dict
    
    def test_template_from_dict(self):
        """Test creating template from dictionary."""
        user_id = uuid4()
        feature_vector = secrets.token_bytes(256)
        
        original_template = BiometricTemplate(
            user_id=user_id,
            feature_vector=feature_vector,
            quality_score=0.75
        )
        
        template_dict = original_template.to_dict()
        restored_template = BiometricTemplate.from_dict(template_dict)
        
        assert restored_template.user_id == original_template.user_id
        assert restored_template.feature_vector == original_template.feature_vector
        assert restored_template.quality_score == original_template.quality_score
        assert restored_template.template_type == original_template.template_type


class TestEncryptedBiometricData:
    """Test cases for EncryptedBiometricData."""
    
    def setup_method(self):
        """Reset encryption config before each test."""
        reset_encryption_config()
    
    def test_encrypt_template(self):
        """Test encrypting a biometric template."""
        user_id = uuid4()
        feature_vector = secrets.token_bytes(256)
        
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=feature_vector,
            quality_score=0.9
        )
        
        encrypted_data = EncryptedBiometricData.encrypt_template(template)
        
        assert encrypted_data.user_id == user_id
        assert encrypted_data.encrypted_payload is not None
        assert encrypted_data.initialization_vector is not None
        assert encrypted_data.authentication_tag is not None
        assert encrypted_data.salt is not None
        assert encrypted_data.encryption_algorithm == "AES-256-GCM"
        assert len(encrypted_data.initialization_vector) == 16
        assert len(encrypted_data.salt) == 32
    
    def test_decrypt_template(self):
        """Test decrypting an encrypted biometric template."""
        user_id = uuid4()
        feature_vector = secrets.token_bytes(256)
        
        original_template = BiometricTemplate(
            user_id=user_id,
            feature_vector=feature_vector,
            quality_score=0.88,
            extraction_algorithm="test_algo"
        )
        
        # Encrypt the template
        encrypted_data = EncryptedBiometricData.encrypt_template(original_template)
        
        # Decrypt the template
        decrypted_template = encrypted_data.decrypt_template()
        
        assert decrypted_template.user_id == original_template.user_id
        assert decrypted_template.feature_vector == original_template.feature_vector
        assert decrypted_template.quality_score == original_template.quality_score
        assert decrypted_template.extraction_algorithm == original_template.extraction_algorithm
        assert encrypted_data.last_accessed is not None
    
    def test_encryption_produces_different_results(self):
        """Test that encrypting the same template twice produces different results."""
        user_id = uuid4()
        feature_vector = secrets.token_bytes(256)
        
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=feature_vector,
            quality_score=0.9
        )
        
        encrypted1 = EncryptedBiometricData.encrypt_template(template)
        encrypted2 = EncryptedBiometricData.encrypt_template(template)
        
        # Different IVs and salts should produce different encrypted data
        assert encrypted1.encrypted_payload != encrypted2.encrypted_payload
        assert encrypted1.initialization_vector != encrypted2.initialization_vector
        assert encrypted1.salt != encrypted2.salt
    
    def test_verify_integrity_valid(self):
        """Test integrity verification with valid data."""
        user_id = uuid4()
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.9
        )
        
        encrypted_data = EncryptedBiometricData.encrypt_template(template)
        assert encrypted_data.verify_integrity() is True
    
    def test_verify_integrity_corrupted(self):
        """Test integrity verification with corrupted data."""
        user_id = uuid4()
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.9
        )
        
        encrypted_data = EncryptedBiometricData.encrypt_template(template)
        
        # Corrupt the encrypted payload
        corrupted_payload = bytearray(encrypted_data.encrypted_payload)
        corrupted_payload[0] = (corrupted_payload[0] + 1) % 256
        encrypted_data.encrypted_payload = bytes(corrupted_payload)
        
        assert encrypted_data.verify_integrity() is False
    
    def test_secure_delete(self):
        """Test secure deletion of encrypted data."""
        user_id = uuid4()
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.9
        )
        
        encrypted_data = EncryptedBiometricData.encrypt_template(template)
        
        # Store original values to verify they're cleared
        original_payload = encrypted_data.encrypted_payload
        original_iv = encrypted_data.initialization_vector
        original_tag = encrypted_data.authentication_tag
        original_salt = encrypted_data.salt
        
        encrypted_data.secure_delete()
        
        # All sensitive data should be cleared
        assert encrypted_data.encrypted_payload is None
        assert encrypted_data.initialization_vector is None
        assert encrypted_data.authentication_tag is None
        assert encrypted_data.salt is None
    
    def test_get_storage_size(self):
        """Test getting storage size of encrypted data."""
        user_id = uuid4()
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.9
        )
        
        encrypted_data = EncryptedBiometricData.encrypt_template(template)
        size = encrypted_data.get_storage_size()
        
        assert size > 0
        assert isinstance(size, int)
        
        # Size should be sum of all encrypted components
        expected_size = (
            len(encrypted_data.encrypted_payload) +
            len(encrypted_data.initialization_vector) +
            len(encrypted_data.authentication_tag) +
            len(encrypted_data.salt)
        )
        assert size == expected_size
    
    def test_is_expired(self):
        """Test expiration checking."""
        user_id = uuid4()
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.9
        )
        
        encrypted_data = EncryptedBiometricData.encrypt_template(template)
        
        # Should not be expired with default retention
        assert encrypted_data.is_expired() is False
        
        # Should be expired with very short retention
        assert encrypted_data.is_expired(retention_days=0) is True
        
        # Test with old creation date
        encrypted_data.created_at = datetime.utcnow() - timedelta(days=400)
        assert encrypted_data.is_expired(retention_days=365) is True


class TestBiometricDataManager:
    """Test cases for BiometricDataManager."""
    
    def setup_method(self):
        """Reset manager and encryption config before each test."""
        reset_biometric_manager()
        reset_encryption_config()
    
    def test_store_and_retrieve_template(self):
        """Test storing and retrieving a biometric template."""
        manager = BiometricDataManager()
        user_id = uuid4()
        
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.92
        )
        
        # Store the template
        encrypted_id = manager.store_template(template)
        assert isinstance(encrypted_id, UUID)
        
        # Retrieve the template
        retrieved_template = manager.retrieve_template(encrypted_id)
        assert retrieved_template is not None
        assert retrieved_template.user_id == template.user_id
        assert retrieved_template.feature_vector == template.feature_vector
        assert retrieved_template.quality_score == template.quality_score
    
    def test_retrieve_nonexistent_template(self):
        """Test retrieving a non-existent template."""
        manager = BiometricDataManager()
        
        result = manager.retrieve_template(uuid4())
        assert result is None
    
    def test_get_user_templates(self):
        """Test getting all templates for a user."""
        manager = BiometricDataManager()
        user_id = uuid4()
        
        # Store multiple templates for the same user
        templates = []
        for i in range(3):
            template = BiometricTemplate(
                user_id=user_id,
                feature_vector=secrets.token_bytes(256),
                quality_score=0.8 + i * 0.05
            )
            templates.append(template)
            manager.store_template(template)
        
        # Get user templates
        user_templates = manager.get_user_templates(user_id)
        assert len(user_templates) == 3
        
        # Verify all templates belong to the user
        for template in user_templates:
            assert template.user_id == user_id
    
    def test_delete_template(self):
        """Test deleting a biometric template."""
        manager = BiometricDataManager()
        user_id = uuid4()
        
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.9
        )
        
        encrypted_id = manager.store_template(template)
        
        # Verify template exists
        assert manager.retrieve_template(encrypted_id) is not None
        
        # Delete the template
        result = manager.delete_template(encrypted_id)
        assert result is True
        
        # Verify template is gone
        assert manager.retrieve_template(encrypted_id) is None
    
    def test_delete_nonexistent_template(self):
        """Test deleting a non-existent template."""
        manager = BiometricDataManager()
        
        result = manager.delete_template(uuid4())
        assert result is False
    
    def test_delete_user_templates(self):
        """Test deleting all templates for a user."""
        manager = BiometricDataManager()
        user_id = uuid4()
        
        # Store multiple templates
        template_ids = []
        for i in range(3):
            template = BiometricTemplate(
                user_id=user_id,
                feature_vector=secrets.token_bytes(256),
                quality_score=0.8 + i * 0.05
            )
            template_id = manager.store_template(template)
            template_ids.append(template_id)
        
        # Delete all user templates
        deleted_count = manager.delete_user_templates(user_id)
        assert deleted_count == 3
        
        # Verify all templates are gone
        for template_id in template_ids:
            assert manager.retrieve_template(template_id) is None
        
        # Verify user has no templates
        assert len(manager.get_user_templates(user_id)) == 0
    
    def test_cleanup_expired_templates(self):
        """Test cleaning up expired templates."""
        manager = BiometricDataManager()
        user_id = uuid4()
        
        # Store a template
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.9
        )
        encrypted_id = manager.store_template(template)
        
        # Make the template appear old
        encrypted_data = manager._storage[encrypted_id]
        encrypted_data.created_at = datetime.utcnow() - timedelta(days=400)
        
        # Cleanup with 365-day retention
        deleted_count = manager.cleanup_expired_templates(retention_days=365)
        assert deleted_count == 1
        
        # Verify template is gone
        assert manager.retrieve_template(encrypted_id) is None
    
    def test_verify_all_templates(self):
        """Test verifying integrity of all templates."""
        manager = BiometricDataManager()
        user_id = uuid4()
        
        # Store valid templates
        template_ids = []
        for i in range(2):
            template = BiometricTemplate(
                user_id=user_id,
                feature_vector=secrets.token_bytes(256),
                quality_score=0.8 + i * 0.1
            )
            template_id = manager.store_template(template)
            template_ids.append(template_id)
        
        # Verify all templates
        integrity_status = manager.verify_all_templates()
        
        assert len(integrity_status) == 2
        for template_id in template_ids:
            assert integrity_status[template_id] is True
    
    def test_get_storage_statistics(self):
        """Test getting storage statistics."""
        manager = BiometricDataManager()
        
        # Initially empty
        stats = manager.get_storage_statistics()
        assert stats["total_templates"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["users_with_templates"] == 0
        assert stats["average_template_size"] == 0
        
        # Add some templates
        user_ids = [uuid4(), uuid4()]
        for user_id in user_ids:
            template = BiometricTemplate(
                user_id=user_id,
                feature_vector=secrets.token_bytes(256),
                quality_score=0.9
            )
            manager.store_template(template)
        
        stats = manager.get_storage_statistics()
        assert stats["total_templates"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["users_with_templates"] == 2
        assert stats["average_template_size"] > 0


class TestGlobalBiometricManager:
    """Test cases for global biometric manager functions."""
    
    def test_get_biometric_manager_singleton(self):
        """Test that get_biometric_manager returns the same instance."""
        reset_biometric_manager()  # Ensure clean state
        
        manager1 = get_biometric_manager()
        manager2 = get_biometric_manager()
        
        assert manager1 is manager2
    
    def test_reset_biometric_manager(self):
        """Test that reset_biometric_manager clears the global instance."""
        manager1 = get_biometric_manager()
        reset_biometric_manager()
        manager2 = get_biometric_manager()
        
        assert manager1 is not manager2


class TestEncryptionIntegration:
    """Test cases for encryption integration."""
    
    def setup_method(self):
        """Reset encryption config before each test."""
        reset_encryption_config()
    
    def test_encryption_with_different_keys(self):
        """Test that different encryption keys produce different results."""
        user_id = uuid4()
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.9
        )
        
        # Encrypt with first key
        encrypted1 = EncryptedBiometricData.encrypt_template(template)
        
        # Reset config to get new keys
        reset_encryption_config()
        
        # Encrypt with second key
        encrypted2 = EncryptedBiometricData.encrypt_template(template)
        
        # Results should be different
        assert encrypted1.encrypted_payload != encrypted2.encrypted_payload
        assert encrypted1.salt != encrypted2.salt
    
    def test_decryption_fails_with_wrong_key(self):
        """Test that decryption fails when using wrong encryption key."""
        user_id = uuid4()
        template = BiometricTemplate(
            user_id=user_id,
            feature_vector=secrets.token_bytes(256),
            quality_score=0.9
        )
        
        # Encrypt with first key
        encrypted_data = EncryptedBiometricData.encrypt_template(template)
        
        # Reset config to get new keys
        reset_encryption_config()
        
        # Try to decrypt with different key - should fail
        with pytest.raises(ValueError, match="Failed to decrypt"):
            encrypted_data.decrypt_template()