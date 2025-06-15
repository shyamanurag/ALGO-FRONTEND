import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function ZerodhaAuthSetup() {
  const [authStatus, setAuthStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authenticating, setAuthenticating] = useState(false);
  const [loginUrl, setLoginUrl] = useState('');
  const [requestToken, setRequestToken] = useState('');
  const [showManualEntry, setShowManualEntry] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/system/zerodha-auth-status`);
      const data = await response.json();
      
      if (data.success) {
        setAuthStatus(data.zerodha_status);
        setLoginUrl(data.login_url || '');
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthenticate = async () => {
    if (!requestToken.trim()) {
      alert('Please enter the request token');
      return;
    }

    setAuthenticating(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/system/zerodha-authenticate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ request_token: requestToken.trim() })
      });

      const data = await response.json();
      
      if (data.success) {
        alert('✅ Zerodha authentication successful!');
        setRequestToken('');
        setShowManualEntry(false);
        checkAuthStatus(); // Refresh status
      } else {
        alert(`❌ Authentication failed: ${data.message}`);
      }
    } catch (error) {
      console.error('Authentication error:', error);
      alert('❌ Authentication error. Please try again.');
    } finally {
      setAuthenticating(false);
    }
  };

  const openZerodhaLogin = () => {
    if (loginUrl) {
      window.open(loginUrl, '_blank');
      setShowManualEntry(true);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse flex space-x-4">
          <div className="rounded-full bg-blue-400 h-10 w-10"></div>
          <div className="flex-1 space-y-2 py-1">
            <div className="h-4 bg-blue-400 rounded w-3/4"></div>
            <div className="h-4 bg-blue-400 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          🔐 Zerodha Authentication Setup
        </h3>
      </div>
      
      <div className="p-6">
        {/* Status Display */}
        <div className="mb-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className={`w-3 h-3 rounded-full ${
              authStatus?.authenticated ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="font-medium">
              Status: {authStatus?.authenticated ? 'Authenticated ✅' : 'Not Authenticated ❌'}
            </span>
          </div>
          
          {authStatus?.authenticated && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="text-green-800 font-medium mb-2">🎉 Authentication Complete!</h4>
              <p className="text-green-700 text-sm">
                Zerodha is successfully authenticated and ready for live trading.
                The system will automatically manage your access token.
              </p>
            </div>
          )}
        </div>

        {!authStatus?.authenticated && (
          <div className="space-y-6">
            {/* Instructions */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="text-blue-800 font-medium mb-2">📋 Authentication Steps:</h4>
              <ol className="text-blue-700 text-sm space-y-1 list-decimal list-inside">
                <li>Click "Authenticate with Zerodha" below</li>
                <li>Login with your Zerodha credentials in the new tab</li>
                <li>After login, copy the 'request_token' from the redirect URL</li>
                <li>Paste it in the box below and click "Complete Authentication"</li>
              </ol>
            </div>

            {/* Authentication Button */}
            <div className="text-center">
              <button
                onClick={openZerodhaLogin}
                className="bg-orange-600 hover:bg-orange-700 text-white font-bold py-3 px-6 rounded-lg transition duration-200 flex items-center mx-auto space-x-2"
              >
                <span>🔐</span>
                <span>Authenticate with Zerodha</span>
              </button>
            </div>

            {/* Manual Token Entry */}
            {showManualEntry && (
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium mb-3">Enter Request Token:</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Request Token (from redirect URL):
                    </label>
                    <input
                      type="text"
                      value={requestToken}
                      onChange={(e) => setRequestToken(e.target.value)}
                      placeholder="Enter request_token here..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={handleAuthenticate}
                      disabled={authenticating || !requestToken.trim()}
                      className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded transition duration-200"
                    >
                      {authenticating ? 'Authenticating...' : 'Complete Authentication'}
                    </button>
                    
                    <button
                      onClick={() => {
                        setShowManualEntry(false);
                        setRequestToken('');
                      }}
                      className="bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded transition duration-200"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Technical Details */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="font-medium text-gray-900 mb-2">🔧 Technical Status:</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">API Key:</span>
              <span className="ml-2 font-mono text-green-600">
                {authStatus?.api_key_configured ? '✅ Configured' : '❌ Missing'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Access Token:</span>
              <span className="ml-2 font-mono text-green-600">
                {authStatus?.access_token_available ? '✅ Available' : '❌ Missing'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Production Mode:</span>
              <span className="ml-2 font-mono text-blue-600">
                {authStatus?.production_mode ? '✅ Enabled' : '❌ Disabled'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Deployment Ready:</span>
              <span className="ml-2 font-mono">
                {authStatus?.deployment_ready ? '✅ Ready' : '⚠️ Pending Auth'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ZerodhaAuthSetup;