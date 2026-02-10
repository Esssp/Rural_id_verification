"""
Unit tests for the FamilyMember model.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from rural_identity_verification.models.family_member import FamilyMember, Relationship, AuthorizationLevel


class TestFamilyMember:
    """Test cases for FamilyMember model."""
    
    def test_family_member_creation_with_valid_data(self):
        """Test creating a family member with valid data."""
        primary_user_id = uuid4()
        family_member = FamilyMember(
            primary_user_id=primary_user_id,
            relationship=Relationship.SPOUSE,
            authorization_level=AuthorizationLevel.FULL_ACCESS
        )
        
        assert family_member.primary_user_id == primary_user_id
        assert family_member.relationship == Relationship.SPOUSE
        assert family_member.authorization_level == AuthorizationLevel.FULL_ACCESS
        assert family_member.consent_given is False
        assert family_member.consent_date is None
        assert family_member.is_active is True
        assert family_member.created_at is not None
    
    def test_family_member_creation_without_primary_user_id(self):
        """Test that family member creation fails without primary user ID."""
        with pytest.raises(ValueError, match="Primary user ID is required"):
            FamilyMember(relationship=Relationship.SPOUSE)
    
    def test_family_member_creation_without_relationship(self):
        """Test that family member creation fails without relationship."""
        with pytest.raises(ValueError, match="Relationship type is required"):
            FamilyMember(primary_user_id=uuid4())
    
    def test_default_authorization_level(self):
        """Test that default authorization level is LIMITED_ACCESS."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.CHILD
        )
        
        assert family_member.authorization_level == AuthorizationLevel.LIMITED_ACCESS
    
    def test_grant_consent(self):
        """Test granting consent for family member authorization."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.SPOUSE
        )
        
        assert family_member.consent_given is False
        assert family_member.consent_date is None
        
        family_member.grant_consent()
        
        assert family_member.consent_given is True
        assert family_member.consent_date is not None
        assert isinstance(family_member.consent_date, datetime)
    
    def test_revoke_consent(self):
        """Test revoking consent for family member authorization."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.SPOUSE
        )
        
        family_member.grant_consent()
        assert family_member.consent_given is True
        
        family_member.revoke_consent()
        
        assert family_member.consent_given is False
        assert family_member.consent_date is None
    
    def test_activate_with_consent(self):
        """Test activating family member with valid consent."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.SPOUSE
        )
        
        family_member.grant_consent()
        family_member.activate()
        
        assert family_member.is_active is True
    
    def test_activate_without_consent(self):
        """Test that activation fails without consent."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.SPOUSE
        )
        
        with pytest.raises(ValueError, match="Cannot activate family member without consent"):
            family_member.activate()
    
    def test_deactivate(self):
        """Test deactivating family member."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.SPOUSE
        )
        
        family_member.grant_consent()
        family_member.activate()
        assert family_member.is_active is True
        
        family_member.deactivate()
        
        assert family_member.is_active is False
    
    def test_has_valid_authorization_with_consent_and_active(self):
        """Test valid authorization when consent is given and member is active."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.SPOUSE
        )
        
        family_member.grant_consent()
        family_member.activate()
        
        assert family_member.has_valid_authorization() is True
    
    def test_has_valid_authorization_without_consent(self):
        """Test invalid authorization when consent is not given."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.SPOUSE
        )
        
        assert family_member.has_valid_authorization() is False
    
    def test_has_valid_authorization_when_inactive(self):
        """Test invalid authorization when member is inactive."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.SPOUSE
        )
        
        family_member.grant_consent()
        family_member.deactivate()
        
        assert family_member.has_valid_authorization() is False
    
    def test_consent_date_auto_set_on_creation(self):
        """Test that consent date is auto-set when consent is given during creation."""
        family_member = FamilyMember(
            primary_user_id=uuid4(),
            relationship=Relationship.SPOUSE,
            consent_given=True
        )
        
        assert family_member.consent_given is True
        assert family_member.consent_date is not None
        assert isinstance(family_member.consent_date, datetime)
    
    def test_all_relationship_types(self):
        """Test that all relationship types can be used."""
        primary_user_id = uuid4()
        
        for relationship in Relationship:
            family_member = FamilyMember(
                primary_user_id=primary_user_id,
                relationship=relationship
            )
            assert family_member.relationship == relationship
    
    def test_all_authorization_levels(self):
        """Test that all authorization levels can be used."""
        primary_user_id = uuid4()
        
        for auth_level in AuthorizationLevel:
            family_member = FamilyMember(
                primary_user_id=primary_user_id,
                relationship=Relationship.SPOUSE,
                authorization_level=auth_level
            )
            assert family_member.authorization_level == auth_level