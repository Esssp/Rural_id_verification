"""
Unit tests for the OfflineTransaction model.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from rural_identity_verification.models.offline_transaction import OfflineTransaction, SyncStatus


class TestOfflineTransaction:
    """Test cases for OfflineTransaction model."""
    
    def test_offline_transaction_creation_with_valid_data(self):
        """Test creating offline transaction with valid data."""
        session_id = uuid4()
        user_id = uuid4()
        device_id = "test-device-123"
        auth_data = b"encrypted_auth_data"
        
        transaction = OfflineTransaction(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            authentication_data=auth_data
        )
        
        assert transaction.session_id == session_id
        assert transaction.user_id == user_id
        assert transaction.device_id == device_id
        assert transaction.authentication_data == auth_data
        assert transaction.sync_status == SyncStatus.PENDING
        assert transaction.retry_count == 0
        assert transaction.last_sync_attempt is None
        assert transaction.timestamp is not None
        assert transaction.transaction_id is not None
    
    def test_offline_transaction_creation_without_session_id(self):
        """Test that transaction creation fails without session ID."""
        with pytest.raises(ValueError, match="Session ID is required"):
            OfflineTransaction(
                user_id=uuid4(),
                device_id="test-device-123"
            )
    
    def test_offline_transaction_creation_without_user_id(self):
        """Test that transaction creation fails without user ID."""
        with pytest.raises(ValueError, match="User ID is required"):
            OfflineTransaction(
                session_id=uuid4(),
                device_id="test-device-123"
            )
    
    def test_offline_transaction_creation_without_device_id(self):
        """Test that transaction creation fails without device ID."""
        with pytest.raises(ValueError, match="Device ID is required"):
            OfflineTransaction(
                session_id=uuid4(),
                user_id=uuid4()
            )
    
    def test_mark_sync_attempt(self, sample_offline_transaction):
        """Test marking a synchronization attempt."""
        assert sample_offline_transaction.retry_count == 0
        assert sample_offline_transaction.last_sync_attempt is None
        
        sample_offline_transaction.mark_sync_attempt()
        
        assert sample_offline_transaction.retry_count == 1
        assert sample_offline_transaction.last_sync_attempt is not None
        assert isinstance(sample_offline_transaction.last_sync_attempt, datetime)
    
    def test_mark_synced(self, sample_offline_transaction):
        """Test marking transaction as successfully synchronized."""
        sample_offline_transaction.mark_synced()
        
        assert sample_offline_transaction.sync_status == SyncStatus.SYNCED
        assert sample_offline_transaction.last_sync_attempt is not None
    
    def test_mark_sync_failed(self, sample_offline_transaction):
        """Test marking synchronization as failed."""
        sample_offline_transaction.mark_sync_failed()
        
        assert sample_offline_transaction.sync_status == SyncStatus.FAILED
        assert sample_offline_transaction.last_sync_attempt is not None
    
    def test_reset_sync_status(self, sample_offline_transaction):
        """Test resetting synchronization status."""
        # First mark as failed with some attempts
        sample_offline_transaction.mark_sync_attempt()
        sample_offline_transaction.mark_sync_failed()
        
        assert sample_offline_transaction.sync_status == SyncStatus.FAILED
        assert sample_offline_transaction.retry_count == 1
        
        sample_offline_transaction.reset_sync_status()
        
        assert sample_offline_transaction.sync_status == SyncStatus.PENDING
        assert sample_offline_transaction.retry_count == 0
        assert sample_offline_transaction.last_sync_attempt is None
    
    def test_should_retry_sync_within_limit(self, sample_offline_transaction):
        """Test that retry is allowed within retry limit."""
        sample_offline_transaction.mark_sync_failed()
        
        assert sample_offline_transaction.should_retry_sync(max_retries=5) is True
    
    def test_should_retry_sync_at_limit(self, sample_offline_transaction):
        """Test that retry is not allowed when at retry limit."""
        # Simulate 5 failed attempts
        for _ in range(5):
            sample_offline_transaction.mark_sync_attempt()
        sample_offline_transaction.mark_sync_failed()
        
        assert sample_offline_transaction.should_retry_sync(max_retries=5) is False
    
    def test_should_retry_sync_when_synced(self, sample_offline_transaction):
        """Test that retry is not allowed when already synced."""
        sample_offline_transaction.mark_synced()
        
        assert sample_offline_transaction.should_retry_sync() is False
    
    def test_should_retry_sync_when_pending(self, sample_offline_transaction):
        """Test that retry is not allowed when status is pending."""
        assert sample_offline_transaction.sync_status == SyncStatus.PENDING
        assert sample_offline_transaction.should_retry_sync() is False
    
    def test_is_pending_sync_true(self, sample_offline_transaction):
        """Test that new transaction is pending sync."""
        assert sample_offline_transaction.is_pending_sync() is True
    
    def test_is_pending_sync_false_when_synced(self, sample_offline_transaction):
        """Test that synced transaction is not pending."""
        sample_offline_transaction.mark_synced()
        
        assert sample_offline_transaction.is_pending_sync() is False
    
    def test_is_pending_sync_false_when_failed(self, sample_offline_transaction):
        """Test that failed transaction is not pending."""
        sample_offline_transaction.mark_sync_failed()
        
        assert sample_offline_transaction.is_pending_sync() is False
    
    def test_get_age_hours_new_transaction(self, sample_offline_transaction):
        """Test age calculation for new transaction."""
        age = sample_offline_transaction.get_age_hours()
        
        # Should be very close to 0 for new transaction
        assert age < 0.01  # Less than 36 seconds
    
    def test_get_age_hours_old_transaction(self, sample_offline_transaction):
        """Test age calculation for older transaction."""
        # Set timestamp to 2 hours ago
        sample_offline_transaction.timestamp = datetime.utcnow() - timedelta(hours=2)
        
        age = sample_offline_transaction.get_age_hours()
        
        # Should be approximately 2 hours
        assert 1.9 < age < 2.1  # Allow for small timing differences
    
    def test_multiple_sync_attempts(self, sample_offline_transaction):
        """Test multiple synchronization attempts."""
        # First attempt
        sample_offline_transaction.mark_sync_attempt()
        assert sample_offline_transaction.retry_count == 1
        
        # Second attempt
        sample_offline_transaction.mark_sync_attempt()
        assert sample_offline_transaction.retry_count == 2
        
        # Third attempt
        sample_offline_transaction.mark_sync_attempt()
        assert sample_offline_transaction.retry_count == 3
        
        # Mark as failed
        sample_offline_transaction.mark_sync_failed()
        assert sample_offline_transaction.sync_status == SyncStatus.FAILED
        assert sample_offline_transaction.retry_count == 3
    
    def test_sync_status_transitions(self, sample_offline_transaction):
        """Test valid sync status transitions."""
        # Start as PENDING
        assert sample_offline_transaction.sync_status == SyncStatus.PENDING
        
        # Can transition to FAILED
        sample_offline_transaction.mark_sync_failed()
        assert sample_offline_transaction.sync_status == SyncStatus.FAILED
        
        # Can reset to PENDING
        sample_offline_transaction.reset_sync_status()
        assert sample_offline_transaction.sync_status == SyncStatus.PENDING
        
        # Can transition to SYNCED
        sample_offline_transaction.mark_synced()
        assert sample_offline_transaction.sync_status == SyncStatus.SYNCED