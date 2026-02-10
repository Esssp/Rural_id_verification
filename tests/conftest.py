"""
Pytest configuration and shared fixtures for the Rural Identity Verification System tests.
"""

import pytest
import secrets
from datetime import datetime, timedelta
from uuid import uuid4

from rural_identity_verification.models.user import User, PersonalInfo, ContactInfo, AuthenticationMethods
from rural_identity_verification.models.family_member import FamilyMember, Relationship, AuthorizationLevel
from rural_identity_verification.models.authentication_session import AuthenticationSession, GeoLocation
from rural_identity_verification.models.offline_transaction import OfflineTransaction
from rural_identity_verification.models.biometric_data import BiometricTemplate, EncryptedBiometricData, reset_biometric_manager
from rural_identity_verification.config.settings import Settings, reset_settings
from rural_identity_verification.config.encryption import EncryptionConfig, reset_encryption_config


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset global configuration before each test."""
    reset_settings()
    reset_encryption_config()
    reset_biometric_manager()
    yield
    reset_settings()
    reset_encryption_config()
    reset_biometric_manager()


@pytest.fixture
def sample_personal_info():
    """Create sample personal information for testing."""
    return PersonalInfo(
        first_name="John",
        last_name="Doe",
        date_of_birth=datetime(1980, 1, 15),
        government_id="ID123456789"
    )


@pytest.fixture
def sample_contact_info():
    """Create sample contact information for testing."""
    return ContactInfo(
        phone_number="+1234567890",
        alternate_contact="+0987654321"
    )


@pytest.fixture
def sample_auth_methods():
    """Create sample authentication methods for testing."""
    return AuthenticationMethods(
        face_recognition=True,
        pin_enabled=True,
        otp_enabled=True
    )


@pytest.fixture
def sample_biometric_template():
    """Create sample biometric template for testing."""
    return BiometricTemplate(
        user_id=uuid4(),
        feature_vector=secrets.token_bytes(256),
        quality_score=0.95,
        extraction_algorithm="test_algorithm"
    )


@pytest.fixture
def sample_encrypted_biometric_data(sample_biometric_template):
    """Create sample encrypted biometric data for testing."""
    return EncryptedBiometricData.encrypt_template(sample_biometric_template)


@pytest.fixture
def sample_user(sample_personal_info, sample_contact_info, sample_auth_methods):
    """Create a sample user for testing."""
    return User(
        personal_info=sample_personal_info,
        contact_info=sample_contact_info,
        authentication_methods=sample_auth_methods
    )


@pytest.fixture
def sample_family_member(sample_user):
    """Create a sample family member for testing."""
    family_member = FamilyMember(
        primary_user_id=sample_user.user_id,
        relationship=Relationship.SPOUSE,
        authorization_level=AuthorizationLevel.FULL_ACCESS
    )
    family_member.grant_consent()
    return family_member


@pytest.fixture
def sample_geo_location():
    """Create sample geographic location for testing."""
    return GeoLocation(
        latitude=40.7128,
        longitude=-74.0060,
        accuracy=10.0
    )


@pytest.fixture
def sample_auth_session(sample_user, sample_geo_location):
    """Create a sample authentication session for testing."""
    return AuthenticationSession(
        user_id=sample_user.user_id,
        device_id="test-device-123",
        location=sample_geo_location
    )


@pytest.fixture
def sample_offline_transaction(sample_auth_session, sample_user):
    """Create a sample offline transaction for testing."""
    return OfflineTransaction(
        session_id=sample_auth_session.session_id,
        user_id=sample_user.user_id,
        device_id="test-device-123",
        authentication_data=b"encrypted_auth_data"
    )


@pytest.fixture
def test_settings():
    """Create test settings configuration."""
    return Settings(
        environment="test",
        debug=True,
        log_level="DEBUG"
    )


@pytest.fixture
def test_encryption_config():
    """Create test encryption configuration."""
    return EncryptionConfig()


# Hypothesis strategies for property-based testing
from hypothesis import strategies as st

@pytest.fixture
def user_id_strategy():
    """Strategy for generating valid user IDs."""
    return st.uuids()


@pytest.fixture
def device_id_strategy():
    """Strategy for generating valid device IDs."""
    return st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))


@pytest.fixture
def phone_number_strategy():
    """Strategy for generating valid phone numbers."""
    return st.text(min_size=10, max_size=15, alphabet=st.characters(whitelist_categories=('Nd',))).map(
        lambda x: f"+{x}"
    )


@pytest.fixture
def government_id_strategy():
    """Strategy for generating valid government IDs."""
    return st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))


@pytest.fixture
def name_strategy():
    """Strategy for generating valid names."""
    return st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')))


@pytest.fixture
def datetime_strategy():
    """Strategy for generating valid datetime objects."""
    return st.datetimes(
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2100, 12, 31)
    )


@pytest.fixture
def feature_vector_strategy():
    """Strategy for generating valid biometric feature vectors."""
    return st.binary(min_size=64, max_size=1024)


@pytest.fixture
def quality_score_strategy():
    """Strategy for generating valid quality scores."""
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)