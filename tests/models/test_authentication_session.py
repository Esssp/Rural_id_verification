"""
Unit tests for the AuthenticationSession model.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from rural_identity_verification.models.authentication_session import (
    AuthenticationSession, AuthenticationMethod, SessionStatus, 
    GeoLocation, AuthenticationAttempt
)


class TestGeoLocation:
    """Test cases for GeoLocation dataclass."""
    
    def test_geo_location_creation(self):
        """Test creating GeoLocation with valid data."""
        location = GeoLocation(
            latitude=40.7128,
            longitude=-74.0060,
            accuracy=10.0
        )
        
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.accuracy == 10.0
    
    def test_geo_location_without_accuracy(self):
        """Test creating GeoLocation without accuracy."""
        location = GeoLocation(
            latitude=40.7128,
            longitude=-74.0060
        )
        
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.accuracy is None


class TestAuthenticationAttempt:
    """Test cases for AuthenticationAttempt model."""
    
    def test_authentication_attempt_creation(self):
        """Test creating AuthenticationAttempt with valid data."""
        attempt = AuthenticationAttempt(
            method=AuthenticationMethod.FACE_ID,
            success=True
        )
        
        assert attempt.method == AuthenticationMethod.FACE_ID
        assert attempt.success is True
        assert attempt.failure_reason is None
        assert attempt.timestamp is not None
        assert attempt.attempt_id is not None
    
    def test_authentication_attempt_with_failure(self):
        """Test creating failed AuthenticationAttempt."""
        attempt = AuthenticationAttempt(
            method=AuthenticationMethod.PIN,
            success=False,
            failure_reason="Invalid PIN"
        )
        
        assert attempt.method == AuthenticationMethod.PIN
        assert attempt.success is False
        assert attempt.failure_reason == "Invalid PIN"
    
    def test_authentication_attempt_without_method(self):
        """Test that attempt creation fails without method."""
        with pytest.raises(ValueError, match="Authentication method is required"):
            AuthenticationAttempt()


class TestAuthenticationSession:
    """Test cases for AuthenticationSession model."""
    
    def test_session_creation_with_valid_data(self, sample_user, sample_geo_location):
        """Test creating authentication session with valid data."""
        session = AuthenticationSession(
            user_id=sample_user.user_id,
            device_id="test-device-123",
            location=sample_geo_location
        )
        
        assert session.user_id == sample_user.user_id
        assert session.device_id == "test-device-123"
        assert session.location == sample_geo_location
        assert session.status == SessionStatus.PENDING
        assert session.attempts == []
        assert session.created_at is not None
        assert session.expires_at is not None
        assert session.completed_at is None
    
    def test_session_creation_without_user_id(self):
        """Test that session creation fails without user ID."""
        with pytest.raises(ValueError, match="User ID is required"):
            AuthenticationSession(device_id="test-device-123")
    
    def test_session_creation_without_device_id(self, sample_user):
        """Test that session creation fails without device ID."""
        with pytest.raises(ValueError, match="Device ID is required"):
            AuthenticationSession(user_id=sample_user.user_id)
    
    def test_default_expiration_time(self, sample_auth_session):
        """Test that default expiration is 15 minutes from creation."""
        expected_expiry = sample_auth_session.created_at + timedelta(minutes=15)
        
        # Allow for small time differences due to execution time
        time_diff = abs((sample_auth_session.expires_at - expected_expiry).total_seconds())
        assert time_diff < 1  # Less than 1 second difference
    
    def test_add_attempt(self, sample_auth_session):
        """Test adding authentication attempt to session."""
        attempt = sample_auth_session.add_attempt(
            method=AuthenticationMethod.FACE_ID,
            success=True
        )
        
        assert len(sample_auth_session.attempts) == 1
        assert sample_auth_session.attempts[0] == attempt
        assert sample_auth_session.authentication_method == AuthenticationMethod.FACE_ID
    
    def test_add_failed_attempt(self, sample_auth_session):
        """Test adding failed authentication attempt."""
        attempt = sample_auth_session.add_attempt(
            method=AuthenticationMethod.PIN,
            success=False,
            failure_reason="Invalid PIN"
        )
        
        assert len(sample_auth_session.attempts) == 1
        assert attempt.success is False
        assert attempt.failure_reason == "Invalid PIN"
    
    def test_get_failed_attempts_count(self, sample_auth_session):
        """Test counting failed attempts."""
        # Add successful attempt
        sample_auth_session.add_attempt(AuthenticationMethod.FACE_ID, success=True)
        
        # Add failed attempts
        sample_auth_session.add_attempt(AuthenticationMethod.FACE_ID, success=False)
        sample_auth_session.add_attempt(AuthenticationMethod.PIN, success=False)
        
        assert sample_auth_session.get_failed_attempts_count() == 2
        assert sample_auth_session.get_failed_attempts_count(AuthenticationMethod.FACE_ID) == 1
        assert sample_auth_session.get_failed_attempts_count(AuthenticationMethod.PIN) == 1
    
    def test_is_expired_false(self, sample_auth_session):
        """Test that new session is not expired."""
        assert sample_auth_session.is_expired() is False
    
    def test_is_expired_true(self, sample_auth_session):
        """Test that session is expired after expiry time."""
        # Set expiry time to past
        sample_auth_session.expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        assert sample_auth_session.is_expired() is True
    
    def test_complete_session_success(self, sample_auth_session):
        """Test completing session successfully."""
        sample_auth_session.complete_session(success=True)
        
        assert sample_auth_session.status == SessionStatus.SUCCESS
        assert sample_auth_session.completed_at is not None
    
    def test_complete_session_failure(self, sample_auth_session):
        """Test completing session with failure."""
        sample_auth_session.complete_session(success=False)
        
        assert sample_auth_session.status == SessionStatus.FAILED
        assert sample_auth_session.completed_at is not None
    
    def test_complete_expired_session(self, sample_auth_session):
        """Test completing an expired session."""
        # Set expiry time to past
        sample_auth_session.expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        sample_auth_session.complete_session(success=True)
        
        assert sample_auth_session.status == SessionStatus.EXPIRED
        assert sample_auth_session.completed_at is not None
    
    def test_should_trigger_fallback_false(self, sample_auth_session):
        """Test that fallback is not triggered with fewer than 3 failures."""
        sample_auth_session.add_attempt(AuthenticationMethod.FACE_ID, success=False)
        sample_auth_session.add_attempt(AuthenticationMethod.FACE_ID, success=False)
        
        assert sample_auth_session.should_trigger_fallback() is False
    
    def test_should_trigger_fallback_true(self, sample_auth_session):
        """Test that fallback is triggered after 3 face recognition failures."""
        sample_auth_session.add_attempt(AuthenticationMethod.FACE_ID, success=False)
        sample_auth_session.add_attempt(AuthenticationMethod.FACE_ID, success=False)
        sample_auth_session.add_attempt(AuthenticationMethod.FACE_ID, success=False)
        
        assert sample_auth_session.should_trigger_fallback() is True
    
    def test_should_trigger_fallback_mixed_methods(self, sample_auth_session):
        """Test that fallback only considers face recognition failures."""
        sample_auth_session.add_attempt(AuthenticationMethod.FACE_ID, success=False)
        sample_auth_session.add_attempt(AuthenticationMethod.PIN, success=False)
        sample_auth_session.add_attempt(AuthenticationMethod.FACE_ID, success=False)
        
        assert sample_auth_session.should_trigger_fallback() is False
    
    def test_extend_session(self, sample_auth_session):
        """Test extending session expiration time."""
        original_expiry = sample_auth_session.expires_at
        
        sample_auth_session.extend_session(minutes=30)
        
        # New expiry should be approximately 30 minutes from now
        expected_expiry = datetime.utcnow() + timedelta(minutes=30)
        time_diff = abs((sample_auth_session.expires_at - expected_expiry).total_seconds())
        assert time_diff < 1  # Less than 1 second difference
        
        # Should be later than original expiry
        assert sample_auth_session.expires_at > original_expiry
    
    def test_extend_expired_session(self, sample_auth_session):
        """Test that expired session cannot be extended."""
        # Set expiry time to past
        sample_auth_session.expires_at = datetime.utcnow() - timedelta(minutes=1)
        original_expiry = sample_auth_session.expires_at
        
        sample_auth_session.extend_session(minutes=30)
        
        # Expiry should not change for expired session
        assert sample_auth_session.expires_at == original_expiry