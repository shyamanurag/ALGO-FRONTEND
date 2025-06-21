import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError # For decoding token in tests
from pydantic import ValidationError # For testing Pydantic model validation if needed

# Functions and classes to test
from backend.src.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_admin_user_from_settings,
    UserInDB, # For type checking
    TokenData # For type checking if we were to decode into it
)

# Mock AppSettings structure that security.py expects
class MockAppSettings:
    JWT_SECRET_KEY: str = "test_secret_key_for_jwt_very_secure"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_USERNAME: str = "testadmin"
    ADMIN_PASSWORD_PLAIN: Optional[str] = "testpassword"
    ADMIN_PASSWORD_HASH: Optional[str] = None # Will be set in some tests

    def __init__(self):
        # If ADMIN_PASSWORD_HASH is not set by a specific test,
        # and ADMIN_PASSWORD_PLAIN is, generate the hash for this instance.
        if not self.ADMIN_PASSWORD_HASH and self.ADMIN_PASSWORD_PLAIN:
            self.ADMIN_PASSWORD_HASH = get_password_hash(self.ADMIN_PASSWORD_PLAIN)

@patch('backend.src.core.security.settings', MockAppSettings())
class TestSecurityUtils(unittest.TestCase):

    def test_get_password_hash_and_verify(self):
        password = "testpassword123"
        hashed_password = get_password_hash(password)

        self.assertIsNotNone(hashed_password)
        self.assertNotEqual(password, hashed_password)

        self.assertTrue(verify_password(password, hashed_password))
        self.assertFalse(verify_password("wrongpassword", hashed_password))

    @patch('backend.src.core.security.datetime')
    def test_create_access_token(self, mock_datetime):
        # Mock datetime.now(timezone.utc) to return a fixed time
        fixed_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now

        mock_settings = MockAppSettings() # Get a fresh instance with current patched values if needed

        token_data = {"sub": "testuser@example.com", "role": "user"}
        token = create_access_token(token_data)

        self.assertIsNotNone(token)

        # Decode the token to verify claims
        decoded_payload = jwt.decode(
            token,
            mock_settings.JWT_SECRET_KEY,
            algorithms=[mock_settings.JWT_ALGORITHM]
        )

        self.assertEqual(decoded_payload["sub"], "testuser@example.com")
        self.assertEqual(decoded_payload["role"], "user")

        expected_exp = fixed_now + timedelta(minutes=mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        # JWT 'exp' is usually a Unix timestamp (integer)
        self.assertEqual(decoded_payload["exp"], int(expected_exp.timestamp()))
        self.assertEqual(decoded_payload["iat"], int(fixed_now.timestamp()))

    @patch('backend.src.core.security.datetime')
    def test_create_access_token_with_custom_expiry(self, mock_datetime):
        fixed_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now

        mock_settings = MockAppSettings()

        token_data = {"sub": "testuser_custom_exp@example.com"}
        custom_delta = timedelta(hours=1)
        token = create_access_token(token_data, expires_delta=custom_delta)

        decoded_payload = jwt.decode(
            token,
            mock_settings.JWT_SECRET_KEY,
            algorithms=[mock_settings.JWT_ALGORITHM]
        )

        expected_exp = fixed_now + custom_delta
        self.assertEqual(decoded_payload["exp"], int(expected_exp.timestamp()))

    def test_get_admin_user_from_settings_success(self):
        # Settings are patched globally for this class
        mock_settings_instance = MockAppSettings() # Ensure it has the hashed password

        with patch('backend.src.core.security.settings', mock_settings_instance):
            admin_user = get_admin_user_from_settings(mock_settings_instance.ADMIN_USERNAME)
            self.assertIsNotNone(admin_user)
            self.assertIsInstance(admin_user, UserInDB)
            self.assertEqual(admin_user.username, mock_settings_instance.ADMIN_USERNAME)
            self.assertTrue(verify_password(mock_settings_instance.ADMIN_PASSWORD_PLAIN, admin_user.hashed_password))
            self.assertEqual(admin_user.role, "admin")

    def test_get_admin_user_from_settings_user_not_found(self):
        with patch('backend.src.core.security.settings', MockAppSettings()):
            non_admin_user = get_admin_user_from_settings("notauser")
            self.assertIsNone(non_admin_user)

    def test_get_admin_user_from_settings_no_hash_or_plain(self):
        # Create a mock settings where admin password (plain or hash) is not set
        settings_no_pass = MockAppSettings()
        settings_no_pass.ADMIN_PASSWORD_PLAIN = None
        settings_no_pass.ADMIN_PASSWORD_HASH = None

        with patch('backend.src.core.security.settings', settings_no_pass):
            admin_user = get_admin_user_from_settings(settings_no_pass.ADMIN_USERNAME)
            self.assertIsNone(admin_user)

    def test_get_admin_user_from_settings_only_hash_provided(self):
        settings_only_hash = MockAppSettings()
        settings_only_hash.ADMIN_PASSWORD_PLAIN = None # Ensure plain is None
        # The hash is already set by MockAppSettings logic if plain was there,
        # or can be set directly for this test.
        # If MockAppSettings.__init__ generates hash, this test is similar to _success.
        # Let's ensure we test a scenario where only hash is "provided" (i.e. plain is None).

        # Re-initialize with plain as None to ensure hash is not from on-the-fly generation
        test_settings = MockAppSettings()
        test_settings.ADMIN_PASSWORD_HASH = get_password_hash("some_preset_password")
        test_settings.ADMIN_PASSWORD_PLAIN = None # Critical for this test case

        with patch('backend.src.core.security.settings', test_settings):
            admin_user = get_admin_user_from_settings(test_settings.ADMIN_USERNAME)
            self.assertIsNotNone(admin_user)
            self.assertEqual(admin_user.username, test_settings.ADMIN_USERNAME)
            self.assertEqual(admin_user.hashed_password, test_settings.ADMIN_PASSWORD_HASH)
            # We can't verify with plain password here as it's None in these settings for this test

if __name__ == '__main__':
    unittest.main()
