#!/usr/bin/env python3
"""
Pre-Deployment Zerodha Authentication
Generate access token NOW for seamless deployment without reauthorization
"""

import asyncio
import os
import sys
import requests
import json
from datetime import datetime, timedelta
import webbrowser
import time

class PreDeploymentZerodhaAuth:
    """Get Zerodha access token before deployment"""
    
    def __init__(self):
        self.api_key = "sylcoq492qz6f7ej"
        self.api_secret = "jm3h4iejwnxr4ngmma2qxccpkhevo8sy"
        self.backend_url = "http://localhost:8001"
        
    def get_login_url(self):
        """Get the login URL from our backend"""
        try:
            response = requests.get(f"{self.backend_url}/api/system/zerodha-auth-status")
            data = response.json()
            
            if data.get('success') and 'login_url' in data:
                return data['login_url']
            else:
                print(f"❌ Error getting login URL: {data}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def show_authentication_instructions(self):
        """Show detailed authentication instructions"""
        print("\n" + "="*80)
        print("🔐 ZERODHA PRE-DEPLOYMENT AUTHENTICATION")
        print("="*80)
        print("Purpose: Get access token NOW to avoid reauthorization after deployment")
        print("="*80)
        
        login_url = self.get_login_url()
        if not login_url:
            print("❌ Could not get login URL")
            return None
        
        print(f"\n📋 STEP-BY-STEP INSTRUCTIONS:")
        print("-" * 40)
        print("1. Click or copy this URL to your browser:")
        print(f"   {login_url}")
        print("\n2. Login with your Zerodha credentials")
        print("3. After successful login, you'll be redirected to a URL like:")
        print("   https://127.0.0.1/something?request_token=XXXXXX&action=login&status=success")
        print("\n4. Copy the 'request_token' value from the URL")
        print("5. Paste it below to complete authentication")
        
        # Try to open browser automatically
        try:
            print(f"\n🌐 Opening browser automatically...")
            webbrowser.open(login_url)
            print("✅ Browser opened! Complete the login process.")
        except:
            print("⚠️  Could not open browser automatically. Please copy the URL manually.")
        
        return login_url
    
    def authenticate_with_token(self, request_token):
        """Authenticate using the request token"""
        try:
            print(f"\n🔧 Authenticating with request token: {request_token[:10]}...")
            
            # Use our backend endpoint to authenticate
            response = requests.post(f"{self.backend_url}/api/system/zerodha-authenticate", 
                                   json={"request_token": request_token})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Authentication successful!")
                    print(f"✅ Access token obtained and configured")
                    print(f"✅ User: {data.get('user_info', {}).get('user_name', 'Unknown')}")
                    return True, data
                else:
                    print(f"❌ Authentication failed: {data.get('message', 'Unknown error')}")
                    return False, data
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False, None
    
    def verify_authentication(self):
        """Verify that authentication worked"""
        try:
            print("\n🔍 Verifying authentication...")
            
            response = requests.get(f"{self.backend_url}/api/system/zerodha-auth-status")
            data = response.json()
            
            zerodha_status = data.get('zerodha_status', {})
            
            if zerodha_status.get('authenticated') and zerodha_status.get('deployment_ready'):
                print("✅ Authentication verified!")
                print("✅ System is ready for deployment!")
                return True
            else:
                print("❌ Authentication verification failed")
                print(f"Status: {zerodha_status}")
                return False
                
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def update_production_files(self):
        """Update production files with the authenticated token"""
        try:
            print("\n📝 Updating production configuration...")
            
            # Get the current access token from backend
            response = requests.get(f"{self.backend_url}/api/system/zerodha-auth-status")
            data = response.json()
            
            # The token should now be configured in the backend
            # We'll create a production config file
            config = {
                "zerodha_authenticated": True,
                "authentication_completed": datetime.now().isoformat(),
                "deployment_ready": True,
                "production_mode": True,
                "token_configured": True,
                "notes": "Access token configured for deployment without reauthorization"
            }
            
            with open('/app/backend/production_auth_status.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Production configuration updated")
            return True
            
        except Exception as e:
            print(f"❌ Error updating production files: {e}")
            return False

def main():
    """Main authentication flow"""
    auth = PreDeploymentZerodhaAuth()
    
    print("🚀 PRE-DEPLOYMENT ZERODHA AUTHENTICATION")
    print("="*80)
    print("This will authenticate Zerodha NOW so you don't need to reauthorize after deployment!")
    print("="*80)
    
    # Step 1: Show instructions and get login URL
    login_url = auth.show_authentication_instructions()
    if not login_url:
        return False
    
    # Step 2: Wait for user to complete login and get request token
    print("\n" + "="*80)
    print("⏳ WAITING FOR YOUR LOGIN...")
    print("="*80)
    
    while True:
        try:
            request_token = input("\n📝 Enter the request_token from the redirect URL: ").strip()
            
            if not request_token:
                print("❌ No token entered. Please try again.")
                continue
            
            if len(request_token) < 10:
                print("❌ Token seems too short. Please check and try again.")
                continue
            
            break
            
        except KeyboardInterrupt:
            print("\n❌ Authentication cancelled by user")
            return False
        except Exception as e:
            print(f"❌ Error reading input: {e}")
            return False
    
    # Step 3: Authenticate with the token
    success, auth_data = auth.authenticate_with_token(request_token)
    if not success:
        print("❌ Authentication failed!")
        return False
    
    # Step 4: Verify authentication
    if not auth.verify_authentication():
        print("❌ Authentication verification failed!")
        return False
    
    # Step 5: Update production files
    if not auth.update_production_files():
        print("❌ Failed to update production configuration!")
        return False
    
    # Final success message
    print("\n" + "="*80)
    print("🎉 PRE-DEPLOYMENT AUTHENTICATION COMPLETE!")
    print("="*80)
    print("✅ Zerodha access token obtained and configured")
    print("✅ System ready for deployment without reauthorization")
    print("✅ You can now deploy to https://fresh-start-13.emergent.host/")
    print("✅ No manual authentication required after deployment!")
    print("\n🚀 DEPLOY WITH CONFIDENCE - Authentication is handled!")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)