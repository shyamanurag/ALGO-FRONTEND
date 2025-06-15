#!/usr/bin/env python3
"""
Production Zerodha Setup for https://fresh-start-13.emergent.host/
One-time setup to configure Zerodha access token for production deployment
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add backend to Python path
sys.path.append('/app/backend')

from real_zerodha_client import get_real_zerodha_client, set_production_access_token

class ProductionZerodhaSetup:
    """Setup Zerodha for production deployment"""
    
    def __init__(self):
        self.api_key = "sylcoq492qz6f7ej"
        self.api_secret = "jm3h4iejwnxr4ngmma2qxccpkhevo8sy"
        self.production_url = "https://fresh-start-13.emergent.host"
        
    def generate_access_token_info(self):
        """Generate info for manual access token setup"""
        print("\n" + "="*80)
        print("🚀 PRODUCTION ZERODHA SETUP FOR DEPLOYMENT")
        print("="*80)
        print(f"Target URL: {self.production_url}")
        print(f"API Key: {self.api_key}")
        print("="*80)
        
        # Generate login URL
        try:
            from kiteconnect import KiteConnect
            kite = KiteConnect(api_key=self.api_key)
            login_url = kite.login_url()
            
            print("\n📋 MANUAL SETUP INSTRUCTIONS:")
            print("-" * 40)
            print("1. Open this URL in your browser:")
            print(f"   {login_url}")
            print("\n2. Login with Zerodha credentials")
            print("3. Copy the 'request_token' from redirect URL")
            print("4. Use it to generate access token with this script")
            
            return login_url
            
        except Exception as e:
            print(f"❌ Error generating login URL: {e}")
            return None
    
    def setup_with_request_token(self, request_token: str):
        """Setup production access token with request token"""
        try:
            print(f"\n🔧 Setting up production token with request_token: {request_token}")
            
            from kiteconnect import KiteConnect
            kite = KiteConnect(api_key=self.api_key)
            
            # Generate access token
            data = kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = data["access_token"]
            user_id = data["user_id"]
            
            print(f"✅ Access token generated: {access_token}")
            print(f"✅ User ID: {user_id}")
            
            # Verify token
            kite.set_access_token(access_token)
            profile = kite.profile()
            print(f"✅ Token verified for user: {profile['user_name']}")
            
            # Configure in system
            self._configure_production_token(access_token, {
                "user_id": user_id,
                "user_name": profile['user_name'],
                "email": profile['email'],
                "generated_at": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def _configure_production_token(self, access_token: str, user_info: dict):
        """Configure the access token in production files"""
        print("\n🔧 CONFIGURING PRODUCTION FILES...")
        
        # 1. Update .env file
        self._update_env_file(access_token)
        
        # 2. Set in real_zerodha_client
        set_production_access_token(access_token)
        
        # 3. Create production config
        self._create_production_config(access_token, user_info)
        
        print("✅ Production configuration complete!")
    
    def _update_env_file(self, access_token: str):
        """Update .env file with production access token"""
        env_path = "/app/backend/.env"
        
        # Read current file
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Replace the placeholder
        content = content.replace(
            'ZERODHA_ACCESS_TOKEN=PRODUCTION_HARDCODED_TOKEN_WILL_BE_SET',
            f'ZERODHA_ACCESS_TOKEN={access_token}'
        )
        
        # Write back
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("✅ Updated .env file with production access token")
    
    def _create_production_config(self, access_token: str, user_info: dict):
        """Create production configuration file"""
        config_path = "/app/backend/production_zerodha_config.json"
        
        config = {
            "production_mode": True,
            "deployment_url": self.production_url,
            "api_key": self.api_key,
            "access_token": access_token,
            "user_info": user_info,
            "configured_at": datetime.now().isoformat(),
            "status": "PRODUCTION_READY"
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Created production configuration file")
    
    def verify_production_setup(self):
        """Verify that production setup is working"""
        print("\n🧪 VERIFYING PRODUCTION SETUP...")
        
        try:
            client = get_real_zerodha_client()
            status = client.get_status()
            
            print(f"📊 Authentication Status: {status['authenticated']}")
            print(f"📊 Access Token Available: {status['access_token_available']}")
            print(f"📊 Production Ready: {status['deployment_ready']}")
            
            if status['authenticated'] and status['deployment_ready']:
                print("✅ PRODUCTION SETUP VERIFIED!")
                print("🚀 System ready for deployment!")
                return True
            else:
                print("❌ Production setup incomplete")
                return False
                
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

def main():
    """Main setup function"""
    setup = ProductionZerodhaSetup()
    
    print("🤖 ALGO-FRONTEND PRODUCTION ZERODHA SETUP")
    print("="*80)
    
    # Check if already configured
    try:
        client = get_real_zerodha_client()
        if client.authenticated:
            print("✅ Zerodha already configured for production!")
            print("🚀 System ready for deployment!")
            return
    except:
        pass
    
    # Generate setup info
    login_url = setup.generate_access_token_info()
    
    if login_url:
        print("\n" + "="*80)
        print("🔗 LOGIN URL GENERATED")
        print("="*80)
        print("Use this URL to authenticate and get the request_token")
        print("Then run this script again with the token")
        print("="*80)
        
        # For production deployment, we'll provide instructions
        print("\n📋 FOR PRODUCTION DEPLOYMENT:")
        print("1. Complete authentication manually")
        print("2. Update ZERODHA_ACCESS_TOKEN in .env file")
        print("3. Restart the backend service")
        print("4. System will be ready for production!")

if __name__ == "__main__":
    main()