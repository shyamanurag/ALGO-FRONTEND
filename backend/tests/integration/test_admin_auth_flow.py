import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

# Assuming the FastAPI app instance is in backend.server (or backend.main)
# Adjust the import based on where 'app = FastAPI()' is located.
# If server.py was renamed to main.py by the tool:
try:
    from backend.main import app, get_app_state, AppState, settings as global_settings_main # Assuming settings is also exposed for patching
except ImportError:
    from backend.server import app, get_app_state, AppState, settings as global_settings_main


# Mock settings for security module specifically for admin credentials during testing
# This is a simplified version of what was in security unit tests.
class MockAdminTestSettings:
    ADMIN_USERNAME: str = "test_admin_user"
    ADMIN_PASSWORD_PLAIN: str = "test_admin_password"
    # security.py's get_admin_user_from_settings will hash this plain password
    # if ADMIN_PASSWORD_HASH is None, or use ADMIN_PASSWORD_HASH if provided.
    ADMIN_PASSWORD_HASH: Optional[str] = None

    # JWT settings needed by security.create_access_token
    JWT_SECRET_KEY: str = "a_very_test_secret_for_admin_flow"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    def __init__(self):
        if not self.ADMIN_PASSWORD_HASH and self.ADMIN_PASSWORD_PLAIN:
            # Import here to avoid circular dependencies at module level if utils imports security
            from backend.src.core.security import get_password_hash
            self.ADMIN_PASSWORD_HASH = get_password_hash(self.ADMIN_PASSWORD_PLAIN)

# This will be patched into src.core.security.settings
mock_security_settings = MockAdminTestSettings()


class TestAdminAuthFlow(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        # Patch the settings instance specifically where it's imported in security.py
        # This ensures that the auth functions use our test admin credentials.
        self.settings_patcher = patch('backend.src.core.security.settings', mock_security_settings)
        self.mock_settings_in_security = self.settings_patcher.start()

        # You might also need to ensure app_state.config is appropriately set if routes
        # directly depend on it via Depends(get_settings) for things other than what security.py uses.
        # For this test, the critical part is that the /api/admin/token route uses
        # logic that eventually calls get_admin_user_from_settings from security.py
        # which will now use our patched mock_security_settings.

        # Example: If get_settings() dependency in routes needs to reflect these specific settings:
        # async def override_get_settings(): return mock_security_settings
        # app.dependency_overrides[get_settings_dependency_from_server_or_main] = override_get_settings
        # This is more complex and depends on how get_settings is defined and imported.
        # For now, focusing on patching where security functions directly read settings.

    def tearDown(self):
        self.settings_patcher.stop()
        # app.dependency_overrides.clear() # Clear overrides if used

    def test_01_get_admin_token_success(self):
        response = self.client.post(
            "/api/admin/token", # Path from admin_routes.py
            data={"username": mock_security_settings.ADMIN_USERNAME, "password": mock_security_settings.ADMIN_PASSWORD_PLAIN}
        )
        self.assertEqual(response.status_code, 200)
        token_data = response.json()
        self.assertIn("access_token", token_data)
        self.assertEqual(token_data["token_type"], "bearer")
        self.assertIsNotNone(token_data["access_token"])

    def test_02_get_admin_token_failure_wrong_password(self):
        response = self.client.post(
            "/api/admin/token",
            data={"username": mock_security_settings.ADMIN_USERNAME, "password": "wrong_password"}
        )
        self.assertEqual(response.status_code, 401) # HTTPException(status_code=401 from admin_routes
        error_data = response.json()
        self.assertIn("Incorrect username or password", error_data.get("detail", ""))

    def test_03_get_admin_token_failure_wrong_username(self):
        response = self.client.post(
            "/api/admin/token",
            data={"username": "wrong_admin", "password": mock_security_settings.ADMIN_PASSWORD_PLAIN}
        )
        self.assertEqual(response.status_code, 401)
        error_data = response.json()
        self.assertIn("Incorrect username or password", error_data.get("detail", ""))

    def test_04_access_protected_route_no_token(self):
        # Assuming /api/admin/status/system-health is a protected route
        # This route is in admin_routes.py and depends on get_current_active_admin_user
        response = self.client.get("/api/admin/status/system-health")
        # Expect 401 if Depends(get_current_active_admin_user) correctly blocks
        self.assertEqual(response.status_code, 401)
        self.assertIn("Not authenticated", response.json().get("detail","").lower())


    def test_05_access_protected_route_with_valid_token(self):
        # 1. Get token
        token_response = self.client.post(
            "/api/admin/token",
            data={"username": mock_security_settings.ADMIN_USERNAME, "password": mock_security_settings.ADMIN_PASSWORD_PLAIN}
        )
        self.assertEqual(token_response.status_code, 200)
        access_token = token_response.json()["access_token"]

        # 2. Access protected route with token
        headers = {"Authorization": f"Bearer {access_token}"}
        protected_response = self.client.get("/api/admin/status/system-health", headers=headers)

        self.assertEqual(protected_response.status_code, 200)
        data = protected_response.json()
        # Check for some expected keys in the system health response (depends on actual route output)
        self.assertIn("data", data)
        self.assertIn("system_health", data["data"])


    def test_06_access_protected_route_with_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        protected_response = self.client.get("/api/admin/status/system-health", headers=headers)
        self.assertEqual(protected_response.status_code, 401) # Or 403 depending on how JWT errors are handled
        # The detail message depends on how JWTError is translated to HTTPException by oauth2_scheme or dependencies
        # Common messages: "Could not validate credentials", "Invalid token"
        self.assertIn("Could not validate credentials", protected_response.json().get("detail",""))


if __name__ == '__main__':
    unittest.main()
```
