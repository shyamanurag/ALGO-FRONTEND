import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import LiveMarketDataStatus from './LiveMarketDataStatus';
import LiveIndices from './LiveIndices';
import LiveIndicesHeader from './LiveIndicesHeader';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function AdminDashboard({ systemStatus, connectedAccounts, realTimeData, onTrueDataConnect, onTrueDataDisconnect }) {
  const [overallMetrics, setOverallMetrics] = useState({});
  const [recentTrades, setRecentTrades] = useState([]);
  const [topPerformers, setTopPerformers] = useState([]);
  const [currentSystemStatus, setCurrentSystemStatus] = useState({});
  const [zerodhaStatus, setZerodhaStatus] = useState({ connected: false, status: 'disconnected' });
  const [truedataStatus, setTruedataStatus] = useState({ connected: false, status: 'disconnected' });

  useEffect(() => {
    fetchOverallMetrics();
    fetchRecentTrades();
    fetchSystemStatus();
    fetchZerodhaStatus();
    fetchTruedataStatus();
    
    // Update system status every 10 seconds
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchZerodhaStatus();
      fetchTruedataStatus();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchTruedataStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/truedata/status`);
      const data = await response.json();
      if (data.success) {
        setTruedataStatus(data);
      }
    } catch (error) {
      console.error('Error fetching TrueData status:', error);
      setTruedataStatus({ connected: false, status: 'error' });
    }
  };

  const fetchZerodhaStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/zerodha/status`);
      const data = await response.json();
      if (data.success) {
        setZerodhaStatus(data);
      }
    } catch (error) {
      console.error('Error fetching Zerodha status:', error);
      setZerodhaStatus({ connected: false, status: 'error' });
    }
  };

  const handleZerodhaAuth = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/zerodha/auth-url`);
      const data = await response.json();
      
      if (data.success && data.login_url) {
        // Open Zerodha OAuth in popup window
        const popup = window.open(
          data.login_url, 
          'zerodha-auth', 
          'width=500,height=700,scrollbars=yes,resizable=yes'
        );
        
        // Check if popup was blocked
        if (!popup) {
          alert('❌ Popup blocked! Please allow popups and try again.');
          return;
        }
        
        // Monitor popup closure
        const checkClosed = setInterval(() => {
          if (popup.closed) {
            clearInterval(checkClosed);
            // Refresh Zerodha status after auth
            setTimeout(fetchZerodhaStatus, 1000);
          }
        }, 1000);
        
      } else {
        alert(`❌ ${data.message}`);
      }
    } catch (error) {
      console.error('Error initiating Zerodha auth:', error);
      alert('❌ Error connecting to Zerodha. Please try again.');
    }
  };

  const handleZerodhaDisconnect = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/zerodha/disconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        alert('✅ Zerodha disconnected successfully');
        setZerodhaStatus({ connected: false, status: 'disconnected' });
      } else {
        alert(`❌ ${data.message}`);
      }
    } catch (error) {
      console.error('Error disconnecting Zerodha:', error);
      alert('❌ Error disconnecting Zerodha. Please try again.');
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/system/status`);
      const data = await response.json();
      if (data.success) {
        setCurrentSystemStatus(data.status);
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
      setCurrentSystemStatus({ system_health: 'ERROR', autonomous_trading: false });
    }
  };

  useEffect(() => {
    fetchOverallMetrics();
    fetchRecentTrades();
  }, []);

  const fetchOverallMetrics = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/overall-metrics`);
      const data = await response.json();
      setOverallMetrics(data);
    } catch (error) {
      console.error('Error fetching overall metrics:', error);
      // No fallback data - let component handle empty state
      setOverallMetrics({});
    }
  };

  const fetchRecentTrades = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/recent-trades`);
      const data = await response.json();
      setRecentTrades(data.trades || []);
    } catch (error) {
      console.error('Error fetching recent trades:', error);
      // No fallback data - let component handle empty state
      setRecentTrades([]);
    }
  };

  const activeAccounts = connectedAccounts.filter(acc => acc.status === 'connected').length;
  const disconnectedAccounts = connectedAccounts.filter(acc => acc.status === 'disconnected').length;

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600">Multi-User Autonomous Trading Platform Overview</p>
        </div>

        {/* System Status Banner */}
        <div className={`mb-6 p-4 rounded-lg border-l-4 ${
          currentSystemStatus.system_health === 'OPERATIONAL' || currentSystemStatus.system_health === 'HEALTHY' ? 'bg-green-50 border-green-400' :
          currentSystemStatus.system_health === 'WARNING' ? 'bg-yellow-50 border-yellow-400' :
          'bg-red-50 border-red-400'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Elite Autonomous Trading System - {currentSystemStatus.system_health || 'UNKNOWN'}
              </h3>
              <p className="text-gray-700">
                Autonomous trading is {currentSystemStatus.autonomous_trading ? 'ACTIVE' : 'INACTIVE'} | 
                Paper Trading: {currentSystemStatus.paper_trading ? 'ON' : 'OFF'}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Uptime: {currentSystemStatus.uptime || 'Unknown'}</div>
              <div className="text-sm text-gray-600">Last Update: {currentSystemStatus.last_update || new Date().toLocaleTimeString()}</div>
            </div>
          </div>
        </div>

        {/* System Status Overview */}
        <div className="mb-6 bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">⚡ System Status</h2>
            <div className="flex items-center space-x-4">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                currentSystemStatus.system_health === 'HEALTHY' ? 'bg-green-100 text-green-800' :
                currentSystemStatus.system_health === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {currentSystemStatus.system_health || 'UNKNOWN'}
              </span>
              <button 
                onClick={fetchSystemStatus}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                Refresh Status
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Trading Status</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Autonomous Trading:</span>
                  <span className={`font-medium ${currentSystemStatus.autonomous_trading ? 'text-green-600' : 'text-red-600'}`}>
                    {currentSystemStatus.autonomous_trading ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Data Connections Panel */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">🔌 Data Connections</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* TrueData Connection */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-bold text-gray-900">📡 TrueData</h3>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  currentSystemStatus.truedata_connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {currentSystemStatus.truedata_connected ? '🟢 Connected' : '🔴 Disconnected'}
                </span>
              </div>
              <p className="text-gray-600 text-sm mb-4">Real-time market data feed</p>
              <div className="flex space-x-2">
                {!currentSystemStatus.truedata_connected ? (
                  <button
                    onClick={onTrueDataConnect}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm transition duration-200"
                  >
                    🚀 Connect TrueData
                  </button>
                ) : (
                  <button
                    onClick={onTrueDataDisconnect}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm transition duration-200"
                  >
                    🔌 Disconnect
                  </button>
                )}
              </div>
            </div>

            {/* Zerodha Connection */}
            <div className="bg-gradient-to-r from-orange-50 to-red-50 p-4 rounded-lg border">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-bold text-gray-900">🔐 Zerodha</h3>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  zerodhaStatus.connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {zerodhaStatus.connected ? '🟢 Connected' : '🔴 Disconnected'}
                </span>
              </div>
              <p className="text-gray-600 text-sm mb-2">Trading broker authentication</p>
              {zerodhaStatus.token_preview && (
                <p className="text-xs text-gray-500 mb-3">Token: {zerodhaStatus.token_preview}</p>
              )}
              <div className="flex space-x-2">
                {!zerodhaStatus.connected ? (
                  <button
                    onClick={handleZerodhaAuth}
                    className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded text-sm transition duration-200"
                  >
                    🚀 Authenticate Zerodha
                  </button>
                ) : (
                  <button
                    onClick={handleZerodhaDisconnect}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm transition duration-200"
                  >
                    🔌 Disconnect
                  </button>
                )}
              </div>
              
              {/* Configuration Status */}
              <div className="mt-3 text-xs text-gray-500">
                <div>API Key: {zerodhaStatus.api_key_configured ? '✅ Configured' : '❌ Not Set'}</div>
                <div>API Secret: {zerodhaStatus.api_secret_configured ? '✅ Configured' : '❌ Not Set'}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Live Market Data Status */}
        <LiveMarketDataStatus />

        {/* Live Market Indices */}
        <LiveIndices />

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Connected Accounts</p>
                <p className="text-2xl font-bold text-gray-900">{activeAccounts}/{connectedAccounts.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">₹</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Capital</p>
                <p className="text-2xl font-bold text-gray-900">₹{(overallMetrics.total_capital || 0).toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                (overallMetrics.daily_pnl || 0) >= 0 ? 'bg-green-500' : 'bg-red-500'
              }`}>
                <span className="text-white font-bold">📈</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Today's P&L</p>
                <p className={`text-2xl font-bold ${
                  (overallMetrics.daily_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ₹{(overallMetrics.daily_pnl || 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">⚡</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Trades Today</p>
                <p className="text-2xl font-bold text-gray-900">{overallMetrics.total_trades_today || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Account Status & Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Account Status Overview */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Status</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
                  <span className="font-medium">Active Accounts</span>
                </div>
                <span className="font-bold text-green-600">{activeAccounts}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-red-400 rounded-full mr-3"></div>
                  <span className="font-medium">Disconnected</span>
                </div>
                <span className="font-bold text-red-600">{disconnectedAccounts}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-blue-400 rounded-full mr-3"></div>
                  <span className="font-medium">Win Rate</span>
                </div>
                <span className="font-bold text-blue-600">{overallMetrics.win_rate || 0}%</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-4">
              <Link
                to="/accounts"
                className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg text-center transition duration-200"
              >
                <div className="text-xl mb-2">👥</div>
                <div className="font-medium">Manage Accounts</div>
              </Link>
              
              <Link
                to="/autonomous-monitoring"
                className="bg-green-600 hover:bg-green-700 text-white p-4 rounded-lg text-center transition duration-200"
              >
                <div className="text-xl mb-2">⚡</div>
                <div className="font-medium">Monitor Trading</div>
              </Link>
              
              <Link
                to="/elite-recommendations"
                className="bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-lg text-center transition duration-200"
              >
                <div className="text-xl mb-2">🎯</div>
                <div className="font-medium">Elite Advisory</div>
              </Link>
              
              <button className="bg-orange-600 hover:bg-orange-700 text-white p-4 rounded-lg text-center transition duration-200">
                <div className="text-xl mb-2">⚙️</div>
                <div className="font-medium">System Config</div>
              </button>
            </div>
          </div>
        </div>

        {/* Recent Autonomous Trades */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Autonomous Trades</h3>
            <p className="text-gray-600">Latest automated trades across all connected accounts</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(recentTrades || []).map((trade) => (
                  <tr key={trade.id || Math.random()} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{trade.time || 'N/A'}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link 
                        to={`/user/${trade.user_id || 'unknown'}`}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {trade.user_id || 'Unknown'}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{trade.symbol || 'N/A'}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        (trade.side || '').toUpperCase() === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {trade.side || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{trade.quantity || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{(trade.price || 0)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${
                        (trade.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ₹{(trade.pnl || 0).toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;