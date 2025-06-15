#!/usr/bin/env python3
"""
Zerodha Authentication Hardcode System
Generates and hardcodes access token for production deployment
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZerodhaHardcodeAuth:
    """Hardcode Zerodha authentication for production"""
    
    def __init__(self):
        self.api_key = "sylcoq492qz6f7ej"
        self.api_secret = "jm3h4iejwnxr4ngmma2qxccpkhevo8sy"
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token = None
        
    def get_login_url(self):
        """Get login URL for manual authentication"""
        try:
            login_url = self.kite.login_url()
            print("\n" + "="*80)
            print("🔐 ZERODHA AUTHENTICATION REQUIRED")
            print("="*80)
            print(f"1. Open this URL in your browser:")
            print(f"   {login_url}")
            print("\n2. Login with your Zerodha credentials")
            print("3. After login, you'll be redirected to a URL with 'request_token'")
            print("4. Copy the 'request_token' parameter from the URL")
            print("5. Enter it below to generate access token")
            print("="*80)
            return login_url
        except Exception as e:
            logger.error(f"Error getting login URL: {e}")
            return None
    
    def authenticate_with_request_token(self, request_token: str):
        """Generate access token from request token"""
        try:
            print(f"\n🔄 Generating access token with request_token: {request_token}")
            
            # Generate session
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            user_id = data["user_id"]
            
            print(f"✅ Authentication successful!")
            print(f"   User ID: {user_id}")
            print(f"   Access Token: {self.access_token}")
            
            # Verify token works
            self.kite.set_access_token(self.access_token)
            profile = self.kite.profile()
            
            print(f"✅ Token verified! User: {profile['user_name']} ({profile['email']})")
            
            return {
                "access_token": self.access_token,
                "user_id": user_id,
                "user_name": profile['user_name'],
                "email": profile['email'],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def hardcode_token_in_files(self, auth_data):
        """Hardcode the access token in necessary files"""
        try:
            print("\n🔧 HARDCODING ACCESS TOKEN IN FILES...")
            print("="*60)
            
            # 1. Update .env file
            self._update_env_file(auth_data)
            
            # 2. Update real_zerodha_client.py
            self._update_zerodha_client(auth_data)
            
            # 3. Create auth backup file
            self._create_auth_backup(auth_data)
            
            print("✅ ACCESS TOKEN SUCCESSFULLY HARDCODED!")
            print("🚀 System is now ready for production deployment!")
            
        except Exception as e:
            logger.error(f"Error hardcoding token: {e}")
    
    def _update_env_file(self, auth_data):
        """Update .env file with access token"""
        env_path = "/app/backend/.env"
        
        # Read current env file
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add access token
        updated_lines = []
        token_found = False
        
        for line in lines:
            if line.startswith('ZERODHA_ACCESS_TOKEN='):
                updated_lines.append(f'ZERODHA_ACCESS_TOKEN={auth_data["access_token"]}\n')
                token_found = True
            else:
                updated_lines.append(line)
        
        # If token line not found, add it
        if not token_found:
            # Find the right place to add it (after other ZERODHA configs)
            for i, line in enumerate(updated_lines):
                if line.startswith('ZERODHA_API_SECRET='):
                    updated_lines.insert(i + 1, f'ZERODHA_ACCESS_TOKEN={auth_data["access_token"]}\n')
                    break
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Updated .env file with access token")
    
    def _update_zerodha_client(self, auth_data):
        """Update real_zerodha_client.py with hardcoded token"""
        client_path = "/app/backend/real_zerodha_client.py"
        
        # Read current file
        with open(client_path, 'r') as f:
            content = f.read()
        
        # Replace access token initialization
        old_line = 'self.access_token = os.getenv(\'ZERODHA_ACCESS_TOKEN\')'
        new_line = f'self.access_token = os.getenv(\'ZERODHA_ACCESS_TOKEN\', \'{auth_data["access_token"]}\')'
        
        content = content.replace(old_line, new_line)
        
        # Write back
        with open(client_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated real_zerodha_client.py with hardcoded fallback")
    
    def _create_auth_backup(self, auth_data):
        """Create a backup file with authentication data"""
        backup_path = "/app/backend/zerodha_auth_backup.json"
        
        backup_data = {
            "production_auth": auth_data,
            "deployment_ready": True,
            "last_updated": datetime.now().isoformat(),
            "notes": "Hardcoded authentication for https://fresh-start-13.emergent.host/ deployment"
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"✅ Created authentication backup file")

async def main():
    """Main authentication flow"""
    auth_system = ZerodhaHardcodeAuth()
    
    print("🤖 ZERODHA HARDCODE AUTHENTICATION SYSTEM")
    print("="*80)
    print("Purpose: Generate and hardcode access token for production deployment")
    print("Target: https://fresh-start-13.emergent.host/")
    print("="*80)
    
    # Step 1: Get login URL
    login_url = auth_system.get_login_url()
    if not login_url:
        print("❌ Failed to generate login URL")
        return
    
    # Step 2: Get request token from user
    request_token = input("\n📝 Enter the request_token from the redirect URL: ").strip()
    
    if not request_token:
        print("❌ No request token provided")
        return
    
    # Step 3: Generate access token
    auth_data = auth_system.authenticate_with_request_token(request_token)
    if not auth_data:
        print("❌ Authentication failed")
        return
    
    # Step 4: Hardcode in files
    auth_system.hardcode_token_in_files(auth_data)
    
    print("\n" + "="*80)
    print("🎉 AUTHENTICATION HARDCODING COMPLETE!")
    print("="*80)
    print("✅ Access token hardcoded in:")
    print("   - /app/backend/.env")
    print("   - /app/backend/real_zerodha_client.py")
    print("   - /app/backend/zerodha_auth_backup.json")
    print("\n🚀 System is ready for deployment to https://fresh-start-13.emergent.host/")
    print("⚡ No manual authentication required after deployment!")

if __name__ == "__main__":
    asyncio.run(main())