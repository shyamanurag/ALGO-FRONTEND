import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

# Import settings directly for JWT key/algo/expiry.
# This module is part of 'core' and 'config' is also part of 'core' (or 'src'),
# so direct import should be fine and avoids passing settings to every function here.
from src.config import settings # Direct import of the settings instance

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    # Add other fields like scopes: Optional[List[str]] = []

class Token(BaseModel): # Model for the token response
    access_token: str
    token_type: str

class UserInDB(BaseModel): # Simplified representation for auth purposes
    username: str
    hashed_password: str
    role: str = "admin"
    disabled: bool = False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password using bcrypt."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)}) # Add issued_at time

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def get_admin_user_from_settings(username_to_check: str) -> Optional[UserInDB]:
    """
    Retrieves the admin user details from settings.
    In a real application, this would query a database.
    This version also handles on-the-fly hashing if ADMIN_PASSWORD_HASH is not set
    (for initial setup - NOT for production use beyond first hash generation).
    """
    # Uses the global `settings` instance imported from src.config
    if username_to_check == settings.ADMIN_USERNAME:
        current_admin_password_hash = settings.ADMIN_PASSWORD_HASH

        # On-the-fly hash generation if plain password is provided and hash is missing
        # This is a development/setup convenience.
        if not current_admin_password_hash and settings.ADMIN_PASSWORD_PLAIN:
            logger.warning(
                f"ADMIN_PASSWORD_HASH is not set in settings for user '{settings.ADMIN_USERNAME}'. "
                "Generating hash from ADMIN_PASSWORD_PLAIN. This is for initial setup only "
                "and ADMIN_PASSWORD_PLAIN should be removed from config/env afterwards."
            )
            current_admin_password_hash = get_password_hash(settings.ADMIN_PASSWORD_PLAIN)
            # For the purpose of this function call, we use the generated hash.
            # Note: This does NOT save it back to the settings file or .env. That's a manual step.
            # However, if the settings object is mutable and global, this might change it in memory for the app's lifetime.
            # For BaseSettings, fields are generally immutable after load unless explicitly made mutable.
            # A better pattern for one-time hash generation is a separate CLI script.

        if current_admin_password_hash:
            return UserInDB(
                username=settings.ADMIN_USERNAME,
                hashed_password=current_admin_password_hash, # Use the (potentially just generated) hash
                role="admin",
                disabled=False # Assuming admin is not disabled by default
            )
        else:
            logger.error(
                f"Cannot authenticate admin user '{settings.ADMIN_USERNAME}': "
                "ADMIN_PASSWORD_HASH is not set and ADMIN_PASSWORD_PLAIN is also not available. "
                "Please set ADMIN_PASSWORD_HASH in your environment/config."
            )
            return None
    return None

if __name__ == "__main__":
    # Example usage (requires settings to be loadable, e.g. .env file in place)
    # Setup basic logging for testing this module directly
    try:
        from src.core.logging_config import setup_logging
        setup_logging(log_level=settings.LOG_LEVEL if settings else "INFO")
    except ImportError:
        logging.basicConfig(level="INFO", format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        logging.warning("Could not import full logging setup for security.py direct execution.")

    logger_sec_test = logging.getLogger(__name__)

    logger_sec_test.info("--- Testing Security Utilities ---")

    # Test password hashing and verification
    if settings and settings.ADMIN_PASSWORD_PLAIN:
        plain_pass = settings.ADMIN_PASSWORD_PLAIN
        logger_sec_test.info(f"Plain password for testing: {plain_pass[:2]}********")
        hashed_pass = get_password_hash(plain_pass)
        logger_sec_test.info(f"Generated Hash: {hashed_pass[:10]}...")
        is_correct = verify_password(plain_pass, hashed_pass)
        logger_sec_test.info(f"Verification (plain vs generated_hash): {is_correct}")

        if settings.ADMIN_PASSWORD_HASH:
             is_correct_against_config_hash = verify_password(plain_pass, settings.ADMIN_PASSWORD_HASH)
             logger_sec_test.info(f"Verification (plain vs settings.ADMIN_PASSWORD_HASH): {is_correct_against_config_hash}")
        else:
            logger_sec_test.info("settings.ADMIN_PASSWORD_HASH is not set for direct comparison test.")

    else:
        logger_sec_test.warning("ADMIN_PASSWORD_PLAIN not in settings, skipping some hash tests.")
        # Test with a dummy password if plain one not in settings
        dummy_hashed = get_password_hash("testpassword")
        logger_sec_test.info(f"Verification (testpassword vs dummy_hash): {verify_password('testpassword', dummy_hashed)}")
        logger_sec_test.info(f"Verification (wrongpassword vs dummy_hash): {verify_password('wrongpassword', dummy_hashed)}")


    # Test JWT creation
    user_data_for_token = {"sub": "testuser", "role": "admin"}
    token = create_access_token(user_data_for_token)
    logger_sec_test.info(f"Generated JWT: {token[:20]}...")

    # Test get_admin_user_from_settings
    if settings:
        logger_sec_test.info(f"Attempting to get admin user: {settings.ADMIN_USERNAME}")
        admin_user_obj = get_admin_user_from_settings(settings.ADMIN_USERNAME)
        if admin_user_obj:
            logger_sec_test.info(f"Retrieved admin user: {admin_user_obj.username}, Role: {admin_user_obj.role}, Hashed Pass: {admin_user_obj.hashed_password[:10]}...")
        else:
            logger_sec_test.error(f"Could not retrieve admin user '{settings.ADMIN_USERNAME}' from settings (check ADMIN_PASSWORD_HASH or ADMIN_PASSWORD_PLAIN).")

        non_admin_user = get_admin_user_from_settings("nonadmin")
        logger_sec_test.info(f"Attempt to get non-admin user 'nonadmin': {non_admin_user}")
    else:
        logger_sec_test.warning("'settings' object not available. Skipping get_admin_user_from_settings test.")

```
