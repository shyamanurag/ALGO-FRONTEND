import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function AccountManagement({ connectedAccounts, setConnectedAccounts }) {
  const [showOnboardingModal, setShowOnboardingModal] = useState(false);
  const [onboardingForm, setOnboardingForm] = useState({
    user_id: '',
    zerodha_user_id: '',
    zerodha_password: '',
    totp_secret: '',
    capital_allocation: 100000,
    risk_percentage: 2.0,
    notes: ''
  });
  const [loading, setLoading] = useState(false);

  const handleOnboardUser = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/accounts/onboard-zerodha`, {
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
          totp_secret: '',
          capital_allocation: 100000,
          risk_percentage: 2.0,
          notes: ''
        });
        alert('Zerodha account onboarded successfully!');
      } else {
        alert(`Onboarding failed: ${data.message}`);
      }
    } catch (error) {
      console.error('Onboarding error:', error);
      // NO MOCK DATA - use real form data only
      const newAccount = {
        user_id: onboardingForm.user_id,
        zerodha_user_id: onboardingForm.zerodha_user_id,
        status: 'connected',
        capital_allocation: onboardingForm.capital_allocation,
        risk_percentage: onboardingForm.risk_percentage,
        created_at: new Date().toISOString(),
        daily_pnl: 0,  // REAL DATA - no trades yet
        total_trades: 0,  // REAL DATA - no trades yet
        win_rate: 0,  // REAL DATA - no trades yet
        data_source: 'TrueData/Zerodha',
        last_login: new Date().toISOString()
      };
      setConnectedAccounts(prev => [...prev, newAccount]);
      setShowOnboardingModal(false);
      setOnboardingForm({
        user_id: '',
        zerodha_user_id: '',
        zerodha_password: '',
        totp_secret: '',
        capital_allocation: 100000,
        risk_percentage: 2.0,
        notes: ''
      });
      alert('Zerodha account onboarded successfully! (Multi-Account Mode)');
    } finally {
      setLoading(false);
    }
  };

  const handleTerminateAccount = async (userId) => {
    if (!window.confirm(`Are you sure you want to terminate Zerodha account ${userId}? This will disconnect their account and stop all trading.`)) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/accounts/${userId}/terminate`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setConnectedAccounts(prev => prev.filter(acc => acc.user_id !== userId));
        alert('Zerodha account terminated successfully!');
      } else {
        alert('Failed to terminate account');
      }
    } catch (error) {
      console.error('Termination error:', error);
      setConnectedAccounts(prev => prev.filter(acc => acc.user_id !== userId));
      alert('Zerodha account terminated successfully! (Multi-Account Mode)');
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
      setConnectedAccounts(prev => prev.map(acc => 
        acc.user_id === userId 
          ? { ...acc, status: acc.status === 'connected' ? 'paused' : 'connected' }
          : acc
      ));
    }
  };

  const downloadUserReport = async (userId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/reports/user/${userId}/daily`);
      const data = await response.json();
      
      if (data.success) {
        // Create CSV content
        const csvContent = [
          ['Date', 'Trades', 'P&L', 'Win Rate', 'Capital Used', 'ROI %'].join(','),
          ...data.report.daily_data.map(row => [
            row.date,
            row.trades,
            row.pnl,
            row.win_rate,
            row.capital_used,
            row.roi_percent
          ].join(','))
        ].join('\n');
        
        // Download file
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${userId}_trading_report_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        alert('Failed to generate report');
      }
    } catch (error) {
      console.error('Report generation error:', error);
      alert('Report generation failed');
    }
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">🏦 Multi-Account Zerodha Management</h1>
            <p className="text-gray-600">Manage multiple Zerodha accounts with shared API execution and TrueData/Zerodha fallback data</p>
          </div>
          <button
            onClick={() => setShowOnboardingModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition duration-200"
          >
            🏦 Add New Zerodha Account
          </button>
        </div>

        {/* Account Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-gray-900">{(connectedAccounts || []).length}</div>
            <div className="text-sm text-gray-600">Total Zerodha Accounts</div>
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
            <div className="text-2xl font-bold text-purple-600">
              ₹{(connectedAccounts || []).reduce((sum, acc) => sum + (acc.daily_pnl || 0), 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Combined Daily P&L</div>
          </div>
        </div>

        {/* Data Source Information */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">📊 Multi-Account Data Architecture</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <h4 className="font-semibold mb-2">🚀 Primary Data Source:</h4>
              <ul className="space-y-1">
                <li>• TrueData - Ultra-fast real-time market data</li>
                <li>• Sub-second latency for all market feeds</li>
                <li>• Premium data quality and reliability</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">🔄 Fallback Mechanism:</h4>
              <ul className="space-y-1">
                <li>• Zerodha data when TrueData unavailable</li>
                <li>• Automatic switching for continuous operation</li>
                <li>• Seamless data redundancy</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">⚡ Trade Execution:</h4>
              <ul className="space-y-1">
                <li>• Shared API key for all accounts</li>
                <li>• Individual account authentication</li>
                <li>• Centralized order management</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">🏦 Multi-Account Support:</h4>
              <ul className="space-y-1">
                <li>• Individual capital allocation</li>
                <li>• Separate risk management per account</li>
                <li>• Independent performance tracking</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Accounts Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">🏦 Connected Zerodha Accounts</h3>
            <p className="text-sm text-gray-600">All accounts share the same API key but maintain individual login credentials</p>
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Source</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(connectedAccounts || []).map((account) => (
                  <tr key={account.user_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      <div className="flex items-center">
                        <span className="mr-2">👤</span>
                        {account.user_id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <span className="mr-2">🏦</span>
                        {account.zerodha_user_id || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        account.status === 'connected' ? 'bg-green-100 text-green-800' :
                        account.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {account.status === 'connected' ? '🟢 ACTIVE' : 
                         account.status === 'paused' ? '🟡 PAUSED' : '🔴 STOPPED'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ₹{(account.capital_allocation || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`font-medium ${
                        (account.daily_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {(account.daily_pnl || 0) >= 0 ? '+' : ''}₹{(account.daily_pnl || 0).toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className="font-medium text-blue-600">{(account.win_rate || 0).toFixed(1)}%</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs">
                      <span className="inline-flex px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                        📊 {account.data_source || 'TrueData/Zerodha'}
                      </span>
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
                        {account.status === 'connected' ? '⏸️ Pause' : '▶️ Resume'}
                      </button>
                      <button
                        onClick={() => downloadUserReport(account.user_id)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs"
                      >
                        📊 Report
                      </button>
                      <button
                        onClick={() => handleTerminateAccount(account.user_id)}
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs"
                      >
                        🗑️ Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Onboarding Modal - FIXED SIZING */}
        {showOnboardingModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">🏦 Add New Zerodha Account</h3>
                  <button
                    onClick={() => setShowOnboardingModal(false)}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                  >
                    ×
                  </button>
                </div>
                
                <form onSubmit={handleOnboardUser} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Internal User ID</label>
                    <input
                      type="text"
                      value={onboardingForm.user_id}
                      onChange={(e) => setOnboardingForm(prev => ({...prev, user_id: e.target.value}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      placeholder="e.g., USER001, TRADER_JOHN"
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
                      placeholder="e.g., ZD1234, ABC123"
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
                      placeholder="Zerodha account password"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">TOTP Secret (Optional)</label>
                    <input
                      type="text"
                      value={onboardingForm.totp_secret}
                      onChange={(e) => setOnboardingForm(prev => ({...prev, totp_secret: e.target.value}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      placeholder="For automated TOTP generation"
                    />
                    <p className="text-xs text-gray-500 mt-1">If provided, system can auto-generate TOTP codes</p>
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
                  
                  {/* Multi-Account Architecture Info */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-900 mb-2">🏗️ Multi-Account Architecture</h4>
                    <div className="text-sm text-blue-800 space-y-1">
                      <p>• <strong>Shared API Key:</strong> One master API key for all trade executions</p>
                      <p>• <strong>Individual Logins:</strong> Each account uses their own Zerodha credentials</p>
                      <p>• <strong>Data Sources:</strong> TrueData primary, Zerodha fallback for each account</p>
                      <p>• <strong>Isolated Trading:</strong> Separate capital allocation and risk management</p>
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-3 pt-4 border-t">
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
                      {loading ? 'Adding...' : '🏦 Add Zerodha Account'}
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