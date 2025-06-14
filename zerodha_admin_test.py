#!/usr/bin/env python3
"""
Elite Trading Platform - Zerodha Admin Integration Tests
Tests the Zerodha integration in the admin panel
"""

import requests
import json
import sys
import os
from urllib.parse import urlparse, parse_qs

# Get the backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://0880b436-2c26-46a5-94e2-507e0663832d.preview.emergentagent.com')

class ZerodhaAdminIntegrationTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status=200, data=None, validate_func=None):
        """Run a single API test"""
        url = f"{self.base_url}/api{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            
            status_success = response.status_code == expected_status
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                print(f"   Response: {json.dumps(response_data, indent=2)[:500]}...")
            except:
                response_data = {"text": response.text[:100] + "..."}
                print(f"   Response: {response.text[:100]}...")
            
            # Validate response content if function provided
            content_success = True
            validation_message = ""
            if validate_func and status_success:
                content_success, validation_message = validate_func(response_data)
            
            success = status_success and content_success
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if validation_message:
                    print(f"   {validation_message}")
            else:
                if not status_success:
                    print(f"❌ Failed - Expected status {expected_status}, got {response.status_code}")
                if not content_success:
                    print(f"❌ Failed - {validation_message}")
            
            self.test_results.append({
                "name": name,
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "validation_message": validation_message if not content_success else "",
                "response": response_data
            })
            
            return success, response_data
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "success": False,
                "error": str(e)
            })
            return False, {"error": str(e)}

    def validate_zerodha_status(self, response):
        """Validate Zerodha status response"""
        if not response.get("success", False):
            return False, "Response missing success=true"
        
        zerodha = response.get("zerodha", {})
        if not isinstance(zerodha, dict):
            return False, "Response missing zerodha object"
        
        # Check for required fields
        required_fields = ["account_name", "client_id", "api_key"]
        missing_fields = [field for field in required_fields if field not in zerodha]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate specific values
        if zerodha.get("account_name") != "Shyam anurag":
            return False, f"Incorrect account_name: {zerodha.get('account_name')}"
        
        if zerodha.get("client_id") != "QSW899":
            return False, f"Incorrect client_id: {zerodha.get('client_id')}"
        
        # Check API key is masked
        api_key = zerodha.get("api_key", "")
        if not api_key.endswith("..."):
            return False, "API key should be masked"
        
        return True, "Zerodha status contains correct account information"

    def validate_login_url(self, response):
        """Validate Zerodha login URL response"""
        if not response.get("success", False):
            return False, "Response missing success=true"
        
        login_url = response.get("login_url")
        if not login_url:
            return False, "Response missing login_url"
        
        # Parse URL to check parameters
        parsed_url = urlparse(login_url)
        
        if parsed_url.netloc != "kite.zerodha.com":
            return False, f"Incorrect URL domain: {parsed_url.netloc}"
        
        query_params = parse_qs(parsed_url.query)
        
        if "api_key" not in query_params:
            return False, "URL missing api_key parameter"
        
        api_key = query_params["api_key"][0]
        if api_key != "sylcoq492qz6f7ej":
            return False, f"Incorrect API key in URL: {api_key}"
        
        return True, "Login URL is valid and contains correct API key"

    def validate_connect_response(self, response):
        """Validate Zerodha connect response"""
        # For testing, we expect an error since we're not completing the OAuth flow
        if response.get("success", False):
            # If it somehow succeeds, check for profile data
            if "profile" not in response:
                return False, "Success response missing profile data"
            return True, "Connection successful with profile data"
        else:
            # Check for appropriate error message
            error = response.get("error", "")
            if not error:
                return False, "Error response missing error message"
            
            # The expected behavior is an error since we're not completing OAuth
            return True, f"Expected error response: {error}"

    def validate_disconnect_response(self, response):
        """Validate Zerodha disconnect response"""
        if not response.get("success", False):
            return False, "Response missing success=true"
        
        if "message" not in response:
            return False, "Response missing message"
        
        return True, "Disconnect response is valid"

    def validate_funds_response(self, response):
        """Validate Zerodha funds response"""
        # Since we're not authenticated, we expect an error response
        if not response.get("success", False) and "error" in response:
            return True, "Expected error response for unauthenticated request"
        
        # If somehow successful, check for funds data
        if "funds" not in response:
            return False, "Success response missing funds data"
        
        return True, "Funds response is valid"

    def validate_positions_response(self, response):
        """Validate Zerodha positions response"""
        # Since we're not authenticated, we expect an error response
        if not response.get("success", False) and "error" in response:
            return True, "Expected error response for unauthenticated request"
        
        # If somehow successful, check for positions data
        if "positions" not in response:
            return False, "Success response missing positions data"
        
        return True, "Positions response is valid"

    def validate_orders_response(self, response):
        """Validate Zerodha orders response"""
        # Since we're not authenticated, we expect an error response
        if not response.get("success", False) and "error" in response:
            return True, "Expected error response for unauthenticated request"
        
        # If somehow successful, check for orders data
        if "orders" not in response:
            return False, "Success response missing orders data"
        
        return True, "Orders response is valid"

    def run_all_tests(self):
        """Run all Zerodha integration tests"""
        print("\n🚀 Starting Zerodha Admin Integration Tests")
        print(f"Backend URL: {self.base_url}")
        
        # Test 1: Get Zerodha status
        self.run_test(
            "Zerodha Status",
            "GET",
            "/admin/zerodha/status",
            200,
            validate_func=self.validate_zerodha_status
        )
        
        # Test 2: Get Zerodha login URL
        self.run_test(
            "Zerodha Login URL",
            "GET",
            "/admin/zerodha/login-url",
            200,
            validate_func=self.validate_login_url
        )
        
        # Test 3: Connect with request token (will fail without actual OAuth flow)
        self.run_test(
            "Zerodha Connect",
            "POST",
            "/admin/zerodha/connect",
            200,
            data={"request_token": "test_token"},
            validate_func=self.validate_connect_response
        )
        
        # Test 4: Disconnect
        self.run_test(
            "Zerodha Disconnect",
            "POST",
            "/admin/zerodha/disconnect",
            200,
            validate_func=self.validate_disconnect_response
        )
        
        # Test 5: Get funds (will fail without authentication)
        self.run_test(
            "Zerodha Funds",
            "GET",
            "/admin/zerodha/funds",
            200,
            validate_func=self.validate_funds_response
        )
        
        # Test 6: Get positions (will fail without authentication)
        self.run_test(
            "Zerodha Positions",
            "GET",
            "/admin/zerodha/positions",
            200,
            validate_func=self.validate_positions_response
        )
        
        # Test 7: Get orders (will fail without authentication)
        self.run_test(
            "Zerodha Orders",
            "GET",
            "/admin/zerodha/orders",
            200,
            validate_func=self.validate_orders_response
        )
        
        # Print summary
        print("\n📊 Test Summary:")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run) * 100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main function"""
    tester = ZerodhaAdminIntegrationTester(BACKEND_URL)
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())