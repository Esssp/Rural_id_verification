"""
Offline transaction data model for the Rural Identity Verification System.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class SyncStatus(Enum):
    """Synchronization status for offline transactions."""
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


@dataclass
class OfflineTransaction:
    """
    Offline transaction model.
    
    Represents authentication transactions that were completed while offline
    and need to be synchronized with cloud services when connectivity returns.
    """
    transaction_id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(default=None)
    user_id: UUID = field(default=None)
    device_id: str = field(default="")
    authentication_data: Optional[bytes] = None  # Encrypted authentication data
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sync_status: SyncStatus = SyncStatus.PENDING
    retry_count: int = 0
    last_sync_attempt: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate offline transaction data."""
        if self.session_id is None:
            raise ValueError("Session ID is required for offline transaction")
        
        if self.user_id is None:
            raise ValueError("User ID is required for offline transaction")
        
        if not self.device_id:
            raise ValueError("Device ID is required for offline transaction")
    
    def mark_sync_attempt(self) -> None:
        """Mark that a synchronization attempt was made."""
        self.last_sync_attempt = datetime.utcnow()
        self.retry_count += 1
    
    def mark_synced(self) -> None:
        """Mark the transaction as successfully synchronized."""
        self.sync_status = SyncStatus.SYNCED
        self.last_sync_attempt = datetime.utcnow()
    
    def mark_sync_failed(self) -> None:
        """Mark the synchronization as failed."""
        self.sync_status = SyncStatus.FAILED
        self.last_sync_attempt = datetime.utcnow()
    
    def reset_sync_status(self) -> None:
        """Reset the synchronization status to pending."""
        self.sync_status = SyncStatus.PENDING
        self.retry_count = 0
        self.last_sync_attempt = None
    
    def should_retry_sync(self, max_retries: int = 5) -> bool:
        """Check if synchronization should be retried."""
        return (self.sync_status == SyncStatus.FAILED and 
                self.retry_count < max_retries)
    
    def is_pending_sync(self) -> bool:
        """Check if the transaction is pending synchronization."""
        return self.sync_status == SyncStatus.PENDING
    
    def get_age_hours(self) -> float:
        """Get the age of the transaction in hours."""
        age_delta = datetime.utcnow() - self.timestamp
        return age_delta.total_seconds() / 3600