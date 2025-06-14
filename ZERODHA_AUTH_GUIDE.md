# 🔐 Zerodha Authentication Setup Guide

## 📋 Step 1: Get Zerodha API Credentials

1. **Login to Kite Connect Portal**
   - Visit: https://kite.trade/
   - Login with your Zerodha account

2. **Create New App**
   - Go to "My Apps" section
   - Click "Create New App"
   - Fill in details:
     - App Name: "ALGO-FRONTEND Trading"
     - App Type: "Connect"
     - Redirect URL: `https://your-domain.com/auth/callback`

3. **Get API Credentials**
   - API Key (public)
   - API Secret (private)
   - App ID

## 🔧 Step 2: Add Credentials to Deployed App

### Method 1: SSH and Edit Files
```bash
# SSH into your server
ssh root@your_server_ip

# Edit environment file
nano /opt/algo-trading/backend/.env

# Add/Update these lines:
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here
ZERODHA_CLIENT_ID=your_client_id_here
ZERODHA_ACCOUNT_NAME=your_account_name

# Save and restart backend
supervisorctl restart backend
```

### Method 2: Secure API Endpoint (Recommended)
Add an admin endpoint to update credentials securely:

```python
@api_router.post("/admin/update-zerodha-credentials")
async def update_zerodha_credentials(
    api_key: str,
    api_secret: str,
    client_id: str,
    admin_password: str
):
    # Verify admin password
    if admin_password != os.environ.get('ADMIN_PASSWORD'):
        raise HTTPException(403, "Invalid admin password")
    
    # Update environment file
    env_file_path = "/opt/algo-trading/backend/.env"
    # ... implementation
    
    return {"status": "Credentials updated successfully"}
```

## 🔄 Step 3: Zerodha Authentication Flow

### Initial Setup
```python
from kiteconnect import KiteConnect

# Initialize KiteConnect
kite = KiteConnect(api_key=ZERODHA_API_KEY)

# Get login URL
login_url = kite.login_url()
print(f"Login URL: {login_url}")
```

### Get Access Token
```python
# After user authorizes, you'll get request_token
# Exchange it for access_token
try:
    data = kite.generate_session(request_token, api_secret=ZERODHA_API_SECRET)
    access_token = data["access_token"]
    
    # Store access token securely
    kite.set_access_token(access_token)
    
except Exception as e:
    print(f"Authentication failed: {e}")
```

## 🔐 Step 4: Secure Token Management

### Environment Variables
```bash
# In your .env file
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
ZERODHA_ACCESS_TOKEN=your_access_token
ZERODHA_CLIENT_ID=your_client_id
```

### Database Storage (Recommended)
```sql
CREATE TABLE zerodha_auth (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    access_token VARCHAR NOT NULL,
    refresh_token VARCHAR,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 Step 5: Production Authentication Script

Create this script on your server:

```bash
#!/bin/bash
# /opt/algo-trading/setup_zerodha.sh

echo "🔐 Zerodha Authentication Setup"
echo "=============================="

read -p "Enter Zerodha API Key: " API_KEY
read -s -p "Enter Zerodha API Secret: " API_SECRET
echo
read -p "Enter Client ID: " CLIENT_ID
read -p "Enter Account Name: " ACCOUNT_NAME

# Update .env file
cd /opt/algo-trading/backend
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update environment variables
sed -i "s/ZERODHA_API_KEY=.*/ZERODHA_API_KEY=${API_KEY}/" .env
sed -i "s/ZERODHA_API_SECRET=.*/ZERODHA_API_SECRET=${API_SECRET}/" .env
sed -i "s/ZERODHA_CLIENT_ID=.*/ZERODHA_CLIENT_ID=${CLIENT_ID}/" .env
sed -i "s/ZERODHA_ACCOUNT_NAME=.*/ZERODHA_ACCOUNT_NAME=${ACCOUNT_NAME}/" .env

echo "✅ Credentials updated"

# Restart backend
supervisorctl restart backend

echo "✅ Backend restarted"

# Test connection
sleep 5
curl -s http://localhost:8001/api/health | grep -q "healthy" && {
    echo "✅ Backend is healthy"
} || {
    echo "❌ Backend health check failed"
}

echo "🎉 Zerodha setup completed!"
echo "Next: Visit your app and complete OAuth flow"
```

## 🔄 Step 6: OAuth Flow Implementation

### Frontend Component
```javascript
// ZerodhaAuth.js
import React, { useState } from 'react';
import axios from 'axios';

const ZerodhaAuth = () => {
    const [isConnecting, setIsConnecting] = useState(false);
    
    const initiateZerodhaAuth = async () => {
        setIsConnecting(true);
        try {
            const response = await axios.get('/api/zerodha/auth-url');
            window.location.href = response.data.login_url;
        } catch (error) {
            console.error('Auth initiation failed:', error);
            setIsConnecting(false);
        }
    };
    
    return (
        <div className="zerodha-auth">
            <button 
                onClick={initiateZerodhaAuth}
                disabled={isConnecting}
                className="bg-orange-500 text-white px-4 py-2 rounded"
            >
                {isConnecting ? 'Connecting...' : 'Connect Zerodha Account'}
            </button>
        </div>
    );
};

export default ZerodhaAuth;
```

### Backend OAuth Endpoints
```python
@api_router.get("/zerodha/auth-url")
async def get_zerodha_auth_url():
    kite = KiteConnect(api_key=ZERODHA_API_KEY)
    login_url = kite.login_url()
    return {"login_url": login_url}

@api_router.post("/zerodha/auth-callback")
async def zerodha_auth_callback(request_token: str):
    try:
        kite = KiteConnect(api_key=ZERODHA_API_KEY)
        data = kite.generate_session(request_token, api_secret=ZERODHA_API_SECRET)
        
        # Store access token securely
        access_token = data["access_token"]
        
        # Save to database or update environment
        # ... implementation
        
        return {"status": "success", "message": "Zerodha connected successfully"}
    except Exception as e:
        raise HTTPException(400, f"Authentication failed: {str(e)}")
```

## 🛡️ Security Best Practices

1. **Never log API secrets**
2. **Use HTTPS only**
3. **Rotate tokens regularly**
4. **Monitor API usage**
5. **Set up IP whitelisting**
6. **Use separate keys for dev/prod**

## 🔄 Token Refresh Strategy

```python
async def refresh_zerodha_token():
    """Refresh Zerodha access token if needed"""
    try:
        # Check if token is expiring
        # Refresh using refresh token or re-authenticate
        # Update stored credentials
        pass
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        # Trigger re-authentication
```

## ⚡ Quick Setup Commands

```bash
# Make setup script executable
chmod +x /opt/algo-trading/setup_zerodha.sh

# Run setup
./setup_zerodha.sh

# Check logs
tail -f /var/log/supervisor/backend.out.log
```