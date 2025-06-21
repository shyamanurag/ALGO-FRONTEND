import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const LiveAutonomousStatus = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [autonomousStatus, setAutonomousStatus] = useState(null);
  const [tradingSignals, setTradingSignals] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch system status
      const systemResponse = await fetch(`${BACKEND_URL}/api/system/status`);
      if (systemResponse.ok) {
        const systemData = await systemResponse.json();
        // Fix: Extract data from nested response structure
        setSystemStatus(systemData.data || systemData);
      }

      // Fetch autonomous status  
      const autonomousResponse = await fetch(`${BACKEND_URL}/api/autonomous/status`);
      if (autonomousResponse.ok) {
        const autonomousData = await autonomousResponse.json();
        // Fix: Extract data from nested response structure
        setAutonomousStatus(autonomousData.data || autonomousData);
      }

      // Fetch trading signals
      const signalsResponse = await fetch(`${BACKEND_URL}/api/trading-signals/active`);
      if (signalsResponse.ok) {
        const signalsData = await signalsResponse.json();
        setTradingSignals(signalsData.signals || []);
      }

      // Fetch system metrics
      const metricsResponse = await fetch(`${BACKEND_URL}/api/autonomous/system-metrics`);
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setSystemMetrics(metricsData);
      }

      setLastUpdate(new Date());
    } catch (err) {
      setError('Failed to fetch system data: ' + err.message);
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const activateAutonomousTrading = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/resume-trading`, {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('Autonomous trading activated!');
        fetchAllData();
      } else {
        const error = await response.text();
        alert(`Failed to activate: ${error}`);
      }
    } catch (err) {
      alert('Error activating trading: ' + err.message);
    }
  };

  const connectTrueData = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/truedata/connect`, {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('TrueData connection initiated!');
        fetchAllData();
      } else {
        const error = await response.text();
        alert(`Failed to connect: ${error}`);
      }
    } catch (err) {
      alert('Error connecting TrueData: ' + err.message);
    }
  };

  if (loading && !systemStatus) {
    return (
      <div className="p-8 text-center">
        <div className="text-4xl mb-4">🔄</div>
        <h2 className="text-xl font-bold">Loading System Status...</h2>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">🤖 LIVE Autonomous Trading System</h1>
          <p className="text-gray-600">Real-time status of the autonomous trading platform</p>
          <p className="text-sm text-gray-500">Last updated: {lastUpdate.toLocaleTimeString()}</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 font-medium">⚠️ {error}</p>
          </div>
        )}

        {/* Main System Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* System Health */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-4 h-4 rounded-full mr-3 ${
                systemStatus?.system_health === 'OPERATIONAL_RESUMED' || systemStatus?.system_health === 'HEALTHY' ? 'bg-green-400' :
                systemStatus?.system_health === 'DEGRADED' || systemStatus?.system_health === 'ERROR_MD_INIT' ? 'bg-yellow-400' : 'bg-red-400'
              }`}></div>
              <div>
                <p className="text-sm font-medium text-gray-600">System Health</p>
                <p className="text-xl font-bold text-gray-900">
                  {systemStatus?.system_health || 'UNKNOWN'}
                </p>
              </div>
            </div>
          </div>

          {/* Autonomous Trading Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-4 h-4 rounded-full mr-3 ${
                autonomousStatus?.trading_active ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              <div>
                <p className="text-sm font-medium text-gray-600">Autonomous Trading</p>
                <p className="text-xl font-bold text-gray-900">
                  {autonomousStatus?.trading_active ? 'ACTIVE' : 'INACTIVE'}
                </p>
              </div>
            </div>
          </div>

          {/* TrueData Connection */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-4 h-4 rounded-full mr-3 ${
                systemStatus?.status?.truedata?.connected ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              <div>
                <p className="text-sm font-medium text-gray-600">TrueData</p>
                <p className="text-xl font-bold text-gray-900">
                  {systemStatus?.status?.truedata?.connected ? 'CONNECTED' : 'DISCONNECTED'}
                </p>
              </div>
            </div>
          </div>

          {/* Strategies Active */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-400 rounded-full mr-3"></div>
              <div>
                <p className="text-sm font-medium text-gray-600">Active Strategies</p>
                <p className="text-xl font-bold text-gray-900">
                  {autonomousStatus?.strategies_active || 0}/{autonomousStatus?.total_strategies || 7}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* System Components Health */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">System Components</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {autonomousStatus?.system_health && Object.entries(autonomousStatus.system_health).map(([component, status]) => (
                <div key={component} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium capitalize">{component.replace('_', ' ')}</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    status === 'CONNECTED' || status === 'ACTIVE' || status === 'RUNNING' ? 'bg-green-100 text-green-800' :
                    status === 'DEGRADED' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Control Actions */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">🎛️ System Controls</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={connectTrueData}
                disabled={systemStatus?.status?.truedata?.connected}
                className={`px-6 py-3 rounded-lg font-medium transition ${
                  systemStatus?.status?.truedata?.connected
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                🔗 {systemStatus?.status?.truedata?.connected ? 'TrueData Connected' : 'Connect TrueData'}
              </button>

              <button
                onClick={activateAutonomousTrading}
                disabled={autonomousStatus?.trading_active}
                className={`px-6 py-3 rounded-lg font-medium transition ${
                  autonomousStatus?.trading_active
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                🤖 {autonomousStatus?.trading_active ? 'Trading Active' : 'Activate Trading'}
              </button>

              <button
                onClick={fetchAllData}
                className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition"
              >
                🔄 Refresh Status
              </button>
            </div>
          </div>
        </div>

        {/* Trading Signals */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">⚡ Live Trading Signals ({tradingSignals.length})</h3>
          </div>
          <div className="overflow-x-auto">
            {tradingSignals.length > 0 ? (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Strategy</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quality</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Entry Price</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Generated</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {tradingSignals.slice(0, 10).map((signal, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                          {signal.strategy_name}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{signal.symbol}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          signal.action === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {signal.action}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`font-medium ${
                          signal.quality_score >= 8 ? 'text-green-600' : 
                          signal.quality_score >= 6 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {(signal.quality_score || 0).toFixed(2)}/10
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-900">₹{(signal.entry_price || 0).toLocaleString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {signal.generated_at ? new Date(signal.generated_at).toLocaleString() : 'Unknown'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📊</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No Active Signals</h3>
                <p className="text-gray-600">
                  {autonomousStatus?.trading_active 
                    ? 'System is active but no signals generated yet. Signals will appear when market conditions meet strategy criteria.'
                    : 'Activate autonomous trading to start generating signals.'
                  }
                </p>
              </div>
            )}
          </div>
        </div>

        {/* System Health Summary */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">📊 System Summary</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-3">System Status</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Market Status:</span>
                    <span className="font-medium">{systemStatus?.status?.market_status || 'UNKNOWN'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Paper Trading:</span>
                    <span className="font-medium">{systemStatus?.status?.paper_trading ? 'ON' : 'OFF'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Data Source:</span>
                    <span className="font-medium">{systemStatus?.status?.data_source || 'NO_DATA'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">System Uptime:</span>
                    <span className="font-medium">{autonomousStatus?.uptime || 'Unknown'}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Real vs Mock Data</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">TrueData Status:</span>
                    <span className={`font-medium ${
                      systemStatus?.status?.truedata?.connected ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {systemStatus?.status?.truedata?.connected ? 'REAL DATA' : 'NO CONNECTION'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Database:</span>
                    <span className={`font-medium ${
                      autonomousStatus?.system_health?.database === 'CONNECTED' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {autonomousStatus?.system_health?.database || 'UNKNOWN'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Signals Generated:</span>
                    <span className="font-medium text-blue-600">{tradingSignals.length} signals</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Last Signal:</span>
                    <span className="font-medium">
                      {tradingSignals.length > 0 
                        ? new Date(tradingSignals[0].generated_at).toLocaleTimeString()
                        : 'None'
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveAutonomousStatus;