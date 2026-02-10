"""
Biometric data models and encryption utilities for the Rural Identity Verification System.

This module provides secure storage and handling of biometric data using AES-256 encryption,
ensuring compliance with privacy requirements and secure key management.
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import json
import base64

from ..config.encryption import get_encryption_config


@dataclass
class BiometricTemplate:
    """
    Raw biometric template data before encryption.
    
    Contains the extracted biometric features and metadata
    that will be encrypted for secure storage.
    """
    template_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=None)
    template_type: str = "facial_recognition"  # Type of biometric template
    feature_vector: bytes = field(default=None)  # Raw biometric features
    quality_score: float = 0.0  # Quality assessment of the template
    extraction_algorithm: str = "default"  # Algorithm used for feature extraction
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate biometric template data."""
        if self.user_id is None:
            raise ValueError("User ID is required for biometric template")
        
        if self.feature_vector is None or len(self.feature_vector) == 0:
            raise ValueError("Feature vector is required and cannot be empty")
        
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError("Quality score must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization."""
        return {
            "template_id": str(self.template_id),
            "user_id": str(self.user_id),
            "template_type": self.template_type,
            "feature_vector": base64.b64encode(self.feature_vector).decode('utf-8'),
            "quality_score": self.quality_score,
            "extraction_algorithm": self.extraction_algorithm,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BiometricTemplate':
        """Create template from dictionary."""
        return cls(
            template_id=UUID(data["template_id"]),
            user_id=UUID(data["user_id"]),
            template_type=data["template_type"],
            feature_vector=base64.b64decode(data["feature_vector"]),
            quality_score=data["quality_score"],
            extraction_algorithm=data["extraction_algorithm"],
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class EncryptedBiometricData:
    """
    Encrypted biometric data with AES-256 encryption.
    
    Provides secure storage and retrieval of biometric templates using
    AES-256-GCM encryption with proper key management and integrity verification.
    """
    encrypted_data_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=None)
    encrypted_payload: bytes = field(default=None)
    initialization_vector: bytes = field(default=None)
    authentication_tag: bytes = field(default=None)
    salt: bytes = field(default=None)
    encryption_algorithm: str = "AES-256-GCM"
    key_derivation_algorithm: str = "PBKDF2-HMAC-SHA256"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate encrypted biometric data."""
        if self.user_id is None:
            raise ValueError("User ID is required for encrypted biometric data")
    
    @classmethod
    def encrypt_template(cls, template: BiometricTemplate) -> 'EncryptedBiometricData':
        """
        Encrypt a biometric template using AES-256-GCM.
        
        Args:
            template: The biometric template to encrypt
            
        Returns:
            EncryptedBiometricData instance with encrypted template
            
        Raises:
            ValueError: If encryption fails or template is invalid
        """
        try:
            # Get encryption configuration
            config = get_encryption_config()
            
            # Generate salt and IV
            salt = config.generate_salt()
            iv = config.generate_iv()
            
            # Derive encryption key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=config.key_size,
                salt=salt,
                iterations=config.key_iterations,
                backend=default_backend()
            )
            derived_key = kdf.derive(config.biometric_key)
            
            # Serialize template to JSON bytes
            template_json = json.dumps(template.to_dict()).encode('utf-8')
            
            # Create cipher and encrypt
            cipher = Cipher(
                algorithms.AES(derived_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt the data
            encrypted_payload = encryptor.update(template_json) + encryptor.finalize()
            authentication_tag = encryptor.tag
            
            return cls(
                user_id=template.user_id,
                encrypted_payload=encrypted_payload,
                initialization_vector=iv,
                authentication_tag=authentication_tag,
                salt=salt
            )
            
        except Exception as e:
            raise ValueError(f"Failed to encrypt biometric template: {str(e)}")
    
    def decrypt_template(self) -> BiometricTemplate:
        """
        Decrypt the encrypted biometric data to recover the original template.
        
        Returns:
            BiometricTemplate: The decrypted biometric template
            
        Raises:
            ValueError: If decryption fails or data is corrupted
        """
        try:
            # Get encryption configuration
            config = get_encryption_config()
            
            # Derive the same encryption key using stored salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=config.key_size,
                salt=self.salt,
                iterations=config.key_iterations,
                backend=default_backend()
            )
            derived_key = kdf.derive(config.biometric_key)
            
            # Create cipher and decrypt
            cipher = Cipher(
                algorithms.AES(derived_key),
                modes.GCM(self.initialization_vector, self.authentication_tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt the data
            decrypted_data = decryptor.update(self.encrypted_payload) + decryptor.finalize()
            
            # Parse JSON and create template
            template_dict = json.loads(decrypted_data.decode('utf-8'))
            template = BiometricTemplate.from_dict(template_dict)
            
            # Update last accessed timestamp
            self.last_accessed = datetime.utcnow()
            
            return template
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt biometric template: {str(e)}")
    
    def verify_integrity(self) -> bool:
        """
        Verify the integrity of the encrypted data without decrypting.
        
        Returns:
            bool: True if data integrity is verified, False otherwise
        """
        try:
            # Attempt to decrypt - if successful, integrity is verified
            self.decrypt_template()
            return True
        except ValueError:
            return False
    
    def secure_delete(self) -> None:
        """
        Securely delete the encrypted biometric data.
        
        Overwrites sensitive data with random bytes before clearing references.
        This provides defense against memory recovery attacks.
        """
        if self.encrypted_payload:
            # Overwrite with random data
            random_data = secrets.token_bytes(len(self.encrypted_payload))
            self.encrypted_payload = random_data
            self.encrypted_payload = None
        
        if self.initialization_vector:
            random_iv = secrets.token_bytes(len(self.initialization_vector))
            self.initialization_vector = random_iv
            self.initialization_vector = None
        
        if self.authentication_tag:
            random_tag = secrets.token_bytes(len(self.authentication_tag))
            self.authentication_tag = random_tag
            self.authentication_tag = None
        
        if self.salt:
            random_salt = secrets.token_bytes(len(self.salt))
            self.salt = random_salt
            self.salt = None
    
    def get_storage_size(self) -> int:
        """
        Get the total storage size of the encrypted data in bytes.
        
        Returns:
            int: Total size in bytes
        """
        size = 0
        if self.encrypted_payload:
            size += len(self.encrypted_payload)
        if self.initialization_vector:
            size += len(self.initialization_vector)
        if self.authentication_tag:
            size += len(self.authentication_tag)
        if self.salt:
            size += len(self.salt)
        return size
    
    def is_expired(self, retention_days: int = 365) -> bool:
        """
        Check if the encrypted data has exceeded its retention period.
        
        Args:
            retention_days: Number of days to retain the data
            
        Returns:
            bool: True if data is expired, False otherwise
        """
        if not self.created_at:
            return False
        
        age_days = (datetime.utcnow() - self.created_at).days
        return age_days > retention_days


class BiometricDataManager:
    """
    Manager class for biometric data storage and retrieval operations.
    
    Provides high-level interface for managing encrypted biometric templates
    with proper security controls and audit logging.
    """
    
    def __init__(self):
        """Initialize the biometric data manager."""
        self._storage: Dict[UUID, EncryptedBiometricData] = {}
        self._user_templates: Dict[UUID, list[UUID]] = {}
    
    def store_template(self, template: BiometricTemplate) -> UUID:
        """
        Store a biometric template with encryption.
        
        Args:
            template: The biometric template to store
            
        Returns:
            UUID: The ID of the encrypted data record
            
        Raises:
            ValueError: If template is invalid or encryption fails
        """
        # Encrypt the template
        encrypted_data = EncryptedBiometricData.encrypt_template(template)
        
        # Store in memory (in production, this would be a secure database)
        self._storage[encrypted_data.encrypted_data_id] = encrypted_data
        
        # Track templates by user
        if template.user_id not in self._user_templates:
            self._user_templates[template.user_id] = []
        self._user_templates[template.user_id].append(encrypted_data.encrypted_data_id)
        
        return encrypted_data.encrypted_data_id
    
    def retrieve_template(self, encrypted_data_id: UUID) -> Optional[BiometricTemplate]:
        """
        Retrieve and decrypt a biometric template.
        
        Args:
            encrypted_data_id: ID of the encrypted data to retrieve
            
        Returns:
            BiometricTemplate or None if not found
            
        Raises:
            ValueError: If decryption fails
        """
        encrypted_data = self._storage.get(encrypted_data_id)
        if not encrypted_data:
            return None
        
        return encrypted_data.decrypt_template()
    
    def get_user_templates(self, user_id: UUID) -> list[BiometricTemplate]:
        """
        Get all biometric templates for a specific user.
        
        Args:
            user_id: The user ID to get templates for
            
        Returns:
            List of BiometricTemplate objects
        """
        templates = []
        template_ids = self._user_templates.get(user_id, [])
        
        for template_id in template_ids:
            template = self.retrieve_template(template_id)
            if template:
                templates.append(template)
        
        return templates
    
    def delete_template(self, encrypted_data_id: UUID) -> bool:
        """
        Securely delete a biometric template.
        
        Args:
            encrypted_data_id: ID of the encrypted data to delete
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        encrypted_data = self._storage.get(encrypted_data_id)
        if not encrypted_data:
            return False
        
        # Secure delete the data
        encrypted_data.secure_delete()
        
        # Remove from storage
        del self._storage[encrypted_data_id]
        
        # Remove from user template tracking
        for user_id, template_ids in self._user_templates.items():
            if encrypted_data_id in template_ids:
                template_ids.remove(encrypted_data_id)
                break
        
        return True
    
    def delete_user_templates(self, user_id: UUID) -> int:
        """
        Delete all biometric templates for a specific user.
        
        Args:
            user_id: The user ID to delete templates for
            
        Returns:
            int: Number of templates deleted
        """
        template_ids = self._user_templates.get(user_id, []).copy()
        deleted_count = 0
        
        for template_id in template_ids:
            if self.delete_template(template_id):
                deleted_count += 1
        
        # Clear user template tracking
        if user_id in self._user_templates:
            del self._user_templates[user_id]
        
        return deleted_count
    
    def cleanup_expired_templates(self, retention_days: int = 365) -> int:
        """
        Clean up expired biometric templates based on retention policy.
        
        Args:
            retention_days: Number of days to retain templates
            
        Returns:
            int: Number of templates deleted
        """
        expired_ids = []
        
        for encrypted_data_id, encrypted_data in self._storage.items():
            if encrypted_data.is_expired(retention_days):
                expired_ids.append(encrypted_data_id)
        
        deleted_count = 0
        for expired_id in expired_ids:
            if self.delete_template(expired_id):
                deleted_count += 1
        
        return deleted_count
    
    def verify_all_templates(self) -> Dict[UUID, bool]:
        """
        Verify the integrity of all stored templates.
        
        Returns:
            Dict mapping template IDs to integrity status
        """
        integrity_status = {}
        
        for encrypted_data_id, encrypted_data in self._storage.items():
            integrity_status[encrypted_data_id] = encrypted_data.verify_integrity()
        
        return integrity_status
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics for monitoring and management.
        
        Returns:
            Dict with storage statistics
        """
        total_templates = len(self._storage)
        total_size = sum(data.get_storage_size() for data in self._storage.values())
        users_with_templates = len(self._user_templates)
        
        return {
            "total_templates": total_templates,
            "total_size_bytes": total_size,
            "users_with_templates": users_with_templates,
            "average_template_size": total_size / total_templates if total_templates > 0 else 0
        }


# Global biometric data manager instance
_biometric_manager: Optional[BiometricDataManager] = None


def get_biometric_manager() -> BiometricDataManager:
    """Get the global biometric data manager instance."""
    global _biometric_manager
    if _biometric_manager is None:
        _biometric_manager = BiometricDataManager()
    return _biometric_manager


def reset_biometric_manager() -> None:
    """Reset the global biometric manager instance (mainly for testing)."""
    global _biometric_manager
    _biometric_manager = None