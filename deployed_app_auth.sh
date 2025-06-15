#!/bin/bash
# Configure Zerodha Authentication in Deployed App
# Target: https://fresh-start-13.emergent.host/

echo "🔐 CONFIGURING ZERODHA AUTHENTICATION IN DEPLOYED APP"
echo "================================================================"
echo "Target: https://fresh-start-13.emergent.host/"
echo "Request Token: DhIcAK6aYODLUHQGr36F8vI4UGBnuDpb"
echo "================================================================"

# Make the authentication API call to your deployed app
curl -X POST https://fresh-start-13.emergent.host/api/system/zerodha-authenticate \
  -H "Content-Type: application/json" \
  -d '{"request_token": "DhIcAK6aYODLUHQGr36F8vI4UGBnuDpb"}' \
  --verbose

echo ""
echo "================================================================"
echo "✅ Authentication request sent to deployed app!"
echo "🔍 Check the response above for success confirmation"
echo "================================================================"