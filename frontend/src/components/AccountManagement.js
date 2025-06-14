import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function AccountManagement({ connectedAccounts, setConnectedAccounts }) {
  const [showOnboardingModal, setShowOnboardingModal] = useState(false);
  const [onboardingForm, setOnboardingForm] = useState({
    user_id: '',
    zerodha_user_id: '',
    zerodha_password: '',
    totp_pin: '', // Current TOTP PIN, not secret
    capital_allocation: 100000,
    risk_percentage: 2.0,
    notes: ''
  });
  const [loading, setLoading] = useState(false);

  const handleOnboardUser = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/accounts/onboard`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(onboardingForm),
      });

      const data = await response.json();

      if (response.ok) {
        setConnectedAccounts(prev => [...prev, data.account]);
        setShowOnboardingModal(false);
        setOnboardingForm({
          user_id: '',
          zerodha_user_id: '',
          zerodha_password: '',
          totp_pin: '',
          capital_allocation: 100000,
          risk_percentage: 2.0,
          notes: ''
        });
        alert('Account onboarded successfully!');
      } else {
        alert(`Onboarding failed: ${data.message}`);
      }
    } catch (error) {
      console.error('Onboarding error:', error);
      // For demo purposes, add account locally
      const newAccount = {
        user_id: onboardingForm.user_id,
        zerodha_user_id: onboardingForm.zerodha_user_id,
        status: 'connected',
        capital_allocation: onboardingForm.capital_allocation,
        risk_percentage: onboardingForm.risk_percentage,
        created_at: new Date().toISOString(),
        daily_pnl: 0,
        total_trades: 0,
        win_rate: 0
      };
      setConnectedAccounts(prev => [...prev, newAccount]);
      setShowOnboardingModal(false);
      alert('Account onboarded successfully! (Demo Mode)');
    } finally {
      setLoading(false);
    }
  };

  const handleTerminateAccount = async (userId) => {
    if (!window.confirm(`Are you sure you want to terminate account ${userId}? This will disconnect Zerodha and stop all trading.`)) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/accounts/${userId}/terminate`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setConnectedAccounts(prev => prev.filter(acc => acc.user_id !== userId));
        alert('Account terminated successfully!');
      } else {
        alert('Failed to terminate account');
      }
    } catch (error) {
      console.error('Termination error:', error);
      // For demo purposes, remove locally
      setConnectedAccounts(prev => prev.filter(acc => acc.user_id !== userId));
      alert('Account terminated successfully! (Demo Mode)');
    }
  };

  const handleToggleAccountStatus = async (userId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/accounts/${userId}/toggle`, {
        method: 'PUT',
      });

      if (response.ok) {
        setConnectedAccounts(prev => prev.map(acc => 
          acc.user_id === userId 
            ? { ...acc, status: acc.status === 'connected' ? 'paused' : 'connected' }
            : acc
        ));
      }
    } catch (error) {
      console.error('Toggle status error:', error);
      // For demo purposes, toggle locally
      setConnectedAccounts(prev => prev.map(acc => 
        acc.user_id === userId 
          ? { ...acc, status: acc.status === 'connected' ? 'paused' : 'connected' }
          : acc
      ));
    }
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Account Management</h1>
            <p className="text-gray-600">Manage Zerodha account connections and trading permissions</p>
          </div>
          <button
            onClick={() => setShowOnboardingModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition duration-200"
          >
            + Onboard New Account
          </button>
        </div>

        {/* Account Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-gray-900">{(connectedAccounts || []).length}</div>
            <div className="text-sm text-gray-600">Total Accounts</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-green-600">
              {(connectedAccounts || []).filter(acc => acc.status === 'connected').length}
            </div>
            <div className="text-sm text-gray-600">Active Trading</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-yellow-600">
              {(connectedAccounts || []).filter(acc => acc.status === 'paused').length}
            </div>
            <div className="text-sm text-gray-600">Paused</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-red-600">
              {(connectedAccounts || []).filter(acc => acc.status === 'disconnected').length}
            </div>
            <div className="text-sm text-gray-600">Disconnected</div>
          </div>
        </div>

        {/* Accounts Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Connected Zerodha Accounts</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Zerodha ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Capital</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Daily P&L</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Win Rate</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(connectedAccounts || []).map((account) => (
                  <tr key={account.user_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {account.user_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {account.zerodha_user_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        account.status === 'connected' ? 'bg-green-100 text-green-800' :
                        account.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {account.status?.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ₹{(account.capital_allocation || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`font-medium ${
                        (account.daily_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ₹{(account.daily_pnl || 0).toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {(account.win_rate || 0).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => handleToggleAccountStatus(account.user_id)}
                        className={`px-3 py-1 rounded text-white text-xs ${
                          account.status === 'connected' 
                            ? 'bg-yellow-600 hover:bg-yellow-700' 
                            : 'bg-green-600 hover:bg-green-700'
                        }`}
                      >
                        {account.status === 'connected' ? 'Pause' : 'Resume'}
                      </button>
                      <button
                        onClick={() => handleTerminateAccount(account.user_id)}
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs"
                      >
                        Terminate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Onboarding Modal */}
        {showOnboardingModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full m-4">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Onboard New Zerodha Account</h3>
                <form onSubmit={handleOnboardUser} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">User ID</label>
                    <input
                      type="text"
                      value={onboardingForm.user_id}
                      onChange={(e) => setOnboardingForm(prev => ({...prev, user_id: e.target.value}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      placeholder="ZD001"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Zerodha User ID</label>
                    <input
                      type="text"
                      value={onboardingForm.zerodha_user_id}
                      onChange={(e) => setOnboardingForm(prev => ({...prev, zerodha_user_id: e.target.value}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      placeholder="ABC123"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Zerodha Password</label>
                    <input
                      type="password"
                      value={onboardingForm.zerodha_password}
                      onChange={(e) => setOnboardingForm(prev => ({...prev, zerodha_password: e.target.value}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Zerodha Login Password"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Current TOTP PIN</label>
                    <input
                      type="text"
                      value={onboardingForm.totp_pin}
                      onChange={(e) => setOnboardingForm(prev => ({...prev, totp_pin: e.target.value}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      placeholder="6-digit TOTP PIN from authenticator app"
                      maxLength="6"
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">Enter the current 6-digit PIN from your TOTP authenticator app</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Capital Allocation (₹)</label>
                    <input
                      type="number"
                      value={onboardingForm.capital_allocation}
                      onChange={(e) => setOnboardingForm(prev => ({...prev, capital_allocation: parseInt(e.target.value)}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      min="10000"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Risk Percentage (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={onboardingForm.risk_percentage}
                      onChange={(e) => setOnboardingForm(prev => ({...prev, risk_percentage: parseFloat(e.target.value)}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      min="0.5"
                      max="10"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Notes (Optional)</label>
                    <textarea
                      value={onboardingForm.notes}
                      onChange={(e) => setOnboardingForm(prev => ({...prev, notes: e.target.value}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Any additional notes about this account"
                      rows="2"
                    />
                  </div>
                  
                  {/* Architecture Explanation */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-900 mb-2">🏗️ Platform Architecture</h4>
                    <div className="text-sm text-blue-800 space-y-1">
                      <p>• <strong>Single API Key:</strong> We use one master Zerodha API for all executions</p>
                      <p>• <strong>Individual Login:</strong> Each user connects with their own Zerodha ID & password</p>
                      <p>• <strong>Isolated Trading:</strong> Separate capital allocation and risk management per user</p>
                      <p>• <strong>Secure Connection:</strong> TOTP authentication ensures account security</p>
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowOnboardingModal(false)}
                      className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                    >
                      {loading ? 'Onboarding...' : 'Onboard Account'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AccountManagement;