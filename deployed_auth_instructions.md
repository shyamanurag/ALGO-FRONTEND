# ZERODHA AUTHENTICATION FOR DEPLOYED APP
# https://fresh-start-13.emergent.host/

## Method 1: Direct API Call
Run this command from your terminal or browser:

```bash
curl -X POST https://fresh-start-13.emergent.host/api/system/zerodha-authenticate \
  -H "Content-Type: application/json" \
  -d '{"request_token": "DhIcAK6aYODLUHQGr36F8vI4UGBnuDpb"}'
```

## Method 2: Web Interface (Recommended)
1. Go to: https://fresh-start-13.emergent.host/admin
2. Find "Zerodha Authentication Setup" section
3. Enter request token: `DhIcAK6aYODLUHQGr36F8vI4UGBnuDpb`
4. Click "Complete Authentication"

## Method 3: Browser JavaScript Console
1. Open https://fresh-start-13.emergent.host/
2. Press F12 to open developer console
3. Run this JavaScript:

```javascript
fetch('https://fresh-start-13.emergent.host/api/system/zerodha-authenticate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    request_token: 'DhIcAK6aYODLUHQGr36F8vI4UGBnuDpb'
  })
})
.then(response => response.json())
.then(data => {
  console.log('Authentication result:', data);
  alert('Authentication result: ' + JSON.stringify(data));
});
```

## Method 4: Test API Endpoint First
Check if the authentication endpoint exists:

```bash
curl https://fresh-start-13.emergent.host/api/system/zerodha-auth-status
```

## Method 5: Manual Environment Variable
If API methods don't work, you may need to manually add this to the deployed app's .env file:

```
ZERODHA_ACCESS_TOKEN=your_access_token_here
```

## Verification
After authentication, verify with:

```bash
curl https://fresh-start-13.emergent.host/api/system/zerodha-auth-status
```

Should return: `"authenticated": true`

---

**Request Token:** `DhIcAK6aYODLUHQGr36F8vI4UGBnuDpb`
**Target App:** https://fresh-start-13.emergent.host/
**Next Step:** Try Method 2 (Web Interface) first - it's the most reliable!