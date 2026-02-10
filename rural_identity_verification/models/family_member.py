"""
Family member data model for the Rural Identity Verification System.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class Relationship(Enum):
    """Family relationship types."""
    SPOUSE = "SPOUSE"
    CHILD = "CHILD"
    PARENT = "PARENT"
    GUARDIAN = "GUARDIAN"
    OTHER = "OTHER"


class AuthorizationLevel(Enum):
    """Authorization levels for family members."""
    FULL_ACCESS = "FULL_ACCESS"
    LIMITED_ACCESS = "LIMITED_ACCESS"


@dataclass
class FamilyMember:
    """
    Family member authorization model.
    
    Represents a family member who is authorized to access benefits
    on behalf of a primary user.
    """
    family_member_id: UUID = field(default_factory=uuid4)
    primary_user_id: UUID = field(default=None)
    relationship: Relationship = field(default=None)
    authorization_level: AuthorizationLevel = AuthorizationLevel.LIMITED_ACCESS
    consent_given: bool = False
    consent_date: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate family member data after initialization."""
        if self.primary_user_id is None:
            raise ValueError("Primary user ID is required")
        
        if self.relationship is None:
            raise ValueError("Relationship type is required")
        
        if self.consent_given and self.consent_date is None:
            self.consent_date = datetime.utcnow()
    
    def grant_consent(self) -> None:
        """Grant consent for family member authorization."""
        self.consent_given = True
        self.consent_date = datetime.utcnow()
    
    def revoke_consent(self) -> None:
        """Revoke consent for family member authorization."""
        self.consent_given = False
        self.consent_date = None
    
    def activate(self) -> None:
        """Activate the family member authorization."""
        if not self.consent_given:
            raise ValueError("Cannot activate family member without consent")
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate the family member authorization."""
        self.is_active = False
    
    def has_valid_authorization(self) -> bool:
        """Check if the family member has valid authorization."""
        return self.consent_given and self.is_active