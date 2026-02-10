"""
User data model for the Rural Identity Verification System.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .family_member import FamilyMember
    from .biometric_data import EncryptedBiometricData


class UserStatus(Enum):
    """User account status enumeration."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"


@dataclass
class PersonalInfo:
    """Personal information for a user."""
    first_name: str
    last_name: str
    date_of_birth: datetime
    government_id: str


@dataclass
class ContactInfo:
    """Contact information for a user (encrypted fields)."""
    phone_number: str  # Will be encrypted
    alternate_contact: Optional[str] = None  # Will be encrypted


@dataclass
class AuthenticationMethods:
    """Available authentication methods for a user."""
    face_recognition: bool = True
    pin_enabled: bool = False
    otp_enabled: bool = False


@dataclass
class User:
    """
    Core user model for the Rural Identity Verification System.
    
    Represents an authorized user who can access government benefits
    through the verification system.
    """
    user_id: UUID = field(default_factory=uuid4)
    personal_info: PersonalInfo = field(default=None)
    biometric_data_ids: List[UUID] = field(default_factory=list)  # References to encrypted biometric data
    contact_info: Optional[ContactInfo] = None
    authentication_methods: AuthenticationMethods = field(default_factory=AuthenticationMethods)
    family_members: List['FamilyMember'] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_authenticated: Optional[datetime] = None
    status: UserStatus = UserStatus.ACTIVE
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if self.personal_info is None:
            raise ValueError("Personal info is required for user creation")
        
        if not self.personal_info.first_name or not self.personal_info.last_name:
            raise ValueError("First name and last name are required")
        
        if not self.personal_info.government_id:
            raise ValueError("Government ID is required")
    
    def is_active(self) -> bool:
        """Check if the user account is active."""
        return self.status == UserStatus.ACTIVE
    
    def update_last_authenticated(self) -> None:
        """Update the last authenticated timestamp."""
        self.last_authenticated = datetime.utcnow()
    
    def add_family_member(self, family_member: 'FamilyMember') -> None:
        """Add a family member to the user's authorized list."""
        if family_member not in self.family_members:
            self.family_members.append(family_member)
    
    def remove_family_member(self, family_member_id: UUID) -> bool:
        """Remove a family member from the user's authorized list."""
        for i, member in enumerate(self.family_members):
            if member.family_member_id == family_member_id:
                del self.family_members[i]
                return True
        return False
    
    def add_biometric_data(self, biometric_data_id: UUID) -> None:
        """Add a reference to encrypted biometric data."""
        if biometric_data_id not in self.biometric_data_ids:
            self.biometric_data_ids.append(biometric_data_id)
    
    def remove_biometric_data(self, biometric_data_id: UUID) -> bool:
        """Remove a reference to encrypted biometric data."""
        if biometric_data_id in self.biometric_data_ids:
            self.biometric_data_ids.remove(biometric_data_id)
            return True
        return False
    
    def has_biometric_data(self) -> bool:
        """Check if the user has any biometric data registered."""
        return len(self.biometric_data_ids) > 0