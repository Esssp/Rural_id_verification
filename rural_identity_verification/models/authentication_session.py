"""
Authentication session data model for the Rural Identity Verification System.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4


class AuthenticationMethod(Enum):
    """Authentication method types."""
    FACE_ID = "FACE_ID"
    PIN = "PIN"
    OTP = "OTP"
    FAMILY_PROXY = "FAMILY_PROXY"


class SessionStatus(Enum):
    """Authentication session status."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


@dataclass
class GeoLocation:
    """Geographic location data."""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None


@dataclass
class AuthenticationAttempt:
    """Individual authentication attempt within a session."""
    attempt_id: UUID = field(default_factory=uuid4)
    method: AuthenticationMethod = field(default=None)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = False
    failure_reason: Optional[str] = None
    
    def __post_init__(self):
        """Validate authentication attempt data."""
        if self.method is None:
            raise ValueError("Authentication method is required")


@dataclass
class AuthenticationSession:
    """
    Authentication session model.
    
    Represents a single attempt to verify identity and access benefits,
    tracking all authentication attempts and session metadata.
    """
    session_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=None)
    device_id: str = field(default="")
    location: Optional[GeoLocation] = None
    authentication_method: Optional[AuthenticationMethod] = None
    attempts: List[AuthenticationAttempt] = field(default_factory=list)
    status: SessionStatus = SessionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default=None)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize session with default expiration time."""
        if self.user_id is None:
            raise ValueError("User ID is required for authentication session")
        
        if not self.device_id:
            raise ValueError("Device ID is required for authentication session")
        
        if self.expires_at is None:
            # Default session expires in 15 minutes
            self.expires_at = self.created_at + timedelta(minutes=15)
    
    def add_attempt(self, method: AuthenticationMethod, success: bool = False, 
                   failure_reason: Optional[str] = None) -> AuthenticationAttempt:
        """Add an authentication attempt to the session."""
        attempt = AuthenticationAttempt(
            method=method,
            success=success,
            failure_reason=failure_reason
        )
        self.attempts.append(attempt)
        
        # Update session authentication method if not set
        if self.authentication_method is None:
            self.authentication_method = method
        
        return attempt
    
    def get_failed_attempts_count(self, method: Optional[AuthenticationMethod] = None) -> int:
        """Get the count of failed attempts, optionally filtered by method."""
        failed_attempts = [a for a in self.attempts if not a.success]
        
        if method is not None:
            failed_attempts = [a for a in failed_attempts if a.method == method]
        
        return len(failed_attempts)
    
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def complete_session(self, success: bool) -> None:
        """Complete the authentication session."""
        if self.is_expired():
            self.status = SessionStatus.EXPIRED
        else:
            self.status = SessionStatus.SUCCESS if success else SessionStatus.FAILED
        
        self.completed_at = datetime.utcnow()
    
    def should_trigger_fallback(self) -> bool:
        """Check if fallback authentication should be triggered."""
        # Trigger fallback after 3 failed face recognition attempts
        face_failures = self.get_failed_attempts_count(AuthenticationMethod.FACE_ID)
        return face_failures >= 3
    
    def extend_session(self, minutes: int = 15) -> None:
        """Extend the session expiration time."""
        if not self.is_expired():
            self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)