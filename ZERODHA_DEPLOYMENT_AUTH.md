# 🔐 Post-Deployment Zerodha Authentication Guide

## Method 1: DigitalOcean App Platform Environment Variables (RECOMMENDED)

### Step 1: Deploy App Without Credentials
Deploy your app with empty Zerodha credentials:
```yaml
# .do/app.yaml
envs:
- key: ZERODHA_API_KEY
  value: ""  # Empty initially
- key: ZERODHA_API_SECRET
  type: SECRET
  value: ""  # Empty initially
```

### Step 2: Add Credentials Through DigitalOcean Dashboard
1. Go to DigitalOcean App Platform dashboard
2. Select your deployed ALGO-FRONTEND app
3. Go to "Settings" → "App-Level Environment Variables"
4. Add/Update:
   - `ZERODHA_API_KEY`: your_actual_api_key
   - `ZERODHA_API_SECRET`: your_actual_secret (mark as SECRET)
   - `ZERODHA_CLIENT_ID`: your_client_id
5. Click "Save" → App will automatically restart with new credentials

### Step 3: Complete OAuth Flow
1. Access your deployed app: `https://your-app-url.com`
2. Navigate to Admin Dashboard
3. Click "Connect Zerodha Account"
4. Complete OAuth flow in popup window
5. Access token will be stored securely

---

## Method 2: Secure Admin Configuration Panel

### Implementation in Your App
Add this secure admin endpoint to your backend:

```python
# In your backend/server.py
@api_router.post("/admin/configure-zerodha")
async def configure_zerodha_credentials(
    api_key: str,
    api_secret: str,
    client_id: str,
    admin_password: str
):
    # Verify admin password
    if admin_password != os.environ.get('ADMIN_PASSWORD'):
        raise HTTPException(403, "Invalid admin password")
    
    # Update environment variables (runtime)
    os.environ['ZERODHA_API_KEY'] = api_key
    os.environ['ZERODHA_API_SECRET'] = api_secret
    os.environ['ZERODHA_CLIENT_ID'] = client_id
    
    # Optionally save to database encrypted
    await save_encrypted_credentials(api_key, api_secret, client_id)
    
    return {"success": True, "message": "Zerodha credentials configured"}
```

### Frontend Admin Panel
```javascript
// Add to your AdminDashboard component
const ConfigureZerodha = () => {
  const [credentials, setCredentials] = useState({
    apiKey: '',
    apiSecret: '',
    clientId: '',
    adminPassword: ''
  });

  const handleSubmit = async () => {
    try {
      const response = await fetch('/api/admin/configure-zerodha', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      if (response.ok) {
        alert('✅ Zerodha credentials configured successfully!');
      }
    } catch (error) {
      alert('❌ Configuration failed');
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-bold mb-4">🔐 Configure Zerodha Credentials</h3>
      
      <input
        type="text"
        placeholder="Zerodha API Key"
        value={credentials.apiKey}
        onChange={(e) => setCredentials({...credentials, apiKey: e.target.value})}
        className="w-full p-2 border rounded mb-3"
      />
      
      <input
        type="password"
        placeholder="Zerodha API Secret"
        value={credentials.apiSecret}
        onChange={(e) => setCredentials({...credentials, apiSecret: e.target.value})}
        className="w-full p-2 border rounded mb-3"
      />
      
      <input
        type="text"
        placeholder="Client ID"
        value={credentials.clientId}
        onChange={(e) => setCredentials({...credentials, clientId: e.target.value})}
        className="w-full p-2 border rounded mb-3"
      />
      
      <input
        type="password"
        placeholder="Admin Password"
        value={credentials.adminPassword}
        onChange={(e) => setCredentials({...credentials, adminPassword: e.target.value})}
        className="w-full p-2 border rounded mb-3"
      />
      
      <button
        onClick={handleSubmit}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Configure Zerodha
      </button>
    </div>
  );
};
```

---

## Method 3: OAuth Flow Integration (MOST SECURE)

### Complete Zerodha OAuth Implementation

```python
# Enhanced Zerodha OAuth endpoints
from kiteconnect import KiteConnect

@api_router.get("/zerodha/auth-url")
async def get_zerodha_auth_url():
    """Get Zerodha login URL for OAuth"""
    try:
        api_key = os.environ.get('ZERODHA_API_KEY')
        if not api_key:
            raise HTTPException(400, "Zerodha API key not configured")
        
        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()
        
        return {
            "success": True,
            "login_url": login_url,
            "message": "Visit this URL to authenticate"
        }
    except Exception as e:
        raise HTTPException(500, f"Error generating auth URL: {str(e)}")

@api_router.post("/zerodha/complete-auth")
async def complete_zerodha_auth(request_token: str):
    """Complete Zerodha OAuth with request token"""
    try:
        api_key = os.environ.get('ZERODHA_API_KEY')
        api_secret = os.environ.get('ZERODHA_API_SECRET')
        
        if not api_key or not api_secret:
            raise HTTPException(400, "Zerodha credentials not configured")
        
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(request_token, api_secret=api_secret)
        
        # Store access token securely
        access_token = data["access_token"]
        await store_zerodha_token(access_token, data)
        
        return {
            "success": True,
            "message": "Zerodha authentication completed",
            "user_id": data.get("user_id"),
            "user_name": data.get("user_name")
        }
    except Exception as e:
        raise HTTPException(500, f"Authentication failed: {str(e)}")
```

### Frontend OAuth Component
```javascript
const ZerodhaAuth = () => {
  const [authStatus, setAuthStatus] = useState('disconnected');
  
  const initiateAuth = async () => {
    try {
      const response = await fetch('/api/zerodha/auth-url');
      const data = await response.json();
      
      if (data.success) {
        // Open OAuth popup
        const popup = window.open(data.login_url, 'zerodha-auth', 'width=500,height=600');
        
        // Listen for completion
        const checkAuth = setInterval(() => {
          try {
            if (popup.closed) {
              clearInterval(checkAuth);
              // Check if authentication was successful
              checkAuthStatus();
            }
          } catch (e) {
            // Handle cross-origin restrictions
          }
        }, 1000);
      }
    } catch (error) {
      console.error('Auth initiation failed:', error);
    }
  };
  
  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/zerodha/status');
      const data = await response.json();
      setAuthStatus(data.connected ? 'connected' : 'disconnected');
    } catch (error) {
      setAuthStatus('error');
    }
  };
  
  return (
    <div className="bg-gradient-to-r from-orange-50 to-red-50 p-4 rounded-lg border">
      <h3 className="font-bold text-orange-800">🔐 Zerodha Authentication</h3>
      <p className="text-sm text-orange-600 mb-3">
        Status: {authStatus === 'connected' ? '✅ Connected' : '🔴 Disconnected'}
      </p>
      
      {authStatus !== 'connected' && (
        <button
          onClick={initiateAuth}
          className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700"
        >
          🚀 Authenticate with Zerodha
        </button>
      )}
    </div>
  );
};
```

---

## Method 4: Secure Configuration Script

### SSH-based Configuration (Advanced Users)
```bash
#!/bin/bash
# deploy-configure.sh

echo "🔐 ALGO-FRONTEND Post-Deployment Configuration"
echo "=============================================="

# Get credentials securely
read -p "Enter Zerodha API Key: " API_KEY
read -s -p "Enter Zerodha API Secret: " API_SECRET
echo
read -p "Enter Client ID: " CLIENT_ID

# Update DigitalOcean app via doctl
doctl apps update $APP_ID --spec <(cat <<EOF
name: algo-frontend-trading
services:
- name: backend
  envs:
  - key: ZERODHA_API_KEY
    value: "$API_KEY"
  - key: ZERODHA_API_SECRET
    value: "$API_SECRET"
  - key: ZERODHA_CLIENT_ID
    value: "$CLIENT_ID"
EOF
)

echo "✅ Credentials updated successfully!"
echo "🔄 App is redeploying with new configuration..."
```

---

## 📋 RECOMMENDED WORKFLOW

### For Your ALGO-FRONTEND Deployment:

1. **Deploy First** (without credentials):
   ```bash
   git push origin main  # Triggers DigitalOcean deployment
   ```

2. **Configure via DigitalOcean Dashboard**:
   - Go to App Platform → Your App → Settings
   - Add Zerodha environment variables
   - App auto-restarts with credentials

3. **Complete OAuth in Your App**:
   - Visit your deployed app URL
   - Go to Admin Dashboard
   - Use the Zerodha Auth component
   - Complete OAuth flow

4. **Verify Connection**:
   - Check system status shows "Zerodha: CONNECTED"
   - Test paper trading functionality
   - Monitor for real data flow

### 🔐 Security Best Practices:

- ✅ **Never commit API keys** to git repository
- ✅ **Use DigitalOcean Secrets** for sensitive data
- ✅ **Implement OAuth flow** for production apps
- ✅ **Monitor access logs** for unauthorized attempts
- ✅ **Rotate keys regularly** for security
- ✅ **Use HTTPS only** for all credential exchanges

This way, you can deploy your sophisticated ALGO-FRONTEND platform and securely configure Zerodha authentication post-deployment!