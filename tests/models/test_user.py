"""
Unit tests for the User model.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from rural_identity_verification.models.user import User, PersonalInfo, ContactInfo, AuthenticationMethods, UserStatus
from rural_identity_verification.models.family_member import FamilyMember, Relationship


class TestPersonalInfo:
    """Test cases for PersonalInfo dataclass."""
    
    def test_personal_info_creation(self):
        """Test creating PersonalInfo with valid data."""
        info = PersonalInfo(
            first_name="John",
            last_name="Doe", 
            date_of_birth=datetime(1980, 1, 15),
            government_id="ID123456789"
        )
        
        assert info.first_name == "John"
        assert info.last_name == "Doe"
        assert info.date_of_birth == datetime(1980, 1, 15)
        assert info.government_id == "ID123456789"


class TestContactInfo:
    """Test cases for ContactInfo dataclass."""
    
    def test_contact_info_creation(self):
        """Test creating ContactInfo with valid data."""
        info = ContactInfo(
            phone_number="+1234567890",
            alternate_contact="+0987654321"
        )
        
        assert info.phone_number == "+1234567890"
        assert info.alternate_contact == "+0987654321"
    
    def test_contact_info_optional_alternate(self):
        """Test creating ContactInfo without alternate contact."""
        info = ContactInfo(phone_number="+1234567890")
        
        assert info.phone_number == "+1234567890"
        assert info.alternate_contact is None


class TestAuthenticationMethods:
    """Test cases for AuthenticationMethods dataclass."""
    
    def test_default_authentication_methods(self):
        """Test default authentication methods configuration."""
        methods = AuthenticationMethods()
        
        assert methods.face_recognition is True
        assert methods.pin_enabled is False
        assert methods.otp_enabled is False
    
    def test_custom_authentication_methods(self):
        """Test custom authentication methods configuration."""
        methods = AuthenticationMethods(
            face_recognition=False,
            pin_enabled=True,
            otp_enabled=True
        )
        
        assert methods.face_recognition is False
        assert methods.pin_enabled is True
        assert methods.otp_enabled is True


class TestUser:
    """Test cases for User model."""
    
    def test_user_creation_with_valid_data(self, sample_personal_info):
        """Test creating a user with valid personal information."""
        user = User(personal_info=sample_personal_info)
        
        assert user.personal_info == sample_personal_info
        assert user.status == UserStatus.ACTIVE
        assert user.family_members == []
        assert user.last_authenticated is None
        assert user.created_at is not None
    
    def test_user_creation_without_personal_info(self):
        """Test that user creation fails without personal info."""
        with pytest.raises(ValueError, match="Personal info is required"):
            User()
    
    def test_user_creation_with_empty_names(self):
        """Test that user creation fails with empty names."""
        invalid_info = PersonalInfo(
            first_name="",
            last_name="Doe",
            date_of_birth=datetime(1980, 1, 15),
            government_id="ID123456789"
        )
        
        with pytest.raises(ValueError, match="First name and last name are required"):
            User(personal_info=invalid_info)
    
    def test_user_creation_without_government_id(self):
        """Test that user creation fails without government ID."""
        invalid_info = PersonalInfo(
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime(1980, 1, 15),
            government_id=""
        )
        
        with pytest.raises(ValueError, match="Government ID is required"):
            User(personal_info=invalid_info)
    
    def test_is_active(self, sample_user):
        """Test user active status check."""
        assert sample_user.is_active() is True
        
        sample_user.status = UserStatus.SUSPENDED
        assert sample_user.is_active() is False
        
        sample_user.status = UserStatus.INACTIVE
        assert sample_user.is_active() is False
    
    def test_update_last_authenticated(self, sample_user):
        """Test updating last authenticated timestamp."""
        assert sample_user.last_authenticated is None
        
        sample_user.update_last_authenticated()
        
        assert sample_user.last_authenticated is not None
        assert isinstance(sample_user.last_authenticated, datetime)
    
    def test_add_family_member(self, sample_user):
        """Test adding a family member to user."""
        family_member = FamilyMember(
            primary_user_id=sample_user.user_id,
            relationship=Relationship.SPOUSE
        )
        
        sample_user.add_family_member(family_member)
        
        assert len(sample_user.family_members) == 1
        assert sample_user.family_members[0] == family_member
    
    def test_add_duplicate_family_member(self, sample_user):
        """Test that duplicate family members are not added."""
        family_member = FamilyMember(
            primary_user_id=sample_user.user_id,
            relationship=Relationship.SPOUSE
        )
        
        sample_user.add_family_member(family_member)
        sample_user.add_family_member(family_member)  # Add same member again
        
        assert len(sample_user.family_members) == 1
    
    def test_remove_family_member(self, sample_user):
        """Test removing a family member from user."""
        family_member = FamilyMember(
            primary_user_id=sample_user.user_id,
            relationship=Relationship.SPOUSE
        )
        
        sample_user.add_family_member(family_member)
        assert len(sample_user.family_members) == 1
        
        result = sample_user.remove_family_member(family_member.family_member_id)
        
        assert result is True
        assert len(sample_user.family_members) == 0
    
    def test_remove_nonexistent_family_member(self, sample_user):
        """Test removing a family member that doesn't exist."""
        nonexistent_id = uuid4()
        
        result = sample_user.remove_family_member(nonexistent_id)
        
        assert result is False
        assert len(sample_user.family_members) == 0