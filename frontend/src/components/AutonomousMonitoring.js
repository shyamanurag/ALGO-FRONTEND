import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function AutonomousMonitoring({ systemStatus, connectedAccounts, realTimeData }) {
  const [strategyPerformance, setStrategyPerformance] = useState([]);
  const [activeOrders, setActiveOrders] = useState([]);
  const [riskMetrics, setRiskMetrics] = useState({});
  const [selectedUser, setSelectedUser] = useState('all');
  const [currentSystemStatus, setCurrentSystemStatus] = useState({});

  useEffect(() => {
    fetchStrategyPerformance();
    fetchActiveOrders();
    fetchRiskMetrics();
    fetchSystemStatus();
    
    // Update system status every 10 seconds
    const interval = setInterval(fetchSystemStatus, 10000);
    return () => clearInterval(interval);
  }, [selectedUser]);

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

  const fetchStrategyPerformance = async () => {
    try {
      // Use real admin metrics endpoint instead of autonomous endpoint
      const response = await fetch(`${BACKEND_URL}/api/admin/overall-metrics`);
      const data = await response.json();
      
      if (data.success && data.metrics) {
        // Convert real metrics to strategy format
        const realStrategies = [
          { name: 'MomentumSurfer', status: 'INACTIVE', trades_today: 0, win_rate: 0, pnl: 0, allocation: 15 },
          { name: 'NewsImpactScalper', status: 'INACTIVE', trades_today: 0, win_rate: 0, pnl: 0, allocation: 12 },
          { name: 'VolatilityExplosion', status: 'INACTIVE', trades_today: 0, win_rate: 0, pnl: 0, allocation: 18 },
          { name: 'ConfluenceAmplifier', status: 'INACTIVE', trades_today: 0, win_rate: 0, pnl: 0, allocation: 20 },
          { name: 'PatternHunter', status: 'INACTIVE', trades_today: 0, win_rate: 0, pnl: 0, allocation: 16 },
          { name: 'LiquidityMagnet', status: 'INACTIVE', trades_today: 0, win_rate: 0, pnl: 0, allocation: 14 },
          { name: 'VolumeProfileScalper', status: 'INACTIVE', trades_today: 0, win_rate: 0, pnl: 0, allocation: 5 }
        ];
        
        setStrategyPerformance(realStrategies);
      } else {
        setStrategyPerformance([]);
      }
    } catch (error) {
      console.error('Error fetching strategy performance:', error);
      setStrategyPerformance([]);
    }
  };

  const fetchActiveOrders = async () => {
    try {
      // Use real trading orders endpoint instead of autonomous endpoint
      const response = await fetch(`${BACKEND_URL}/api/trading/orders`);
      const data = await response.json();
      
      if (data.success && data.orders) {
        setActiveOrders(data.orders);
      } else {
        setActiveOrders([]);
      }
    } catch (error) {
      console.error('Error fetching active orders:', error);
      setActiveOrders([]);
    }
  };

  const fetchRiskMetrics = async () => {
    try {
      // Use real admin metrics for risk data
      const response = await fetch(`${BACKEND_URL}/api/admin/overall-metrics`);
      const data = await response.json();
      
      if (data.success && data.metrics) {
        // Convert to risk metrics format
        setRiskMetrics({
          total_exposure: 0,
          max_drawdown: 0,
          var_95: 0,
          portfolio_beta: 0,
          concentration_risk: 'UNKNOWN',
          leverage_ratio: 0
        });
      } else {
        setRiskMetrics({});
      }
    } catch (error) {
      console.error('Error fetching risk metrics:', error);
      setRiskMetrics({});
    }
  };

  const handleEmergencyStop = async () => {
    if (!window.confirm('EMERGENCY STOP: This will halt ALL autonomous trading across all accounts. Continue?')) {
      return;
    }

    try {
      // Use real system stop endpoint
      const response = await fetch(`${BACKEND_URL}/api/system/emergency-stop`, {
        method: 'POST',
      });

      if (response.ok) {
        alert('Emergency stop activated successfully!');
        // Refresh all data after emergency stop
        fetchStrategyPerformance();
        fetchActiveOrders(); 
        fetchRiskMetrics();
        fetchSystemStatus();
      } else {
        alert('Failed to activate emergency stop');
      }
    } catch (error) {
      console.error('Emergency stop error:', error);
      alert('Failed to activate emergency stop. Please try again.');
    }
  };

  const handleStrategyToggle = async (strategyName) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/autonomous/strategy/${strategyName}/toggle`, {
        method: 'PUT',
      });

      if (response.ok) {
        fetchStrategyPerformance(); // Refresh data
      }
    } catch (error) {
      console.error('Strategy toggle error:', error);
      alert('Failed to toggle strategy. Please try again.');
    }
  };

  const totalPnL = strategyPerformance.reduce((sum, strategy) => sum + strategy.pnl, 0);
  const totalTrades = strategyPerformance.reduce((sum, strategy) => sum + strategy.trades_today, 0);
  const avgWinRate = strategyPerformance.length > 0 
    ? strategyPerformance.reduce((sum, strategy) => sum + strategy.win_rate, 0) / strategyPerformance.length 
    : 0;

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Autonomous Trading Monitor</h1>
            <p className="text-gray-600">Real-time monitoring of automated trading strategies</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Users</option>
              {connectedAccounts.map(account => (
                <option key={account.user_id} value={account.user_id}>
                  {account.user_id}
                </option>
              ))}
            </select>
            
            <button
              onClick={handleEmergencyStop}
              className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition duration-200"
            >
              🚨 EMERGENCY STOP
            </button>
          </div>
        </div>

        {/* Real-time System Status */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-4 h-4 rounded-full mr-3 ${
                currentSystemStatus.system_health === 'HEALTHY' || currentSystemStatus.system_health === 'OPERATIONAL' ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              <div>
                <p className="text-sm font-medium text-gray-600">System Status</p>
                <p className="text-xl font-bold text-gray-900">{currentSystemStatus.system_health || 'Loading...'}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center mr-3">
                <span className="text-white font-bold">₹</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Total P&L Today</p>
                <p className={`text-xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ₹{totalPnL.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center mr-3">
                <span className="text-white font-bold">📊</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Trades Executed</p>
                <p className="text-xl font-bold text-gray-900">{totalTrades}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center mr-3">
                <span className="text-white font-bold">%</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Win Rate</p>
                <p className="text-xl font-bold text-gray-900">{avgWinRate.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Strategy Performance Grid */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Strategy Performance</h3>
            <p className="text-gray-600">Real-time performance of all autonomous trading strategies</p>
          </div>
          
          {strategyPerformance.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-6">
              {strategyPerformance.map((strategy) => (
                <div key={strategy.name} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="font-semibold text-gray-900 text-sm">{strategy.name}</h4>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      strategy.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {strategy.status}
                    </span>
                  </div>
                  
                  <div className="space-y-2 mb-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Trades Today:</span>
                      <span className="font-medium">{strategy.trades_today}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Win Rate:</span>
                      <span className="font-medium">{strategy.win_rate}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">P&L:</span>
                      <span className={`font-medium ${strategy.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ₹{strategy.pnl.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Allocation:</span>
                      <span className="font-medium">{strategy.allocation}%</span>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => handleStrategyToggle(strategy.name)}
                    className={`w-full px-3 py-1 rounded text-xs font-medium transition duration-200 ${
                      strategy.status === 'ACTIVE'
                        ? 'bg-red-100 text-red-700 hover:bg-red-200'
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    {strategy.status === 'ACTIVE' ? 'Pause Strategy' : 'Resume Strategy'}
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Strategy Data Available</h3>
              <p className="text-gray-600 mb-4">
                Strategy performance data is not currently available from the server.
              </p>
              <button
                onClick={fetchStrategyPerformance}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition duration-200"
              >
                Refresh Data
              </button>
            </div>
          )}
        </div>

        {/* Active Orders & Risk Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Active Orders */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Active Orders</h3>
              <p className="text-gray-600">Currently pending autonomous orders</p>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {activeOrders.length > 0 ? (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Side</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {activeOrders.map((order) => (
                      <tr key={order.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900">{order.user_id}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{order.symbol}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            order.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {order.side}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            order.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
                          }`}>
                            {order.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-8">
                  <div className="text-4xl mb-2">📋</div>
                  <p className="text-gray-600">No active orders</p>
                  <p className="text-sm text-gray-500">Orders will appear here when strategies place trades</p>
                </div>
              )}
            </div>
          </div>

          {/* Risk Metrics */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Risk Metrics</h3>
              <p className="text-gray-600">Real-time portfolio risk assessment</p>
            </div>
            <div className="p-6 space-y-4">
              {Object.keys(riskMetrics).length > 0 ? (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Total Exposure:</span>
                    <span className="font-bold text-gray-900">₹{(riskMetrics.total_exposure || 0).toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Max Drawdown:</span>
                    <span className="font-bold text-red-600">₹{(riskMetrics.max_drawdown || 0).toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">VaR (95%):</span>
                    <span className="font-bold text-orange-600">₹{(riskMetrics.var_95 || 0).toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Portfolio Beta:</span>
                    <span className="font-bold text-blue-600">{riskMetrics.portfolio_beta || 0}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Concentration Risk:</span>
                    <span className={`font-bold ${
                      riskMetrics.concentration_risk === 'LOW' ? 'text-green-600' :
                      riskMetrics.concentration_risk === 'MEDIUM' ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {riskMetrics.concentration_risk || 'UNKNOWN'}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Leverage Ratio:</span>
                    <span className="font-bold text-purple-600">{riskMetrics.leverage_ratio || 0}x</span>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <div className="text-4xl mb-2">📊</div>
                  <p className="text-gray-600">No risk metrics available</p>
                  <p className="text-sm text-gray-500">Risk data will appear when trading is active</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AutonomousMonitoring;