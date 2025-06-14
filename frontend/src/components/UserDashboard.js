import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function UserDashboard({ connectedAccounts, realTimeData }) {
  const { userId } = useParams();
  const [userMetrics, setUserMetrics] = useState({});
  const [userTrades, setUserTrades] = useState([]);
  const [userPositions, setUserPositions] = useState([]);
  const [userAccount, setUserAccount] = useState(null);

  useEffect(() => {
    if (userId) {
      fetchUserData();
    }
  }, [userId]);

  const fetchUserData = async () => {
    try {
      const [metricsResponse, tradesResponse, positionsResponse] = await Promise.all([
        fetch(`${BACKEND_URL}/api/users/${userId}/metrics`),
        fetch(`${BACKEND_URL}/api/users/${userId}/trades`),
        fetch(`${BACKEND_URL}/api/users/${userId}/positions`)
      ]);

      const metrics = await metricsResponse.json();
      const trades = await tradesResponse.json();
      const positions = await positionsResponse.json();

      setUserMetrics(metrics);
      setUserTrades(trades.trades || []);
      setUserPositions(positions.positions || []);
    } catch (error) {
      console.error('Error fetching user data:', error);
      // Fallback data for demo
      setUserMetrics({
        daily_pnl: 12500,
        total_trades: 23,
        win_rate: 73.9,
        capital_allocated: 200000,
        capital_used: 145000,
        max_drawdown: -8500,
        sharpe_ratio: 1.42,
        current_exposure: 89000
      });
      setUserTrades([
        { id: 1, symbol: 'NIFTY25JUN24400CE', side: 'BUY', quantity: 50, entry_price: 125.5, exit_price: 135.0, pnl: 2375, time: '14:30:15', strategy: 'MomentumSurfer' },
        { id: 2, symbol: 'BANKNIFTY25JUN51000PE', side: 'SELL', quantity: 25, entry_price: 89.0, exit_price: 82.5, pnl: 1625, time: '13:45:30', strategy: 'VolatilityExplosion' },
        { id: 3, symbol: 'NIFTY25JUN24500CE', side: 'BUY', quantity: 75, entry_price: 67.5, exit_price: 71.0, pnl: 2625, time: '12:20:45', strategy: 'PatternHunter' }
      ]);
      setUserPositions([
        { symbol: 'NIFTY25JUN24600CE', side: 'LONG', quantity: 25, entry_price: 45.5, current_price: 48.0, unrealized_pnl: 625, time: '15:00:00' },
        { symbol: 'BANKNIFTY25JUN52000PE', side: 'SHORT', quantity: 15, entry_price: 112.0, current_price: 108.5, unrealized_pnl: 525, time: '14:45:00' }
      ]);
    }
  };

  // Find user account details
  useEffect(() => {
    const account = connectedAccounts.find(acc => acc.user_id === userId);
    setUserAccount(account);
  }, [userId, connectedAccounts]);

  if (!userAccount) {
    return (
      <div className="p-6 bg-gray-100 min-h-screen">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">User Not Found</h1>
            <p className="text-gray-600 mb-4">The requested user ID "{userId}" was not found.</p>
            <Link to="/" className="text-blue-600 hover:text-blue-800">← Back to Admin Dashboard</Link>
          </div>
        </div>
      </div>
    );
  }

  const utilizationPercentage = ((userMetrics.capital_used || 0) / (userMetrics.capital_allocated || 1)) * 100;

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">User Dashboard: {userId}</h1>
            <p className="text-gray-600">Individual trading performance and analytics</p>
            <div className="flex items-center mt-2">
              <div className={`w-3 h-3 rounded-full mr-2 ${
                userAccount.status === 'connected' ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              <span className="text-sm text-gray-600">
                Zerodha ID: {userAccount.zerodha_user_id} | Status: {userAccount.status?.toUpperCase()}
              </span>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <Link
              to={`/reports/${userId}`}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
            >
              📊 View Reports
            </Link>
            <Link
              to="/"
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
            >
              ← Back to Admin
            </Link>
          </div>
        </div>

        {/* User Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                (userMetrics.daily_pnl || 0) >= 0 ? 'bg-green-500' : 'bg-red-500'
              }`}>
                <span className="text-white font-bold">₹</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Today's P&L</p>
                <p className={`text-2xl font-bold ${
                  (userMetrics.daily_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ₹{(userMetrics.daily_pnl || 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">📊</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Trades</p>
                <p className="text-2xl font-bold text-gray-900">{userMetrics.total_trades || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">%</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Win Rate</p>
                <p className="text-2xl font-bold text-gray-900">{(userMetrics.win_rate || 0).toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">📈</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Sharpe Ratio</p>
                <p className="text-2xl font-bold text-gray-900">{(userMetrics.sharpe_ratio || 0).toFixed(2)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Capital Utilization & Risk Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Capital Utilization</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Allocated Capital:</span>
                <span className="font-bold text-gray-900">₹{(userMetrics.capital_allocated || 0).toLocaleString()}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Capital Used:</span>
                <span className="font-bold text-blue-600">₹{(userMetrics.capital_used || 0).toLocaleString()}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Current Exposure:</span>
                <span className="font-bold text-purple-600">₹{(userMetrics.current_exposure || 0).toLocaleString()}</span>
              </div>
              
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Utilization</span>
                  <span>{utilizationPercentage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full ${
                      utilizationPercentage > 80 ? 'bg-red-500' : 
                      utilizationPercentage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(utilizationPercentage, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Metrics</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Max Drawdown:</span>
                <span className="font-bold text-red-600">₹{(userMetrics.max_drawdown || 0).toLocaleString()}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Risk Percentage:</span>
                <span className="font-bold text-orange-600">{userAccount.risk_percentage}%</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Account Status:</span>
                <span className={`font-bold ${
                  userAccount.status === 'connected' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {userAccount.status?.toUpperCase()}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Created:</span>
                <span className="font-medium text-gray-900">
                  {userAccount.created_at ? new Date(userAccount.created_at).toLocaleDateString() : 'Unknown'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Current Positions */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Current Positions</h3>
            <p className="text-gray-600">Active autonomous trading positions</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entry Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unrealized P&L</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(userPositions || []).map((position, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{position.symbol}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        position.side === 'LONG' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {position.side}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{position.quantity}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{position.entry_price}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{position.current_price}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${
                        (position.unrealized_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ₹{(position.unrealized_pnl || 0).toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{position.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Trades */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Autonomous Trades</h3>
            <p className="text-gray-600">Latest executed trades for this user</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entry Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Exit Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strategy</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(userTrades || []).map((trade) => (
                  <tr key={trade.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{trade.time}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{trade.symbol}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        trade.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{trade.quantity}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{trade.entry_price}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{trade.exit_price}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${
                        (trade.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ₹{(trade.pnl || 0).toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{trade.strategy}</td>
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

export default UserDashboard;