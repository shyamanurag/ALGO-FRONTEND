import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function UserReports({ connectedAccounts, realTimeData }) {
  const { userId } = useParams();
  const [reportType, setReportType] = useState('daily');
  const [reportData, setReportData] = useState({});
  const [performanceChart, setPerformanceChart] = useState([]);
  const [strategyBreakdown, setStrategyBreakdown] = useState([]);
  const [detailedTrades, setDetailedTrades] = useState([]);
  const [tradeFilter, setTradeFilter] = useState('today');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (userId) {
      fetchReportData();
      fetchDetailedTrades();
      fetchStrategyBreakdown();
    }
  }, [userId, reportType, tradeFilter]);

  const fetchReportData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${userId}/reports?type=${reportType}`);
      if (response.ok) {
        const data = await response.json();
        setReportData(data);
        setPerformanceChart(data.performance_chart || []);
      } else {
        // For production - show empty state instead of fallback data
        setReportData({
          summary: {
            total_trades: 0,
            winning_trades: 0,
            losing_trades: 0,
            win_rate: 0,
            total_pnl: 0,
            gross_profit: 0,
            gross_loss: 0,
            max_profit: 0,
            max_loss: 0,
            avg_profit: 0,
            avg_loss: 0,
            profit_factor: 0,
            max_drawdown: 0,
            sharpe_ratio: 0,
            sortino_ratio: 0
          }
        });
        setPerformanceChart([]);
      }
    } catch (error) {
      console.error('Error fetching report data:', error);
      setError('Failed to fetch report data. Please ensure the backend is running.');
      setReportData({});
    } finally {
      setLoading(false);
    }
  };

  const fetchDetailedTrades = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${userId}/detailed-trades?filter=${tradeFilter}`);
      if (response.ok) {
        const data = await response.json();
        setDetailedTrades(data.trades || []);
      } else {
        setDetailedTrades([]);
      }
    } catch (error) {
      console.error('Error fetching detailed trades:', error);
      setDetailedTrades([]);
    }
  };

  const fetchStrategyBreakdown = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${userId}/strategy-breakdown`);
      if (response.ok) {
        const data = await response.json();
        setStrategyBreakdown(data.strategies || []);
      } else {
        setStrategyBreakdown([]);
      }
    } catch (error) {
      console.error('Error fetching strategy breakdown:', error);
      setStrategyBreakdown([]);
    }
  };

  const exportReport = async (format) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${userId}/export-report?type=${reportType}&format=${format}`, {
        method: 'GET',
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${userId}_${reportType}_report.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        alert('Export functionality requires backend implementation');
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Export functionality requires backend implementation');
    }
  };

  const userAccount = connectedAccounts.find(acc => acc.user_id === userId);
  
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

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Trading Performance Report: {userId}</h1>
            <p className="text-gray-600">Real-time trading performance analysis and metrics</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="daily">Daily Report</option>
              <option value="weekly">Weekly Report</option>
              <option value="monthly">Monthly Report</option>
              <option value="quarterly">Quarterly Report</option>
            </select>
              
            <select
              value={tradeFilter}
              onChange={(e) => setTradeFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="today">Today's Trades</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
            </select>
            
            <div className="flex space-x-2">
              <button
                onClick={() => exportReport('pdf')}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
              >
                📄 Export PDF
              </button>
              <button
                onClick={() => exportReport('excel')}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
              >
                📊 Export Excel
              </button>
            </div>
            
            <Link
              to={`/user/${userId}`}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Generating report...</p>
          </div>
        )}

        {!loading && reportData.summary && (
          <>
            {/* Summary Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-2xl font-bold text-gray-900">{reportData.summary.total_trades}</div>
                <div className="text-sm text-gray-600">Total Trades</div>
                <div className="mt-2 text-xs">
                  <span className="text-green-600">Win: {reportData.summary.winning_trades}</span> | 
                  <span className="text-red-600 ml-1">Loss: {reportData.summary.losing_trades}</span>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className={`text-2xl font-bold ${reportData.summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ₹{reportData.summary.total_pnl.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Total P&L</div>
                <div className="mt-2 text-xs text-gray-500">
                  Profit Factor: {reportData.summary.profit_factor.toFixed(2)}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-2xl font-bold text-blue-600">{reportData.summary.win_rate.toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Win Rate</div>
                <div className="mt-2 text-xs text-gray-500">
                  Avg Profit: ₹{reportData.summary.avg_profit.toFixed(0)}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-2xl font-bold text-purple-600">{reportData.summary.sharpe_ratio.toFixed(2)}</div>
                <div className="text-sm text-gray-600">Sharpe Ratio</div>
                <div className="mt-2 text-xs text-gray-500">
                  Sortino: {reportData.summary.sortino_ratio.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Performance Chart Placeholder */}
            <div className="bg-white rounded-lg shadow mb-8 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Cumulative P&L Performance</h3>
              {performanceChart.length > 0 ? (
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-4xl mb-2">📈</div>
                    <p className="text-gray-600">Performance Chart</p>
                    <p className="text-sm text-gray-500">Current P&L: ₹{reportData.summary.total_pnl.toLocaleString()}</p>
                    <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
                      {performanceChart.slice(-4).map((point, index) => (
                        <div key={index} className="text-center">
                          <div className="font-medium">{new Date(point.date).toLocaleDateString()}</div>
                          <div className={`text-lg font-bold ${point.cumulative_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ₹{point.cumulative_pnl.toLocaleString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <div className="text-4xl mb-2">📊</div>
                    <p>No performance data available</p>
                    <p className="text-sm">Start trading to see performance charts</p>
                  </div>
                </div>
              )}
            </div>

            {/* Risk Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Analysis</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Max Drawdown:</span>
                    <span className="font-bold text-red-600">₹{reportData.summary.max_drawdown.toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Largest Profit:</span>
                    <span className="font-bold text-green-600">₹{reportData.summary.max_profit.toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Largest Loss:</span>
                    <span className="font-bold text-red-600">₹{reportData.summary.max_loss.toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Average Loss:</span>
                    <span className="font-bold text-orange-600">₹{reportData.summary.avg_loss.toLocaleString()}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Capital Allocation:</span>
                    <span className="font-bold text-blue-600">₹{userAccount.capital_allocation?.toLocaleString() || 'N/A'}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Ratios</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Profit Factor:</span>
                    <span className="font-bold text-green-600">{reportData.summary.profit_factor.toFixed(2)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Sharpe Ratio:</span>
                    <span className="font-bold text-blue-600">{reportData.summary.sharpe_ratio.toFixed(2)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Sortino Ratio:</span>
                    <span className="font-bold text-purple-600">{reportData.summary.sortino_ratio.toFixed(2)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Return on Capital:</span>
                    <span className="font-bold text-indigo-600">
                      {userAccount.capital_allocation ? 
                        ((reportData.summary.total_pnl / userAccount.capital_allocation) * 100).toFixed(2) : 0}%
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Risk Percentage:</span>
                    <span className="font-bold text-orange-600">{userAccount.risk_percentage || 'N/A'}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Strategy Breakdown */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Strategy Performance Breakdown</h3>
                <p className="text-gray-600">Individual strategy contribution to overall performance</p>
              </div>
              {strategyBreakdown.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strategy</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trades</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Win Rate</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg P&L/Trade</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {strategyBreakdown.map((strategy, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {strategy.strategy}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {strategy.trades}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`text-sm font-medium ${
                              strategy.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              ₹{strategy.pnl.toLocaleString()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {strategy.win_rate.toFixed(1)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ₹{strategy.trades > 0 ? (strategy.pnl / strategy.trades).toFixed(0) : '0'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-6 text-center text-gray-500">
                  <div className="text-4xl mb-2">📊</div>
                  <p>No strategy data available</p>
                  <p className="text-sm">Strategy breakdown will appear after trading activity</p>
                </div>
              )}
            </div>

            {/* Detailed Trades Analysis */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Detailed Trade History</h3>
                <p className="text-gray-600">Real-time trade execution details and performance</p>
              </div>
              {detailedTrades.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strategy</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {detailedTrades.slice(0, 50).map((trade, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                            {trade.symbol}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                            {trade.strategy}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              trade.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {trade.side}
                            </span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                            {trade.quantity}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                            ₹{trade.price?.toFixed(2)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className={`text-sm font-medium ${
                              trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              ₹{trade.pnl?.toLocaleString()}
                            </span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                            {new Date(trade.timestamp).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-6 text-center text-gray-500">
                  <div className="text-4xl mb-2">📋</div>
                  <p>No trades found</p>
                  <p className="text-sm">Trade history will appear after trading activity</p>
                </div>
              )}
              {detailedTrades.length > 0 && (
                <div className="p-4 bg-gray-50 text-center">
                  <p className="text-sm text-gray-600">
                    Showing latest {Math.min(detailedTrades.length, 50)} trades. Export full data using the export buttons above.
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {!loading && !reportData.summary && !error && (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📊</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No Trading Data Available</h2>
            <p className="text-gray-600 mb-4">Start trading to see comprehensive reports and analytics</p>
            <Link to="/trading" className="text-blue-600 hover:text-blue-800">
              Go to Trading Dashboard →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserReports;